import secrets
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from yatrago import db
from yatrago.models import (
    TransportBooking,
    TransportOption,
    TransportPassenger,
    TransportSeat,
)


class TransportBookingError(ValueError):
    """Invalid or unavailable demonstration transport booking."""


def create_transport_booking(
    user,
    option_id,
    passenger_details,
    trip_type="oneway",
    return_option_id=None,
    return_date=None,
    pickup_address="",
    dropoff_address="",
    rental_driver="",
    seat_ids=None,
):
    seat_ids = seat_ids or []
    try:
        option = db.session.get(TransportOption, option_id)
        if option is None or option.departure_at < datetime.now():
            raise TransportBookingError("That sample transport option is no longer available.")
        if not 1 <= len(passenger_details) <= 8:
            raise TransportBookingError("Choose between 1 and 8 passengers.")
        if trip_type not in {"oneway", "roundtrip", "rental"}:
            raise TransportBookingError("Choose a valid journey type.")
        if trip_type == "roundtrip" and option.mode != "cab":
            raise TransportBookingError("Round trips are only available for sample taxis.")
        if trip_type == "rental" and option.mode not in {"car", "bike"}:
            raise TransportBookingError("Rental periods are only available for cars and bikes.")
        if trip_type == "oneway" and return_option_id:
            raise TransportBookingError("A return service requires a round-trip booking.")
        return_option = db.session.get(TransportOption, return_option_id) if return_option_id else None
        if return_option_id and (
            return_option is None
            or return_option.mode != option.mode
            or return_option.origin != option.destination
            or return_option.destination != option.origin
            or (return_date is not None and return_option.departure_at.date() != return_date)
        ):
            raise TransportBookingError("Choose a valid return service for your route and date.")
        if trip_type == "roundtrip" and return_option is None:
            raise TransportBookingError("Choose a sample return service.")
        if trip_type == "roundtrip" and (
            return_date is None
            or return_date <= option.departure_at.date()
            or return_option.departure_at.date() != return_date
        ):
            raise TransportBookingError("Choose a return date after departure and a matching sample service.")
        if option.mode in {"cab", "auto"} and (
            not pickup_address.strip() or not dropoff_address.strip()
        ):
            raise TransportBookingError("Enter both pickup and drop-off details.")
        if option.mode in {"car", "bike"} and trip_type != "rental":
            raise TransportBookingError("Choose a valid rental period.")
        if option.mode in {"car", "bike"} and rental_driver not in {"Self-drive", "Chauffeur-driven"}:
            raise TransportBookingError("Choose self-drive or chauffeur-driven service.")
        if option.mode in {"car", "bike"} and option.service_type in {
            "Self-drive", "Chauffeur-driven"
        } and rental_driver != option.service_type:
            raise TransportBookingError("Choose the listed drive option for this sample vehicle.")
        if option.mode == "train":
            if len(seat_ids) != len(passenger_details) or len(seat_ids) != len(set(seat_ids)):
                raise TransportBookingError("Select one different sample train seat per passenger.")
        elif seat_ids:
            raise TransportBookingError("Seat selection is only available for sample trains.")

        cleaned = []
        for detail in passenger_details:
            name = detail.get("name", "").strip()
            try:
                age = int(detail.get("age", ""))
            except (TypeError, ValueError):
                raise TransportBookingError("Enter a valid age for every traveller.") from None
            if not name or len(name) > 100 or not 1 <= age <= 120:
                raise TransportBookingError("Check each traveller’s name and age.")
            cleaned.append((name, age))

        selected_seats = []
        if option.mode == "train":
            selected_seats = TransportSeat.query.filter(
                TransportSeat.id.in_(seat_ids),
                TransportSeat.option_id == option.id,
                TransportSeat.booking_id.is_(None),
            ).all()
            if len(selected_seats) != len(seat_ids):
                raise TransportBookingError("One or more selected train seats are no longer available.")

        start_day = option.departure_at.date()
        end_day = return_date
        if option.mode in {"car", "bike"}:
            if not return_date or return_date <= start_day:
                raise TransportBookingError("Choose a rental return date after pickup.")
            if (return_date - start_day).days > 30:
                raise TransportBookingError("Sample rentals are limited to 30 days.")
            trip_type = "rental"
        elif trip_type == "roundtrip":
            end_day = return_option.departure_at.date()

        if option.price_basis == "per_day":
            fare = option.fare * (end_day - start_day).days
        elif trip_type == "roundtrip":
            multiplier = len(cleaned) if option.price_basis == "per_person" else 1
            fare = (option.fare + return_option.fare) * multiplier
        else:
            units = len(cleaned) if option.price_basis == "per_person" else 1
            fare = option.fare * units
        if fare <= 0:
            raise TransportBookingError("The sample journey must have a positive fare.")

        booking = TransportBooking(
            reference=secrets.token_hex(5).upper(),
            user_id=user.id,
            option_id=option.id,
            return_option_id=return_option.id if return_option else None,
            travel_date=start_day,
            return_date=end_day,
            passengers=len(cleaned),
            customer_name=cleaned[0][0],
            pickup_address=pickup_address.strip() or None,
            dropoff_address=dropoff_address.strip() or None,
            trip_type=trip_type,
            rental_driver=rental_driver or None,
            total_fare=fare,
        )
        db.session.add(booking)
        db.session.flush()
        if selected_seats:
            updated = TransportSeat.query.filter(
                TransportSeat.id.in_([seat.id for seat in selected_seats]),
                TransportSeat.booking_id.is_(None),
            ).update({TransportSeat.booking_id: booking.id}, synchronize_session=False)
            if updated != len(selected_seats):
                raise TransportBookingError("Train-seat availability changed. Please select seats again.")
        db.session.add_all(
            TransportPassenger(booking_id=booking.id, name=name, age=age)
            for name, age in cleaned
        )
        db.session.commit()
        return booking
    except TransportBookingError:
        db.session.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        raise TransportBookingError("We couldn’t save that transport booking. Please try again.") from error


def cancel_transport_booking(booking, user):
    if booking.user_id != user.id:
        raise TransportBookingError("You can only cancel your own transport bookings.")
    if booking.status != "confirmed" or booking.travel_date <= date.today():
        raise TransportBookingError("This transport booking is no longer eligible for cancellation.")
    try:
        booking.status = "cancelled"
        TransportSeat.query.filter_by(booking_id=booking.id).update(
            {TransportSeat.booking_id: None}, synchronize_session=False
        )
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise TransportBookingError("We couldn’t cancel this transport booking.") from error
