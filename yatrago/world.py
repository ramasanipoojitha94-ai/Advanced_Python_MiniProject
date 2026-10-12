import math
from datetime import date, datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from yatrago import db
from yatrago.models import (
    PackingItem,
    PlaceReview,
    PlanExpense,
    PlanStop,
    SavedWorldPlace,
    TravelPlan,
    WorldPlace,
)

world = Blueprint("world", __name__)
PLACE_TYPES = {"hotel", "restaurant", "attraction", "transport", "destination"}
EXPENSE_CATEGORIES = {"transport", "stay", "food", "activity", "other"}


def _distance_km(latitude, longitude, place):
    lat1, lat2 = math.radians(latitude), math.radians(place.latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(place.longitude - longitude)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1, haversine)))


def _parse_coordinates(args):
    latitude_text, longitude_text = args.get("lat", ""), args.get("lon", "")
    if not latitude_text and not longitude_text:
        return None, None
    try:
        latitude, longitude = float(latitude_text), float(longitude_text)
    except (TypeError, ValueError):
        raise ValueError("Choose valid map coordinates.") from None
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Map coordinates are outside the supported range.")
    return latitude, longitude


def _optional_number(args, key, converter):
    raw_value = args.get(key, "").strip()
    if not raw_value:
        return None
    try:
        return converter(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f"Enter a valid {key.replace('_', ' ')} filter.") from None


def _review_stats():
    return {
        place_id: (float(average), count)
        for place_id, average, count in db.session.query(
            PlaceReview.place_id,
            func.avg(PlaceReview.rating),
            func.count(PlaceReview.id),
        ).group_by(PlaceReview.place_id).all()
    }


def _places_from_args(args, user_id=None):
    query = WorldPlace.query
    place_type = args.get("type", "").strip().lower()
    if place_type and place_type != "all":
        if place_type not in PLACE_TYPES:
            raise ValueError("Choose a supported place category.")
        query = query.filter(WorldPlace.place_type == place_type)
    category = args.get("category", "").strip()
    if category:
        query = query.filter(WorldPlace.category.ilike(category[:50]))
    term = args.get("q", "").strip()
    if term:
        pattern = f"%{term[:100]}%"
        query = query.filter(or_(
            WorldPlace.name.ilike(pattern),
            WorldPlace.city.ilike(pattern),
            WorldPlace.country.ilike(pattern),
            WorldPlace.address.ilike(pattern),
            WorldPlace.category.ilike(pattern),
            WorldPlace.cuisine.ilike(pattern),
        ))
    cuisine = args.get("cuisine", "").strip()
    if cuisine:
        query = query.filter(WorldPlace.cuisine.ilike(f"%{cuisine[:80]}%"))
    amenity = args.get("amenity", "").strip()
    if amenity:
        query = query.filter(WorldPlace.amenities.ilike(f"%{amenity[:80]}%"))
    dietary = args.get("dietary", "").strip()
    if dietary:
        query = query.filter(WorldPlace.dietary.ilike(f"%{dietary[:40]}%"))
    max_price = _optional_number(args, "max_price", int)
    if max_price is not None:
        if not 0 <= max_price <= 1_000_000:
            raise ValueError("Set a sample price limit between ₹0 and ₹10,00,000.")
        query = query.filter(WorldPlace.price_inr.is_not(None), WorldPlace.price_inr <= max_price)
    min_rating = _optional_number(args, "min_rating", float)
    if min_rating is not None:
        if not 1 <= min_rating <= 5:
            raise ValueError("Rating filter must be between 1 and 5.")
    saved_only = args.get("saved", "").lower() in {"1", "true", "yes"}
    saved_ids = set()
    if saved_only:
        if user_id is None:
            raise PermissionError("Sign in to view your saved map places.")
        saved_ids = {
            row[0] for row in db.session.query(SavedWorldPlace.place_id)
            .filter_by(user_id=user_id).all()
        }
        query = query.filter(WorldPlace.id.in_(saved_ids))

    latitude, longitude = _parse_coordinates(args)
    radius = _optional_number(args, "radius", float)
    if radius is not None and (not 0 < radius <= 5000 or latitude is None):
        raise ValueError("A radius requires a map location and must be between 1 and 5,000 km.")
    places = query.order_by(WorldPlace.country, WorldPlace.city, WorldPlace.name).all()
    rating_stats = _review_stats()
    rows = []
    for place in places:
        distance = _distance_km(latitude, longitude, place) if latitude is not None else None
        if radius is not None and distance > radius:
            continue
        average, review_count = rating_stats.get(place.id, (None, 0))
        rating = place.sample_rating if place.sample_rating is not None else average
        if min_rating is not None and (rating is None or rating < min_rating):
            continue
        rows.append((place, distance, rating, review_count))
    sort = args.get("sort", "relevance")
    if sort not in {"relevance", "price", "rating", "distance"}:
        raise ValueError("Choose a supported sort order.")
    if sort == "distance" and latitude is None:
        raise ValueError("Choose a location before sorting by distance.")
    if sort == "price":
        rows.sort(key=lambda row: (row[0].price_inr is None, row[0].price_inr or 0))
    elif sort == "rating":
        rows.sort(key=lambda row: (row[2] is None, -(row[2] or 0)))
    elif sort == "distance" and latitude is not None:
        rows.sort(key=lambda row: row[1])
    return rows


