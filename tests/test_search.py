from datetime import date, timedelta

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
    assert b"Southern Star Travels" in response.data
    assert b"Highway Express" not in response.data
    with app.app_context():
        trips = Trip.query.join(Trip.route).filter_by(source="Bengaluru", destination="Hyderabad").all()
        assert trips
        assert min(trip.fare for trip in trips) <= 800


def test_search_shows_friendly_empty_state_for_unknown_route(client):
    response = client.get(
        "/search",
        query_string={
            "source": "Bengaluru",
            "destination": "Kolkata",
            "date": (date.today() + timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 200
    assert b"No departures found" in response.data


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
