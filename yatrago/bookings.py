import secrets
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from yatrago import db
from yatrago.models import Booking, Destination, Passenger, Seat, StayProperty, Trip

bookings = Blueprint("bookings", __name__)


class BookingError(ValueError):
    """An invalid or no-longer-available booking request."""


def create_booking(user, trip_id, seat_ids, passenger_details):
    """Atomically reserve available seats and save the named passengers."""
    try:
        trip = db.session.get(Trip, trip_id)
        if trip is None or trip.departure_at <= datetime.now():
            raise BookingError("This departure is no longer available.")
        if not seat_ids or len(seat_ids) != len(set(seat_ids)):
            raise BookingError("Select one or more different seats.")
        if len(passenger_details) != len(seat_ids):
            raise BookingError("Enter passenger details for every selected seat.")
        seats = (
            Seat.query.filter(
                Seat.trip_id == trip_id,
                Seat.id.in_(seat_ids),
                Seat.booking_id.is_(None),
            )
            .order_by(Seat.seat_number)
            .all()
        )
        if len(seats) != len(seat_ids):
            raise BookingError("One or more selected seats have just been booked. Please choose again.")
        for detail in passenger_details:
            name = detail.get("name", "").strip()
            try:
                age = int(detail.get("age", ""))
            except (TypeError, ValueError):
                raise BookingError("Enter a valid age for every passenger.") from None
            gender = detail.get("gender", "")
            if not name or len(name) > 100 or not 1 <= age <= 120 or gender not in {
                "Female", "Male", "Other", "Prefer not to say"
            }:
                raise BookingError("Check each passenger’s name, age, and gender.")

        booking = Booking(
            reference=secrets.token_hex(5).upper(),
            user_id=user.id,
            trip_id=trip.id,
            total_fare=trip.fare * len(seats),
            status="confirmed",
        )
        db.session.add(booking)
        db.session.flush()

        updated = Seat.query.filter(
            Seat.id.in_([seat.id for seat in seats]),
            Seat.trip_id == trip.id,
            Seat.booking_id.is_(None),
        ).update({Seat.booking_id: booking.id}, synchronize_session=False)
        if updated != len(seats):
            raise BookingError("Seat availability changed. Please search and select seats again.")

        for seat_id, detail in zip(seat_ids, passenger_details):
            db.session.add(
                Passenger(
                    booking_id=booking.id,
                    seat_id=seat_id,
                    name=detail["name"].strip(),
                    age=int(detail["age"]),
                    gender=detail["gender"],
                )
            )
        db.session.commit()
        return booking
    except BookingError:
        db.session.rollback()
        raise
    except (IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        raise BookingError("We couldn’t save that booking. Please try again.") from error


def cancel_booking(booking, user):
    """Cancel an eligible booking and release its seats in the same transaction."""
    if booking.user_id != user.id:
        raise BookingError("You can only cancel your own bookings.")
    if booking.status != "confirmed" or booking.trip.departure_at <= datetime.now():
        raise BookingError("This booking is no longer eligible for cancellation.")
    try:
        booking.status = "cancelled"
        Seat.query.filter_by(booking_id=booking.id).update(
            {Seat.booking_id: None}, synchronize_session=False
        )
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise BookingError("We couldn’t cancel that booking. Please try again.") from error


@bookings.get("/trips/<int:trip_id>/book")
@login_required
def select_seats(trip_id):
    trip = db.session.get(Trip, trip_id)
    if trip is None:
        abort(404)
    passenger_count = request.args.get("passengers", default=1, type=int)
    if not 1 <= passenger_count <= 6:
        passenger_count = 1
    if trip.departure_at <= datetime.now():
        flash("This departure has already left.", "error")
        return redirect(url_for("main.search"))
    return render_template(
        "booking/seats.html", trip=trip, seats=trip.seats, passenger_count=passenger_count
    )


@bookings.post("/trips/<int:trip_id>/book")
@login_required
def book_trip(trip_id):
    try:
        raw_seats = request.form.getlist("seat_ids")
        seat_ids = [int(value) for value in raw_seats]
        passenger_count = request.form.get("passenger_count", default=1, type=int)
        if not 1 <= passenger_count <= 6:
            raise BookingError("Bookings are limited to 1–6 passengers.")
        if len(seat_ids) != passenger_count:
            raise BookingError(f"Select exactly {passenger_count} seat(s) for your travellers.")
        passenger_details = [
            {
                "name": request.form.get(f"name_{index}", ""),
                "age": request.form.get(f"age_{index}", ""),
                "gender": request.form.get(f"gender_{index}", ""),
            }
            for index in range(len(seat_ids))
        ]
        booking = create_booking(current_user, trip_id, seat_ids, passenger_details)
    except (ValueError, TypeError) as error:
        flash(str(error) or "Select valid seats and enter passenger details.", "error")
        return redirect(url_for("bookings.select_seats", trip_id=trip_id))
    flash("Your seats are confirmed. Have a wonderful journey!", "success")
    return redirect(url_for("bookings.confirmation", reference=booking.reference))


@bookings.get("/booking/<reference>")
@login_required
def confirmation(reference):
    booking = Booking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    destination = Destination.query.filter_by(name=booking.trip.route.destination).first()
    nearby_stays = StayProperty.query.filter_by(destination_id=destination.id).limit(3).all() if destination else []
    return render_template(
        "booking/confirmation.html", booking=booking, nearby_stays=nearby_stays
    )


@bookings.post("/booking/<reference>/cancel")
@login_required
def cancel(reference):
    booking = Booking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    try:
        cancel_booking(booking, current_user)
        flash("Your booking has been cancelled and the seats released.", "success")
    except BookingError as error:
        flash(str(error), "error")
    return redirect(url_for("main.trips"))