def _serialize_place(place, distance=None, saved=False, rating=None, review_count=0):
    return {
        "id": place.id,
        "name": place.name,
        "type": place.place_type,
        "category": place.category,
        "city": place.city,
        "country": place.country,
        "address": place.address,
        "lat": place.latitude,
        "lon": place.longitude,
        "description": place.description,
        "image": place.image,
        "rating": rating if rating is not None else place.sample_rating,
        "rating_count": review_count,
        "rating_kind": "unverified traveller reviews" if review_count else "sample",
        "price_inr": place.price_inr,
        "local_price": place.local_price,
        "local_currency": place.local_currency,
        "amenities": place.amenities,
        "cuisine": place.cuisine,
        "dietary": place.dietary,
        "opening_hours": place.opening_hours,
        "distance_km": round(distance, 1) if distance is not None else None,
        "saved": saved,
    }


@world.get("/world-map")
def explore_map():
    saved_only = request.args.get("saved", "").lower() in {"1", "true", "yes"}
    try:
        rows = _places_from_args(request.args, current_user.id if current_user.is_authenticated else None)
    except PermissionError:
        flash("Sign in to view your saved map places.", "info")
        return redirect(url_for("auth.login", next=request.full_path))
    except ValueError as error:
        rows = []
        flash(str(error), "error")
    saved_ids = set()
    if current_user.is_authenticated:
        saved_ids = {
            row[0] for row in db.session.query(SavedWorldPlace.place_id)
            .filter_by(user_id=current_user.id).all()
        }
    places = [
        _serialize_place(place, distance, place.id in saved_ids, rating, review_count)
        for place, distance, rating, review_count in rows
    ]
    plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(
        TravelPlan.created_at.desc()
    ).all() if current_user.is_authenticated else []
    return render_template(
        "world/map.html",
        places=places,
        plans=plans,
        query=request.args.get("q", ""),
        selected_type=request.args.get("type", "all"),
        selected_category=request.args.get("category", ""),
        categories=[
            row[0] for row in db.session.query(WorldPlace.category)
            .filter(WorldPlace.category != "")
            .distinct().order_by(WorldPlace.category).all()
        ],
        saved_only=saved_only,
        recent_searches=session.get("world_recent_searches", []),
    )


@world.get("/api/world-places")
def places_api():
    term = request.args.get("q", "").strip()
    if term:
        recent = session.get("world_recent_searches", [])
        session["world_recent_searches"] = [term[:100]] + [
            item for item in recent if item.casefold() != term.casefold()
        ][:4]
    try:
        rows = _places_from_args(
            request.args, current_user.id if current_user.is_authenticated else None
        )
    except PermissionError as error:
        return jsonify({"error": str(error)}), 401
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    saved_ids = set()
    if current_user.is_authenticated:
        saved_ids = {
            row[0] for row in db.session.query(SavedWorldPlace.place_id)
            .filter_by(user_id=current_user.id).all()
        }
    return jsonify({
        "places": [
            _serialize_place(place, distance, place.id in saved_ids, rating, review_count)
            for place, distance, rating, review_count in rows
        ],
        "source": "curated demonstration data",
        "live_data": False,
    })


@world.get("/api/world-places/<int:place_id>/reviews")
def place_reviews_api(place_id):
    place = db.session.get(WorldPlace, place_id)
    if not place:
        abort(404)
    reviews = PlaceReview.query.filter_by(place_id=place.id).order_by(
        PlaceReview.created_at.desc()
    ).limit(20).all()
    return jsonify({
        "reviews": [
            {
                "rating": review.rating,
                "body": review.body,
                "created_at": review.created_at.date().isoformat(),
                "verified": False,
            }
            for review in reviews
        ],
        "source": "traveller-submitted; not independently verified",
    })


