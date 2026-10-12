from datetime import datetime

import pytest
from flask_login import login_user

from yatrago import db
from yatrago.bookings import BookingError, cancel_booking, create_booking
from yatrago.migrations import migrate_reusable_bus_seats
from yatrago.models import Booking, Passenger, Seat, Trip, User


@pytest.fixture()
def booking_context(app):
    with app.app_context():
        user = User(name="Asha Rao", email="asha@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.flush()
        trip = (
            Trip.query.filter(Trip.departure_at > datetime.now())
            .join(Trip.route)
            .filter_by(source="Bengaluru", destination="Hyderabad")
            .order_by(Trip.departure_at)
            .first()
        )
        seats = Seat.query.filter_by(trip_id=trip.id).order_by(Seat.seat_number).limit(2).all()
        ids = [seat.id for seat in seats]
        db.session.commit()
        yield user.id, trip.id, ids


def test_booking_saves_passengers_and_blocks_double_booking(app, booking_context):
    user_id, trip_id, seat_ids = booking_context
    with app.app_context():
        user = db.session.get(User, user_id)
        booking = create_booking(
            user,
            trip_id,
            seat_ids,
            [
                {"name": "Asha Rao", "age": "24", "gender": "Female"},
                {"name": "Ravi Rao", "age": "27", "gender": "Male"},
            ],
        )
        assert booking.total_fare > 0
        assert len(booking.passengers) == 2
        with pytest.raises(BookingError, match="just been booked"):
            create_booking(
                user,
                trip_id,
                seat_ids,
                [
                    {"name": "Someone", "age": "30", "gender": "Other"},
                    {"name": "Someone Else", "age": "31", "gender": "Other"},
                ],
            )
        saved = db.session.get(Booking, booking.id)
        assert saved.status == "confirmed"
        assert all(db.session.get(Seat, seat_id).booking_id == saved.id for seat_id in seat_ids)


def test_cancellation_releases_seats(app, booking_context):
    user_id, trip_id, seat_ids = booking_context
    with app.app_context():
        user = db.session.get(User, user_id)
        booking = create_booking(
            user,
            trip_id,
            seat_ids[:1],
            [{"name": "Asha Rao", "age": "24", "gender": "Female"}],
        )
        cancel_booking(booking, user)
        assert db.session.get(Booking, booking.id).status == "cancelled"
        assert db.session.get(Seat, seat_ids[0]).booking_id is None
        replacement = create_booking(
            user,
            trip_id,
            seat_ids[:1],
            [{"name": "Asha Rao", "age": "24", "gender": "Female"}],
        )
        assert replacement.id != booking.id


def test_seat_page_and_confirmation_require_login(client, app, booking_context):
    _, trip_id, _seat_ids = booking_context
    assert client.get(f"/trips/{trip_id}/book").status_code == 302
    assert client.get(f"/trips/{trip_id}/book").status_code == 302


def test_booking_and_cancellation_http_flow(client, app, booking_context):
    user_id, trip_id, seat_ids = booking_context
    client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    assert client.get(f"/trips/{trip_id}/book").status_code == 200
    response = client.post(
        f"/trips/{trip_id}/book",
        data={
            "passenger_count": "1",
            "seat_ids": str(seat_ids[0]),
            "name_0": "Asha Rao",
            "age_0": "24",
            "gender_0": "Female",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Booking confirmed" in response.data
    with app.app_context():
        booking = Booking.query.filter_by(user_id=user_id).one()
        reference = booking.reference
        assert db.session.get(Seat, seat_ids[0]).booking_id == booking.id

    response = client.post(f"/booking/{reference}/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"has been cancelled" in response.data
    with app.app_context():
        booking = Booking.query.filter_by(reference=reference).one()
        assert booking.status == "cancelled"
        assert db.session.get(Seat, seat_ids[0]).booking_id is None


def test_legacy_passenger_seat_constraint_migrates_without_losing_history(app, booking_context):
    user_id, trip_id, seat_ids = booking_context
    with app.app_context():
        user = db.session.get(User, user_id)
        original = create_booking(
            user,
            trip_id,
            seat_ids[:1],
            [{"name": "Asha Rao", "age": "24", "gender": "Female"}],
        )
        passenger = Passenger.query.filter_by(booking_id=original.id).one()
        original_id = original.id
        connection = db.engine.raw_connection()
        try:
            connection.cursor().execute(
                "CREATE UNIQUE INDEX uq_legacy_passenger_seat ON passenger (seat_id)"
            )
            connection.commit()
        finally:
            connection.close()

        migrate_reusable_bus_seats()
        db.session.expire_all()
        assert Passenger.query.filter_by(booking_id=original_id).one().name == "Asha Rao"
        cancel_booking(db.session.get(Booking, original_id), user)
        replacement = create_booking(
            user,
            trip_id,
            seat_ids[:1],
            [{"name": "Asha Rao", "age": "24", "gender": "Female"}],
        )
        assert replacement.id != original_id
