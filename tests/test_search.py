from datetime import date, timedelta
import re

from yatrago.models import Trip


def test_search_returns_matching_demo_buses_and_filters(client, app):
    travel_date = (date.today() + timedelta(days=1)).isoformat()
    response = client.get(
        "/search",
        query_string={
            "source": "Bengaluru",
            "destination": "Hyderabad",
            "date": travel_date,
            "max_price": 800,
            "sort": "price",
            "amenity": "Wi-Fi",
            "bus_type": "AC Sleeper",
        },
    )
    assert response.status_code == 200
    assert b"KSRTC (DEMO DATA)" in response.data
    assert b"Highway Express" not in response.data
    with app.app_context():
        trips = Trip.query.join(Trip.route).filter_by(source="Bengaluru", destination="Hyderabad").all()
        assert trips
        assert min(trip.fare for trip in trips) <= 800


def test_search_shows_friendly_empty_state_when_filters_exclude_demo_route(client):
    response = client.get(
        "/search",
        query_string={
            "source": "Bengaluru",
            "destination": "Kolkata",
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "max_price": 1,
        },
    )
    assert response.status_code == 200
    assert b"No demo departures match" in response.data


def test_bus_search_generates_idempotent_schedules_for_custom_routes_and_dates(client, app):
    travel_day = (date.today() + timedelta(days=90)).isoformat()
    query = {
        "source": "Silchar",
        "destination": "Gangtok",
        "date": travel_day,
        "passengers": 2,
        "sort": "price",
    }
    first = client.get("/search", query_string=query)
    second = client.get("/search", query_string=query)
    assert first.status_code == second.status_code == 200
    assert b"DEMO DATA" in first.data
    assert b"Private bus operator A (DEMO DATA)" in first.data
    assert b"No demo departures match" not in first.data
    shown_fares = [
        int(value)
        for value in re.findall(r'<strong class="fare">\u20b9(\d+)', first.get_data(as_text=True))
    ]
    assert shown_fares == sorted(shown_fares)
    with app.app_context():
        trips = Trip.query.join(Trip.route).filter_by(
            source="Silchar", destination="Gangtok"
        ).order_by(Trip.departure_at).all()
        trip = trips[0]
        assert trip.departure_at.date().isoformat() == travel_day
        assert trip.arrival_at > trip.departure_at
        assert len(trip.seats) == 24
        trip_count = Trip.query.join(Trip.route).filter_by(
            source="Silchar", destination="Gangtok"
        ).count()
    assert trip_count >= 8


def test_bus_search_filters_generated_schedule_and_rejects_same_city(client):
    travel_day = (date.today() + timedelta(days=120)).isoformat()
    response = client.get(
        "/search",
        query_string={
            "source": "Silchar",
            "destination": "Gangtok",
            "date": travel_day,
            "passengers": 2,
            "bus_type": "AC Sleeper",
            "amenity": "Wi-Fi",
            "departure": "morning",
            "availability": "available",
            "max_price": 1000,
            "sort": "price",
        },
    )
    assert response.status_code == 200
    assert b"Public roadways demo (DEMO DATA)" in response.data
    assert b"Seats for all travellers" in response.data

    same_city = client.get(
        "/search",
        query_string={
            "source": "New Delhi",
            "destination": "Delhi",
            "date": travel_day,
        },
    )
    assert b"Choose different source and destination cities" in same_city.data


def test_search_rejects_past_date(client):
    response = client.get(
        "/search",
        query_string={
            "source": "Bengaluru",
            "destination": "Hyderabad",
            "date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 200
    assert b"Journey date cannot be in the past" in response.data
