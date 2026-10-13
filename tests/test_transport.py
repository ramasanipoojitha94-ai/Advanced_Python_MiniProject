from datetime import date, datetime, timedelta

import pytest

from yatrago import db
from yatrago.models import TransportBooking, TransportOption, TransportSeat, User
from yatrago.transport_services import (
    TransportBookingError,
    cancel_transport_booking,
    create_transport_booking,
)


@pytest.fixture()
def transport_user(app):
    with app.app_context():
        user = User(name="Asha Rao", email="transport@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()
        yield user.id


def _login(client):
    client.post(
        "/auth/login",
        data={"email": "transport@example.com", "password": "secure-pass-123"},
    )


def test_homepage_and_transport_search_cover_modes_filters_and_sample_data(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b"Choose your transport" in home.data
    assert home.data.count(b'data-transport-mode="') == 4
    for mode in (b"bus", b"flight", b"train", b"cab"):
        assert b'data-transport-mode="' + mode + b'"' in home.data
    for mode in (b"car", b"bike", b"metro", b"ferry", b"auto", b"shared"):
        assert b'data-transport-mode="' + mode + b'"' not in home.data
    assert b"Explore Incredible India" in home.data
    assert b"Phoenix Marketcity Bengaluru" in home.data
    assert b"Popular Weekend Trips from Bengaluru" in home.data
    assert b"Famous Food to Try" in home.data
    assert b"Depart after" not in home.data
    assert b"Travellers" not in home.data
    assert b"Service / vehicle" not in home.data
    assert b"Journey type" not in home.data
    assert b'name="departure_time"' not in home.data
    assert b'name="service_type"' not in home.data
    assert b'name="trip_type"' in home.data
    travel_day = (date.today() + timedelta(days=1)).isoformat()
    response = client.get(
        "/transport",
        query_string={
            "mode": "train",
            "origin": "Bengaluru",
            "destination": "Mysuru",
            "date": travel_day,
            "sort": "duration",
            "max_stops": "0",
        },
    )
    assert response.status_code == 200
    assert b"Demo rail service" in response.data
    assert b"DEMO DATA ONLY" in response.data
    assert b"demo seats" in response.data


def test_all_transport_modes_remain_available_outside_the_home_search(client):
    response = client.get("/transport")
    assert response.status_code == 200
    assert b"Ferries &amp; boats" in response.data
    assert b"Car rentals" in response.data
    assert b"Depart after" in response.data
    assert b"Travellers" in response.data
    assert b"Journey type" in response.data


def test_bus_and_flight_tabs_reuse_existing_search_flows(client):
    travel_day = (date.today() + timedelta(days=2)).isoformat()
    bus = client.get(
        "/transport",
        query_string={
            "mode": "bus",
            "origin": "Bengaluru",
            "destination": "Hyderabad",
            "date": travel_day,
            "passengers": 2,
        },
    )
    assert bus.status_code == 302
    assert "/search?" in bus.location
    flight = client.get(
        "/transport",
        query_string={
            "mode": "flight",
            "origin": "Bengaluru",
            "destination": "Delhi",
            "date": travel_day,
        },
    )
    assert flight.status_code == 302
    assert "/flights?" in flight.location
    assert "depart_date=" in flight.location


def test_bus_search_displays_state_corporations_and_private_demo_services(client):
    travel_day = (date.today() + timedelta(days=30)).isoformat()
    response = client.get(
        "/search",
        query_string={
            "source": "Bengaluru",
            "destination": "Hyderabad",
            "date": travel_day,
            "passengers": 1,
        },
    )
    assert response.status_code == 200
    assert b"KSRTC (DEMO DATA)" in response.data
    assert b"TGSRTC (DEMO DATA)" in response.data
    assert b"Private bus operator A (DEMO DATA)" in response.data
    assert response.data.count(b"DEMO DATA") >= 8

    response = client.get(
        "/search",
        query_string={
            "source": "Vijayawada",
            "destination": "Bengaluru",
            "date": travel_day,
        },
    )
    assert response.status_code == 200
    assert b"APSRTC (DEMO DATA)" in response.data
    assert b"KSRTC (DEMO DATA)" in response.data


def test_train_search_generates_multiple_route_date_options_and_seats(client, app):
    travel_day = (date.today() + timedelta(days=35)).isoformat()
    response = client.get(
        "/transport",
        query_string={
            "mode": "train",
            "origin": "Agra",
            "destination": "Ahmedabad",
            "date": travel_day,
            "passengers": 2,
            "sort": "departure",
        },
    )
    assert response.status_code == 200
    assert response.data.count(b"DEMO DATA") >= 6
    assert b"Agra" in response.data and b"Ahmedabad" in response.data
    with app.app_context():
        options = TransportOption.query.filter_by(
            mode="train", origin="Agra", destination="Ahmedabad"
        ).filter(
            db.func.date(TransportOption.departure_at) == travel_day
        ).all()
        assert len(options) == 6
        assert all(option.provider == "Demo rail service (DEMO DATA)" for option in options)
        assert all(len(option.seats) == 32 for option in options)


def test_train_booking_confirmation_double_booking_and_seat_reuse(
    app, client, transport_user
):
    travel_day = date.today() + timedelta(days=2)
    with app.app_context():
        option = TransportOption.query.filter_by(
            mode="train", origin="Bengaluru", destination="Mysuru"
        ).filter(db.func.date(TransportOption.departure_at) == travel_day.isoformat()).one()
        user = db.session.get(User, transport_user)
        seats = TransportSeat.query.filter_by(option_id=option.id).order_by(
            TransportSeat.seat_number
        ).limit(2).all()
        option_id, seat_id = option.id, seats[0].id
        booking = create_transport_booking(
            user, option_id, [{"name": "Asha Rao", "age": 24}], seat_ids=[seat_id]
        )
        reference = booking.reference
        with pytest.raises(TransportBookingError, match="no longer available"):
            create_transport_booking(
                user, option_id, [{"name": "Someone Else", "age": 30}], seat_ids=[seat_id]
            )
        cancel_transport_booking(booking, user)
        replacement = create_transport_booking(
            user, option_id, [{"name": "Asha Rao", "age": 24}], seat_ids=[seat_id]
        )
        assert replacement.reference != reference

    _login(client)
    confirmation = client.get(f"/transport/booking/{replacement.reference}")
    assert confirmation.status_code == 200
    assert b"Thank You for Choosing YatraGo!" in confirmation.data
    assert b"Your journey starts here." in confirmation.data
    history = client.get("/trips")
    assert b"Deccan Rail" in history.data
    assert b"UPCOMING" in history.data


def test_transport_booking_validates_round_trips_and_rental_dates(app, transport_user):
    with app.app_context():
        user = db.session.get(User, transport_user)
        taxi = TransportOption.query.filter_by(
            mode="cab", origin="Bengaluru", destination="Mysuru"
        ).filter(
            db.func.date(TransportOption.departure_at)
            == (date.today() + timedelta(days=2)).isoformat()
        ).first()
        car = TransportOption.query.filter_by(
            mode="car", origin="Bengaluru", service_type="Self-drive"
        ).filter(
            db.func.date(TransportOption.departure_at)
            == (date.today() + timedelta(days=2)).isoformat()
        ).first()
        assert taxi is not None and car is not None
        with pytest.raises(TransportBookingError, match="sample return service"):
            create_transport_booking(
                user,
                taxi.id,
                [{"name": "Asha Rao", "age": 24}],
                trip_type="roundtrip",
            )
        with pytest.raises(TransportBookingError, match="rental return"):
            create_transport_booking(
                user,
                car.id,
                [{"name": "Asha Rao", "age": 24}],
                trip_type="rental",
                return_date=car.departure_at.date(),
                rental_driver="Self-drive",
            )


def test_transport_bookings_are_private_and_cancellable(client, app, transport_user):
    travel_day = date.today() + timedelta(days=3)
    with app.app_context():
        option = TransportOption.query.filter_by(
            mode="train", origin="Delhi", destination="Jaipur"
        ).filter(db.func.date(TransportOption.departure_at) == travel_day.isoformat()).first()
        user = db.session.get(User, transport_user)
        booking = create_transport_booking(
            user,
            option.id,
            [{"name": "Asha Rao", "age": 24}],
            seat_ids=[option.seats[0].id],
        )
        reference = booking.reference
    assert client.get(f"/transport/booking/{reference}").status_code == 302
    _login(client)
    assert client.get(f"/transport/booking/{reference}").status_code == 200
    response = client.post(f"/transport/booking/{reference}/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"has been cancelled" in response.data
    with app.app_context():
        saved = TransportBooking.query.filter_by(reference=reference).one()
        assert saved.status == "cancelled"
        assert all(seat.booking_id is None for seat in saved.seats)
