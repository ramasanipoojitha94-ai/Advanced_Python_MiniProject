from datetime import date, datetime, timedelta

import pytest

from yatrago import db
from yatrago.models import (
    Destination,
    Flight,
    FlightBooking,
    FlightSeat,
    SavedDestination,
    SavedWorldPlace,
    StayBooking,
    StayProperty,
    User,
    WorldPlace,
)
from yatrago.travel_services import (
    TravelBookingError,
    book_flight,
    book_stay,
    cancel_flight_booking,
)


@pytest.fixture()
def traveller(app):
    with app.app_context():
        user = User(name="Asha Rao", email="asha@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()
        yield user.id


def test_destination_search_filters_database_regions_and_categories(client, app):
    response = client.get("/destinations?region=South&category=Hill%20station&q=Munnar")
    assert response.status_code == 200
    assert b"Munnar" in response.data
    assert b"Shillong" not in response.data
    with app.app_context():
        assert Destination.query.count() >= 40
        destination_id = Destination.query.filter_by(name="Munnar").one().id
    client.post(
        "/auth/register",
        data={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "password": "secure-pass-123",
            "confirm_password": "secure-pass-123",
        },
    )
    detail = client.get(f"/destinations/{destination_id}")
    assert b"Save this place" in detail.data
    client.post(f"/destinations/{destination_id}/save")
    assert b"Saved for later" in client.get("/destinations").data


def test_sample_flight_search_and_filters(client):
    travel_day = (date.today() + timedelta(days=2)).isoformat()
    response = client.get(
        "/flights",
        query_string={
            "origin": "Bengaluru",
            "destination": "Delhi",
            "depart_date": travel_day,
            "trip_type": "oneway",
            "cabin_class": "Economy",
            "passengers": 2,
            "max_stops": 1,
            "sort": "price",
        },
    )
    assert response.status_code == 200
    assert b"SAMPLE FLIGHT OPTIONS" in response.data
    assert b"Bengaluru" in response.data and b"Delhi" in response.data
    assert b"DEMO DATA ONLY" in response.data


def test_sample_stay_search_filters_property_records(client):
    response = client.get(
        "/hotels",
        query_string={"city": "Kochi", "type": "Hostel", "max_price": 1000, "sort": "price"},
    )
    assert response.status_code == 200
    assert b"Harbour Lane Hostel" in response.data
    assert b"Tea Valley Retreat" not in response.data


def test_invalid_flight_and_stay_booking_input_is_rejected(app, traveller):
    with app.app_context():
        user = db.session.get(User, traveller)
        flight = Flight.query.filter_by(origin_city="Bengaluru", destination_city="Delhi").first()
        with pytest.raises(TravelBookingError, match="valid cabin"):
            book_flight(user, flight.id, None, None, "Premium", [
                {"name": "Asha Rao", "age": "28", "gender": "Female"}
            ])
        stay = StayProperty.query.filter_by(name="Garden City Guesthouse").one()
        with pytest.raises(TravelBookingError, match="future"):
            book_stay(
                user,
                stay.id,
                date.today() - timedelta(days=1),
                date.today() + timedelta(days=1),
                ["Asha Rao"],
                "Standard room",
            )


def test_flight_booking_round_trip_confirmation_and_cancellation(app, client, traveller):
    outbound_day = date.today() + timedelta(days=2)
    return_day = outbound_day + timedelta(days=3)
    client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    response = client.get(
        "/flights",
        query_string={
            "origin": "Bengaluru",
            "destination": "Delhi",
            "depart_date": outbound_day.isoformat(),
            "return_date": return_day.isoformat(),
            "trip_type": "roundtrip",
            "cabin_class": "Economy",
            "passengers": 1,
        },
    )
    assert response.status_code == 200
    with app.app_context():
        outbound = Flight.query.filter_by(
            origin_city="Bengaluru", destination_city="Delhi"
        ).filter(db.func.date(Flight.departure_at) == outbound_day.isoformat()).first()
        returning = Flight.query.filter_by(
            origin_city="Delhi", destination_city="Bengaluru"
        ).filter(db.func.date(Flight.departure_at) == return_day.isoformat()).first()
        assert outbound is not None and returning is not None
        outbound_id, return_id = outbound.id, returning.id
        seat_id = FlightSeat.query.filter_by(flight_id=outbound.id).first().id
    response = client.post(
        f"/flights/{outbound_id}/book",
        data={
            "passenger_count": "1",
            "cabin_class": "Economy",
            "trip_type": "roundtrip",
            "return_date": return_day.isoformat(),
            "return_flight_id": str(return_id),
            "name_0": "Asha Rao",
            "age_0": "28",
            "gender_0": "Female",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Thank you for choosing YatraGo!" in response.data
    assert b"Your journey starts here." in response.data
    with app.app_context():
        booking = FlightBooking.query.filter_by(user_id=traveller).one()
        reference = booking.reference
        assert booking.return_flight_id == return_id
        assert booking.total_fare > 0
        assert db.session.get(FlightSeat, seat_id).booking_id == booking.id
    history = client.get("/trips")
    assert b"ROUND TRIP" in history.data
    cancel_response = client.post(f"/flights/booking/{reference}/cancel", follow_redirects=True)
    assert cancel_response.status_code == 200
    with app.app_context():
        assert db.session.get(FlightBooking, booking.id).status == "cancelled"
        assert db.session.get(FlightSeat, seat_id).booking_id is None


def test_stay_reservation_confirmation_and_unified_trips(client, app, traveller):
    client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    with app.app_context():
        property_id = StayProperty.query.filter_by(name="Garden City Guesthouse").one().id
    check_in = date.today() + timedelta(days=4)
    check_out = check_in + timedelta(days=2)
    response = client.post(
        f"/stays/{property_id}/book",
        data={
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guest_count": "2",
            "guest_0": "Asha Rao",
            "guest_1": "Dev Rao",
            "room_type": "Family room",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Thank you for choosing YatraGo!" in response.data
    assert b"Family room" in response.data
    with app.app_context():
        booking = StayBooking.query.filter_by(user_id=traveller).one()
        assert booking.guests == 2
        assert booking.total_fare == booking.property.price_per_night * 2
    trips = client.get("/trips")
    assert b"Garden City Guesthouse" in trips.data
    assert b"UPCOMING" in trips.data
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Book Your Journey" in dashboard.data


def test_travel_bookings_are_private_to_the_account(client, app, traveller):
    client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    with app.app_context():
        property_id = StayProperty.query.first().id
    check_in = date.today() + timedelta(days=7)
    response = client.post(
        f"/stays/{property_id}/book",
        data={
            "check_in": check_in.isoformat(),
            "check_out": (check_in + timedelta(days=1)).isoformat(),
            "guest_count": "1",
            "guest_0": "Asha Rao",
            "room_type": "Standard room",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        reference = StayBooking.query.filter_by(user_id=traveller).one().reference
    client.post("/auth/logout")
    assert client.get(f"/stays/booking/{reference}").status_code == 302


def test_dashboard_has_three_sections_and_keeps_other_tools_off_dashboard(client, app, traveller):
    with app.app_context():
        destination = Destination.query.filter_by(name="Munnar").one()
        map_place = WorldPlace.query.filter_by(name="Central Park").one()
        db.session.add_all([
            SavedDestination(user_id=traveller, destination_id=destination.id),
            SavedWorldPlace(user_id=traveller, place_id=map_place.id),
        ])
        db.session.commit()

    client.post(
        "/auth/login",
        data={"email": "asha@example.com", "password": "secure-pass-123"},
    )
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Your next adventure" in dashboard.data
    assert b"starts here." in dashboard.data
    assert b"Book Your Journey" in dashboard.data
    assert b"Explore India" in dashboard.data
    assert b"Plan Your Trip" in dashboard.data
    assert b"Travellers" in dashboard.data
    assert b"Buses" in dashboard.data
    assert b"Flights" in dashboard.data
    assert b"Trains" in dashboard.data
    assert b"Cabs" in dashboard.data
    assert dashboard.data.count(b'class="dashboard-featured-card"') == 8
    assert b"Popular routes" not in dashboard.data
    assert b"Central Park" not in dashboard.data
    assert b"Build a trip budget" not in dashboard.data
    with app.app_context():
        assert SavedDestination.query.filter_by(user_id=traveller).count() == 1
        assert SavedWorldPlace.query.filter_by(user_id=traveller).count() == 1
