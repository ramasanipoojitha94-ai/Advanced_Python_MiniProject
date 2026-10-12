from datetime import date, timedelta

import pytest

from yatrago import db
from yatrago.models import (
    PackingItem,
    PlaceReview,
    PlanExpense,
    PlanStop,
    SavedWorldPlace,
    TravelPlan,
    User,
    WorldPlace,
)


@pytest.fixture()
def map_user(app):
    with app.app_context():
        user = User(name="Mira Shah", email="map-user@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()
        yield user.id


def _login(client):
    client.post(
        "/auth/login",
        data={"email": "map-user@example.com", "password": "secure-pass-123"},
    )


def test_world_map_and_place_api_search_filter_radius_and_source(client, app):
    response = client.get("/world-map")
    assert response.status_code == 200
    assert b"Explore World Map" in response.data
    assert b"OpenStreetMap contributors" in response.data
    response = client.get(
        "/api/world-places",
        query_string={"q": "Tokyo", "type": "hotel", "sort": "price"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["live_data"] is False
    assert data["source"] == "curated demonstration data"
    assert len(data["places"]) == 1
    assert data["places"][0]["city"] == "Tokyo"
    radius = client.get(
        "/api/world-places",
        query_string={
            "lat": "35.6938",
            "lon": "139.7034",
            "radius": "1",
            "sort": "distance",
        },
    )
    assert radius.status_code == 200
    assert radius.get_json()["places"][0]["distance_km"] == 0
    assert client.get("/api/world-places?type=unknown").status_code == 400
    assert client.get("/api/world-places?sort=distance").status_code == 400
    assert client.get("/api/world-places?radius=invalid").status_code == 400
    temple_places = client.get(
        "/api/world-places",
        query_string={"q": "Madurai", "category": "Temples & places of worship"},
    )
    assert temple_places.status_code == 200
    assert temple_places.get_json()["live_data"] is False
    assert temple_places.get_json()["places"][0]["city"] == "Madurai"


def test_saved_places_and_trip_planner_are_private_with_expenses_and_checklist(
    client, app, map_user
):
    with app.app_context():
        place = WorldPlace.query.filter_by(name="Central Park").one()
        place_id = place.id
    _login(client)
    saved = client.post(f"/world-map/places/{place_id}/save", follow_redirects=True)
    assert saved.status_code == 200
    assert b"Saved for later" in saved.data
    response = client.get("/api/world-places?saved=1")
    assert [item["id"] for item in response.get_json()["places"]] == [place_id]

    check_in = (date.today() + timedelta(days=5)).isoformat()
    create = client.post(
        "/planner",
        data={
            "title": "New York break",
            "start_date": check_in,
            "end_date": (date.today() + timedelta(days=7)).isoformat(),
            "budget_inr": "25000",
            "place_id": str(place_id),
            "notes": "Museum and park days",
        },
    )
    assert create.status_code == 302
    with app.app_context():
        plan = TravelPlan.query.filter_by(user_id=map_user).one()
        plan_id = plan.id
        assert PlanStop.query.filter_by(plan_id=plan_id, place_id=place_id).count() == 1
    client.post(
        f"/planner/{plan_id}/stops",
        data={"name": "Museum visit", "visit_date": check_in, "notes": "Bring the camera"},
    )
    client.post(
        f"/planner/{plan_id}/expenses",
        data={
            "category": "food",
            "description": "Lunch",
            "amount_inr": "900",
            "spent_on": check_in,
        },
    )
    client.post(f"/planner/{plan_id}/packing", data={"label": "Camera"})
    with app.app_context():
        assert PlanStop.query.filter_by(plan_id=plan_id).count() == 2
        assert PlanExpense.query.filter_by(plan_id=plan_id).one().amount_inr == 900
        packing = PackingItem.query.filter_by(plan_id=plan_id).one()
        packing_id = packing.id
    client.post(f"/planner/{plan_id}/packing/{packing_id}/toggle")
    detail = client.get(f"/planner/{plan_id}")
    assert detail.status_code == 200
    assert b"New York break" in detail.data
    assert b"24,100" in detail.data
    assert b"Camera" in detail.data
    client.post("/auth/logout")
    assert client.get(f"/planner/{plan_id}").status_code == 302
    client.post(
        "/auth/register",
        data={
            "name": "Other User",
            "email": "another-map-user@example.com",
            "password": "secure-pass-456",
            "confirm_password": "secure-pass-456",
        },
    )
    assert client.get(f"/planner/{plan_id}").status_code == 404


def test_map_place_reviews_are_validated_and_marked_unverified(client, app, map_user):
    with app.app_context():
        place_id = WorldPlace.query.filter_by(name="Central Park").one().id
    _login(client)
    response = client.post(
        f"/world-map/places/{place_id}/reviews",
        data={"rating": "5", "body": "A pleasant walk in the sample itinerary."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"not independently verified" in response.data
    response = client.get(f"/api/world-places/{place_id}/reviews")
    assert response.get_json()["reviews"][0]["verified"] is False
    filtered = client.get(
        "/api/world-places",
        query_string={"q": "Central Park", "min_rating": "5"},
    )
    assert [place["id"] for place in filtered.get_json()["places"]] == [place_id]
    with app.app_context():
        assert PlaceReview.query.filter_by(user_id=map_user, place_id=place_id).count() == 1
    duplicate = client.post(
        f"/world-map/places/{place_id}/reviews",
        data={"rating": "4", "body": "Another review."},
        follow_redirects=True,
    )
    assert b"already reviewed" in duplicate.data