@world.post("/world-map/places/<int:place_id>/save")
@login_required
def toggle_saved_place(place_id):
    place = db.session.get(WorldPlace, place_id)
    if not place:
        abort(404)
    saved = SavedWorldPlace.query.filter_by(
        user_id=current_user.id, place_id=place.id
    ).first()
    if saved:
        db.session.delete(saved)
        message, category = f"{place.name} removed from saved places.", "info"
    else:
        db.session.add(SavedWorldPlace(user_id=current_user.id, place_id=place.id))
        message, category = f"Saved for later: {place.name}.", "success"
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not update your saved places. Please try again.", "error")
        return redirect(url_for("world.explore_map", q=place.name))
    flash(message, category)
    return redirect(url_for("world.explore_map", q=place.name))


@world.get("/planner")
@login_required
def planner():
    plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(
        TravelPlan.created_at.desc()
    ).all()
    place_id = request.args.get("place_id", type=int)
    place = db.session.get(WorldPlace, place_id) if place_id else None
    return render_template("world/planner.html", plans=plans, place=place)


@world.post("/planner")
@login_required
def create_plan():
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    if not title or len(title) > 120 or len(notes) > 1000:
        flash("Enter a trip title (up to 120 characters) and notes under 1,000 characters.", "error")
        return redirect(url_for("world.planner"))
    try:
        start_date_text = request.form.get("start_date", "").strip()
        end_date_text = request.form.get("end_date", "").strip()
        start_date = date.fromisoformat(start_date_text) if start_date_text else None
        end_date = date.fromisoformat(end_date_text) if end_date_text else None
        budget_text = request.form.get("budget_inr", "").strip()
        budget = int(budget_text) if budget_text else None
        if end_date and start_date and end_date < start_date:
            raise ValueError("Trip end date must be on or after its start date.")
        if budget is not None and not 0 <= budget <= 100_000_000:
            raise ValueError("Enter a trip budget between ₹0 and ₹10,00,00,000.")
        place_id = request.form.get("place_id", type=int)
        place = db.session.get(WorldPlace, place_id) if place_id else None
        latitude_text, longitude_text = request.form.get("lat", ""), request.form.get("lon", "")
        if bool(latitude_text) != bool(longitude_text):
            raise ValueError("Both coordinates are required for a map-selected stop.")
        latitude = float(latitude_text) if latitude_text else None
        longitude = float(longitude_text) if longitude_text else None
        if latitude is not None and (
            not -90 <= latitude <= 90 or not -180 <= longitude <= 180
        ):
            raise ValueError("Map coordinates are outside the supported range.")
        if place_id and not place:
            abort(404)
        plan = TravelPlan(
            user_id=current_user.id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            budget_inr=budget,
            notes=notes,
        )
        db.session.add(plan)
        db.session.flush()
        if place or latitude is not None:
            db.session.add(PlanStop(
                plan_id=plan.id,
                place_id=place.id if place else None,
                name=place.name if place else request.form.get("location_name", "").strip()[:120] or "Selected map point",
                latitude=place.latitude if place else latitude,
                longitude=place.longitude if place else longitude,
                visit_date=start_date,
                position=0,
            ))
        db.session.commit()
    except (ValueError, IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        flash(str(error) if isinstance(error, ValueError) else "Could not save this trip plan.", "error")
        return redirect(url_for("world.planner"))
    flash("Your trip plan has been saved.", "success")
    return redirect(url_for("world.plan_detail", plan_id=plan.id))


def _owned_plan(plan_id):
    plan = TravelPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
    if not plan:
        abort(404)
    return plan


@world.get("/planner/<int:plan_id>")
@login_required
def plan_detail(plan_id):
    plan = _owned_plan(plan_id)
    spent = sum(expense.amount_inr for expense in plan.expenses)
    return render_template(
        "world/plan_detail.html",
        plan=plan,
        places=WorldPlace.query.order_by(WorldPlace.country, WorldPlace.city, WorldPlace.name).all(),
        spent=spent,
        remaining=plan.budget_inr - spent if plan.budget_inr is not None else None,
    )


@world.post("/planner/<int:plan_id>/stops")
@login_required
def add_stop(plan_id):
    plan = _owned_plan(plan_id)
    place_id = request.form.get("place_id", type=int)
    place = db.session.get(WorldPlace, place_id) if place_id else None
    name = request.form.get("name", "").strip()
    notes = request.form.get("notes", "").strip()
    if len(plan.stops) >= 100 or len(notes) > 500:
        flash("A trip can contain up to 100 stops; notes are limited to 500 characters.", "error")
        return redirect(url_for("world.plan_detail", plan_id=plan.id))
    if place_id and not place:
        abort(404)
    if not place and (not name or len(name) > 120):
        flash("Choose a map place or enter a stop name under 120 characters.", "error")
        return redirect(url_for("world.plan_detail", plan_id=plan.id))
    try:
        visit_text = request.form.get("visit_date", "").strip()
        visit_date = date.fromisoformat(visit_text) if visit_text else None
        stop = PlanStop(
            plan_id=plan.id,
            place_id=place.id if place else None,
            name=place.name if place else name,
            latitude=place.latitude if place else None,
            longitude=place.longitude if place else None,
            visit_date=visit_date,
            notes=notes,
            position=len(plan.stops),
        )
        db.session.add(stop)
        db.session.commit()
    except (ValueError, IntegrityError, SQLAlchemyError):
        db.session.rollback()
        flash("Could not add that itinerary stop. Check the date and try again.", "error")
        return redirect(url_for("world.plan_detail", plan_id=plan.id))
    flash("Itinerary stop added.", "success")
    return redirect(url_for("world.plan_detail", plan_id=plan.id))


@world.post("/planner/<int:plan_id>/expenses")
@login_required
def add_expense(plan_id):
    plan = _owned_plan(plan_id)
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    try:
        amount = int(request.form.get("amount_inr", ""))
        spent_text = request.form.get("spent_on", "").strip()
        spent_on = date.fromisoformat(spent_text) if spent_text else date.today()
        if category not in EXPENSE_CATEGORIES or not description or len(description) > 160:
            raise ValueError("Choose a category and enter a description under 160 characters.")
        if not 0 <= amount <= 10_000_000:
            raise ValueError("Enter an expense between ₹0 and ₹1,00,00,000.")
        db.session.add(PlanExpense(
            plan_id=plan.id,
            category=category,
            description=description,
            amount_inr=amount,
            spent_on=spent_on,
        ))
        db.session.commit()
    except (ValueError, IntegrityError, SQLAlchemyError) as error:
        db.session.rollback()
        flash(str(error) if isinstance(error, ValueError) else "Could not save that expense.", "error")
        return redirect(url_for("world.plan_detail", plan_id=plan.id))
    flash("Expense added to your trip tracker.", "success")
    return redirect(url_for("world.plan_detail", plan_id=plan.id))


@world.post("/planner/<int:plan_id>/packing")
@login_required
def add_packing_item(plan_id):
    plan = _owned_plan(plan_id)
    label = request.form.get("label", "").strip()
    if not label or len(label) > 120:
        flash("Enter a packing item under 120 characters.", "error")
    else:
        db.session.add(PackingItem(plan_id=plan.id, label=label))
        try:
            db.session.commit()
            flash("Packing item added.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("That packing item is already on your list.", "info")
    return redirect(url_for("world.plan_detail", plan_id=plan.id))


@world.post("/planner/<int:plan_id>/packing/<int:item_id>/toggle")
@login_required
def toggle_packing_item(plan_id, item_id):
    plan = _owned_plan(plan_id)
    item = PackingItem.query.filter_by(id=item_id, plan_id=plan.id).first_or_404()
    item.is_packed = not item.is_packed
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not update that packing item.", "error")
    return redirect(url_for("world.plan_detail", plan_id=plan.id))


@world.post("/world-map/places/<int:place_id>/reviews")
@login_required
def add_review(place_id):
    place = db.session.get(WorldPlace, place_id)
    if not place:
        abort(404)
    body = request.form.get("body", "").strip()
    rating = request.form.get("rating", type=int)
    if rating not in range(1, 6) or not body or len(body) > 1000:
        flash("Choose a rating from 1 to 5 and add a review under 1,000 characters.", "error")
        return redirect(url_for("world.explore_map", q=place.name))
    db.session.add(PlaceReview(
        user_id=current_user.id,
        place_id=place.id,
        rating=rating,
        body=body,
    ))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("You have already reviewed this place.", "info")
        return redirect(url_for("world.explore_map", q=place.name))
    flash("Your traveller review was saved. It is user-submitted and not independently verified.", "success")
    return redirect(url_for("world.explore_map", q=place.name))
