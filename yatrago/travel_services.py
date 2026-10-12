import secrets
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from yatrago import db
from yatrago.models import (
    Flight,
    FlightBooking,
    FlightPassenger,
    FlightSeat,
    StayBooking,
    StayGuest,
    StayProperty,
)


class TravelBookingError(ValueError):
    """A booking request contains invalid or unavailable sample inventory."""


def book_flight(user, outbound_id, return_id, return_date, cabin_class, passenger_details):
    try:
        outbound = db.session.get(Flight, outbound_id)
        if outbound is None or outbound.departure_at <= datetime.now():
            raise TravelBookingError("That sample flight is no longer available.")
        if cabin_class not in {"Economy", "Business"}:
            raise TravelBookingError("Choose a valid cabin class.")
        if not 1 <= len(passenger_details) <= 6:
            raise TravelBookingError("Flight bookings are limited to 1–6 passengers.")
        returning = db.session.get(Flight, return_id) if return_id else None
        if return_id and (
            returning is None
            or returning.departure_at <= outbound.arrival_at
            or returning.origin_code != outbound.destination_code
            or returning.destination_code != outbound.origin_code
            or (return_date is not None and returning.departure_at.date() != return_date)
        ):
            raise TravelBookingError("Choose a valid return flight for this route.")
        cleaned = []
        for passenger in passenger_details:
            name = passenger.get("name", "").strip()
            try:
                age = int(passenger.get("age", ""))
            except (TypeError, ValueError):
                raise TravelBookingError("Enter a valid age for each traveller.") from None
            gender = passenger.get("gender", "")
            if not name or len(name) > 100 or not 1 <= age <= 120 or gender not in {
                "Female", "Male", "Other", "Prefer not to say"
            }:
                raise TravelBookingError("Check each traveller’s name, age, and gender.")
            cleaned.append((name, age, gender))

        outbound_seats = (
            FlightSeat.query.filter_by(flight_id=outbound.id, booking_id=None)
            .order_by(FlightSeat.seat_number).limit(len(cleaned)).all()
        )
        return_seats = (
            FlightSeat.query.filter_by(flight_id=returning.id, booking_id=None)
            .order_by(FlightSeat.seat_number).limit(len(cleaned)).all()
            if returning else []
        )
        if len(outbound_seats) != len(cleaned) or (returning and len(return_seats) != len(cleaned)):
            raise TravelBookingError("There are not enough sample seats on this flight.")

        unit_fare = outbound.fare_economy if cabin_class == "Economy" else outbound.fare_business
        if returning:
            unit_fare += returning.fare_economy if cabin_class == "Economy" else returning.fare_business
        booking = FlightBooking(
            reference=secrets.token_hex(5).upper(),
            user_id=user.id,
            outbound_flight_id=outbound.id,
            return_flight_id=returning.id if returning else None,
            cabin_class=cabin_class,
            total_fare=unit_fare * len(cleaned),
        )
        db.session.add(booking)
        db.session.flush()
        for seats in (outbound_seats, return_seats):
            if not seats:
                continue
            updated = FlightSeat.query.filter(
                FlightSeat.id.in_([seat.id for seat in seats]),
                FlightSeat.booking_id.is_(None),
            ).update({FlightSeat.booking_id: booking.id}, synchronize_session=False)
            if updated != len(seats):
                raise TravelBookingError("Flight availability changed. Please search again.")
        for index, (name, age, gender) in enumerate(cleaned):
            db.session.add(
                FlightPassenger(
                    booking_id=booking.id,
                    name=name,
                    age=age,
                    gender=gender,
                    outbound_seat_id=outbound_seats[index].id,
                    return_seat_id=return_seats[index].id if return_seats else None,
                )
            )
        db.session.commit()
        return booking
    except TravelBookingError:
        db.session.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        raise TravelBookingError("We couldn’t save that flight booking. Please try again.") from error


def cancel_flight_booking(booking, user):
    if booking.user_id != user.id:
        raise TravelBookingError("You can only cancel your own bookings.")
    if booking.status != "confirmed" or booking.outbound_flight.departure_at <= datetime.now():
        raise TravelBookingError("This flight booking is no longer eligible for cancellation.")
    try:
        booking.status = "cancelled"
        FlightSeat.query.filter_by(booking_id=booking.id).update(
            {FlightSeat.booking_id: None}, synchronize_session=False
        )
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise TravelBookingError("We couldn’t cancel that flight booking.") from error


def book_stay(user, property_id, check_in, check_out, guest_names, room_type):
    try:
        property_item = db.session.get(StayProperty, property_id)
        if property_item is None:
            raise TravelBookingError("Choose a listed sample stay.")
        today = date.today()
        if check_in < today or check_out <= check_in:
            raise TravelBookingError("Choose valid future check-in and check-out dates.")
        if (check_out - check_in).days > 30:
            raise TravelBookingError("Sample stays can be booked for up to 30 nights.")
        if not 1 <= len(guest_names) <= 8:
            raise TravelBookingError("Stay reservations are limited to 1–8 guests.")
        names = [name.strip() for name in guest_names]
        if any(not name or len(name) > 100 for name in names):
            raise TravelBookingError("Enter a name for each guest.")
        if room_type not in {"Standard room", "Family room"}:
            raise TravelBookingError("Choose a listed sample room type.")
        booking = StayBooking(
            reference=secrets.token_hex(5).upper(),
            user_id=user.id,
            property_id=property_item.id,
            check_in=check_in,
            check_out=check_out,
            guests=len(names),
            room_type=room_type,
            total_fare=property_item.price_per_night * (check_out - check_in).days,
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add_all(StayGuest(booking_id=booking.id, name=name) for name in names)
        db.session.commit()
        return booking
    except TravelBookingError:
        db.session.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        raise TravelBookingError("We couldn’t save that stay reservation. Please try again.") from error


def cancel_stay_booking(booking, user):
    if booking.user_id != user.id:
        raise TravelBookingError("You can only cancel your own stay reservations.")
    if booking.status != "confirmed" or booking.check_in <= date.today():
        raise TravelBookingError("This stay is no longer eligible for cancellation.")
    try:
        booking.status = "cancelled"
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise TravelBookingError("We couldn’t cancel that stay reservation.") from error
