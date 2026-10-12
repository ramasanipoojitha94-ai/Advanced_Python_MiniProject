from datetime import date, datetime, time, timedelta
import os
import time as time_mod
from werkzeug.utils import secure_filename

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from flask_login import current_user, login_required
from sqlalchemy import func

from yatrago import db
from yatrago.content import BUS_IMAGES, FOODS
from yatrago.discovery_data import (
    DESTINATION_COLLECTIONS,
    DESTINATION_MAP_CITIES,
    TEMPLE_PHOTOS,
)
from yatrago.models import (
    Booking,
    Bus,
    Destination,
    FlightBooking,
    RecentDestination,
    Route,
    SavedDestination,
    SavedWorldPlace,
    StayBooking,
    StayProperty,
    TravelPlan,
    Trip,
    TransportBooking,
    TransportOption,
    WorldPlace,
)
from yatrago.transport import MODES, supported_locations

main = Blueprint("main", __name__)


@main.app_context_processor
def inject_today():
    return {
        "today": date.today().isoformat(),
        "today_date": date.today(),
        "now": datetime.now(),
        "timedelta": timedelta,
    }


@main.get("/")
def home():
    routes = Route.query.order_by(Route.source, Route.destination).all()
    featured_names = set().union(*DESTINATION_COLLECTIONS.values())
    discovery_destinations = Destination.query.filter(
        Destination.name.in_(featured_names)
    ).order_by(Destination.region, Destination.name).all()
    destination_collections = {
        destination.id: [
            label for label, names in DESTINATION_COLLECTIONS.items()
            if destination.name in names
        ]
        for destination in discovery_destinations
    }
    seasonal_names = {
        12: ("Goa", "Munnar", "Jaipur", "Kerala Backwaters", "Rishikesh"),
        1: ("Goa", "Munnar", "Jaipur", "Kerala Backwaters", "Rishikesh"),
        2: ("Goa", "Munnar", "Jaipur", "Kerala Backwaters", "Rishikesh"),
        3: ("Ooty", "Coorg", "Manali", "Darjeeling", "Munnar"),
        4: ("Ooty", "Coorg", "Manali", "Darjeeling", "Munnar"),
        5: ("Ooty", "Coorg", "Manali", "Darjeeling", "Munnar"),
        6: ("Ooty", "Coorg", "Manali", "Darjeeling", "Munnar"),
        7: ("Coorg", "Wayanad", "Jog Falls", "Kerala Backwaters", "Chikmagalur"),
        8: ("Coorg", "Wayanad", "Jog Falls", "Kerala Backwaters", "Chikmagalur"),
        9: ("Coorg", "Wayanad", "Jog Falls", "Kerala Backwaters", "Chikmagalur"),
        10: ("Mysuru", "Hampi", "Jaipur", "Varanasi", "Pondicherry"),
        11: ("Mysuru", "Hampi", "Jaipur", "Varanasi", "Pondicherry"),
    }
    seasonal_destinations = Destination.query.filter(
        Destination.name.in_(seasonal_names[date.today().month])
    ).order_by(Destination.name).all()
    weekend_names = DESTINATION_COLLECTIONS["Weekend getaways"]
    weekend_by_name = {
        item.name: item for item in Destination.query.filter(
            Destination.name.in_(weekend_names)
        ).all()
    }
    saved_destination_ids = {
        saved.destination_id
        for saved in SavedDestination.query.filter_by(user_id=current_user.id).all()
    } if current_user.is_authenticated else set()
    return render_template(
        "home.html",
        routes=routes,
        bus_types=[value[0] for value in db.session.query(Bus.bus_type).distinct().order_by(Bus.bus_type)],
        destinations=discovery_destinations,
        destination_collections=destination_collections,
        temple_photo_credits=TEMPLE_PHOTOS,
        saved_destination_ids=saved_destination_ids,
        destination_categories=list(DESTINATION_COLLECTIONS),
        weekend_destinations=[
            weekend_by_name[name] for name in weekend_names if name in weekend_by_name
        ],
        seasonal_destinations=seasonal_destinations,
        nearby_places=WorldPlace.query.filter_by(city="Bengaluru")
        .order_by(WorldPlace.id.desc()).limit(5).all(),
        hotels=StayProperty.query.order_by(StayProperty.price_per_night).limit(3).all(),
        foods=FOODS[:3],
        modes={key: MODES[key] for key in ("bus", "flight", "train", "cab")},
        recent_modes=MODES,
        mode="bus",
        locations=supported_locations(),
        recent_searches=session.get("transport_recent_searches", []),
    )


@main.get("/search")
def search():
    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    travel_date = request.args.get("date", "").strip()
    departure_time = request.args.get("departure_time", "").strip()
    try:
        day = date.fromisoformat(travel_date)
        selected_time = time.fromisoformat(departure_time) if departure_time else None
    except ValueError:
        flash("Choose a valid journey date.", "error")
        return render_template("search/results.html", trips=[], search_values=request.args)
    if not source or not destination or source.casefold() == destination.casefold():
        flash("Choose different source and destination cities.", "error")
        return render_template("search/results.html", trips=[], search_values=request.args)
    if day < date.today():
        flash("Journey date cannot be in the past.", "error")
        return render_template("search/results.html", trips=[], search_values=request.args)
    passengers = request.args.get("passengers", default=1, type=int)
    if not 1 <= passengers <= 6:
        flash("Choose between 1 and 6 passengers.", "error")
        return render_template("search/results.html", trips=[], search_values=request.args)

    query = Trip.query.join(Trip.route).join(Trip.bus).filter(
        func.lower(Route.source) == source.lower(),
        func.lower(Route.destination) == destination.lower(),
        Trip.departure_at >= datetime.combine(day, time.min),
        Trip.departure_at < datetime.combine(day + timedelta(days=1), time.min),
    )
    if selected_time:
        query = query.filter(
            Trip.departure_at >= datetime.combine(day, selected_time)
        )
    if day == date.today():
        query = query.filter(Trip.departure_at > datetime.now())
    max_price = request.args.get("max_price", type=int)
    if max_price is not None and max_price > 0:
        query = query.filter(Trip.fare <= max_price)
    bus_type = request.args.get("bus_type", "").strip()
    if bus_type:
        query = query.filter(Bus.bus_type == bus_type)
    amenity = request.args.get("amenity", "").strip()
    if amenity in {"Wi-Fi", "Charging point", "Blanket", "Water bottle"}:
        query = query.filter(Bus.amenities.ilike(f"%{amenity}%"))
    departure = request.args.get("departure", "")
    if departure in {"morning", "evening", "night"}:
        hours = {"morning": range(5, 12), "evening": range(12, 18), "night": range(18, 24)}[departure]
        query = query.filter(db.extract("hour", Trip.departure_at).in_(list(hours)))
    sort = request.args.get("sort", "departure")
    if sort == "price":
        query = query.order_by(Trip.fare, Trip.departure_at)
    elif sort == "duration":
        query = query.order_by(
            func.julianday(Trip.arrival_at) - func.julianday(Trip.departure_at),
            Trip.departure_at,
        )
    else:
        query = query.order_by(Trip.departure_at)
    trips = query.all()
    for index, trip in enumerate(trips):
        trip.available_seats = sum(seat.booking_id is None for seat in trip.seats)
        trip.sample_image = BUS_IMAGES[index % len(BUS_IMAGES)]
    routes = Route.query.order_by(Route.source, Route.destination).all()
    return render_template(
        "search/results.html",
        trips=trips,
        routes=routes,
        search_values=request.args,
        selected_bus_type=bus_type,
        selected_departure=departure,
        selected_sort=sort,
        selected_amenity=amenity,
        passenger_count=passengers,
    )


@main.get("/dashboard")
@login_required
def dashboard():
    featured_names = (
        "Tirupati Balaji", "Mysuru", "Hampi", "Goa", "Ooty",
        "Taj Mahal", "Phoenix Marketcity Bengaluru", "Munnar",
    )
    destinations_by_name = {
        destination.name: destination
        for destination in Destination.query.filter(
            Destination.name.in_(featured_names)
        ).all()
    }
    return render_template(
        "dashboard.html",
        featured_destinations=[
            destinations_by_name[name]
            for name in featured_names
            if name in destinations_by_name
        ],
        locations=supported_locations(),
    )


@main.post('/profile/upload')
@login_required
def upload_avatar():
    """Accept a profile image upload and save under static/uploads/."""
    file = request.files.get('avatar')
    if not file or file.filename == "":
        flash("No image selected.", "error")
        return redirect(url_for('main.dashboard'))
    filename = secure_filename(file.filename)
    if '.' not in filename:
        flash("Invalid file name.", "error")
        return redirect(url_for('main.dashboard'))
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    if ext not in allowed:
        flash("Unsupported image format. Use png, jpg, jpeg, gif, webp or svg.", "error")
        return redirect(url_for('main.dashboard'))
    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    saved_name = f"user_{current_user.id}_{int(time_mod.time())}.{ext}"
    save_path = os.path.join(uploads_dir, saved_name)
    try:
        file.save(save_path)
    except Exception:
        flash("Failed to save image.", "error")
        return redirect(url_for('main.dashboard'))
    # store path relative to static folder
    current_user.avatar = f"uploads/{saved_name}"
    db.session.commit()
    flash("Profile photo updated.", "success")
    return redirect(url_for('main.dashboard'))


@main.get("/trips")
@login_required
def trips():
    history = (
        Booking.query.filter_by(user_id=current_user.id)
        .join(Booking.trip)
        .order_by(Trip.departure_at.desc())
        .all()
    )
    flight_history = (
        FlightBooking.query.filter_by(user_id=current_user.id)
        .order_by(FlightBooking.created_at.desc())
        .all()
    )
    stay_history = (
        StayBooking.query.filter_by(user_id=current_user.id)
        .order_by(StayBooking.check_in.desc())
        .all()
    )
    transport_history = (
        TransportBooking.query.filter_by(user_id=current_user.id)
        .order_by(TransportBooking.travel_date.desc())
        .all()
    )
    itinerary_destinations = {
        item.trip.route.destination for item in history
    } | {
        item.outbound_flight.destination_city for item in flight_history
    } | {
        item.property.destination.name for item in stay_history
    } | {
        item.option.destination for item in transport_history
    }
    recommendations = {}
    booked_stay_ids = {item.property_id for item in stay_history}
    for city in itinerary_destinations:
        destination = Destination.query.filter_by(name=city).first()
        if destination:
            query = StayProperty.query.filter_by(destination_id=destination.id)
            if city == next(
                (item.property.destination.name for item in stay_history if item.property.destination.name == city),
                None,
            ):
                query = query.filter(StayProperty.id.notin_(booked_stay_ids))
            suggestions = query.limit(2).all()
            if suggestions:
                recommendations[city] = suggestions
    return render_template(
        "trips.html",
        bookings=history,
        flight_bookings=flight_history,
        stay_bookings=stay_history,
        transport_bookings=transport_history,
        recommendations=recommendations,
    )


@main.get("/destinations")
def destinations():
    query = request.args.get("q", "").strip().casefold()
    category = request.args.get("category", "")
    region = request.args.get("region", "")
    max_budget = request.args.get("max_budget", type=int)
    statement = Destination.query
    if query:
        statement = statement.filter(
            db.or_(
                Destination.name.ilike(f"%{query}%"),
                Destination.state.ilike(f"%{query}%"),
                Destination.attractions.ilike(f"%{query}%"),
            )
        )
    if category:
        statement = statement.filter(Destination.category == category)
    if region:
        statement = statement.filter(Destination.region == region)
    if max_budget:
        statement = statement.filter(Destination.budget_min <= max_budget)
    items = statement.order_by(Destination.region, Destination.name).all()
    saved_ids = {
        saved.destination_id for saved in SavedDestination.query.filter_by(user_id=current_user.id).all()
    } if current_user.is_authenticated else set()
    regions = [value[0] for value in db.session.query(Destination.region).distinct().order_by(Destination.region)]
    categories = [value[0] for value in db.session.query(Destination.category).distinct().order_by(Destination.category)]
    return render_template(
        "explore/destinations.html",
        items=items,
        query=request.args.get("q", ""),
        category=category,
        region=region,
        max_budget=request.args.get("max_budget", ""),
        regions=regions,
        categories=categories,
        saved_ids=saved_ids,
    )


@main.get("/destinations/<int:destination_id>")
def destination_detail(destination_id):
    destination = db.session.get(Destination, destination_id)
    if not destination:
        abort(404)
    properties = StayProperty.query.filter_by(destination_id=destination.id).order_by(StayProperty.price_per_night).all()
    transport_options = []
    seen_modes = set()
    for option in TransportOption.query.filter(
        db.or_(
            TransportOption.origin == destination.name,
            TransportOption.destination == destination.name,
        ),
        TransportOption.departure_at >= datetime.combine(date.today(), time.min),
    ).order_by(TransportOption.departure_at).all():
        if option.mode not in seen_modes:
            seen_modes.add(option.mode)
            transport_options.append(option)
    if current_user.is_authenticated:
        recent = RecentDestination.query.filter_by(
            user_id=current_user.id, destination_id=destination.id
        ).first()
        if recent:
            recent.viewed_at = datetime.now()
        else:
            recent = RecentDestination(user_id=current_user.id, destination_id=destination.id)
            db.session.add(recent)
        db.session.commit()
        is_saved = SavedDestination.query.filter_by(
            user_id=current_user.id, destination_id=destination.id
        ).first() is not None
    else:
        is_saved = False
    return render_template(
        "explore/destination_detail.html",
        destination=destination,
        properties=properties,
        transport_options=transport_options,
        is_saved=is_saved,
        nearby_query=DESTINATION_MAP_CITIES.get(destination.name, destination.name),
        photo_credit=TEMPLE_PHOTOS.get(destination.name),
    )


@main.post("/destinations/<int:destination_id>/save")
@login_required
def toggle_destination_save(destination_id):
    destination = db.session.get(Destination, destination_id)
    if not destination:
        abort(404)
    saved = SavedDestination.query.filter_by(
        user_id=current_user.id, destination_id=destination.id
    ).first()
    if saved:
        db.session.delete(saved)
        flash(f"{destination.name} removed from saved places.", "info")
    else:
        db.session.add(SavedDestination(user_id=current_user.id, destination_id=destination.id))
        flash(f"Saved for later: {destination.name}.", "success")
    db.session.commit()
    return redirect(url_for("main.destination_detail", destination_id=destination.id))


@main.get("/hotels")
def hotels():
    statement = StayProperty.query.join(StayProperty.destination)
    city = request.args.get("city", "").strip()
    property_type = request.args.get("type", "").strip()
    amenity = request.args.get("amenity", "").strip()
    min_rating = request.args.get("rating", type=float)
    if city:
        statement = statement.filter(Destination.name == city)
    if property_type in {"Hostel", "Guesthouse", "Homestay", "Budget hotel"}:
        statement = statement.filter(StayProperty.property_type == property_type)
    if amenity:
        statement = statement.filter(StayProperty.amenities.ilike(f"%{amenity}%"))
    if min_rating:
        statement = statement.filter(StayProperty.sample_rating >= min_rating)
    max_price = request.args.get("max_price", type=int)
    if max_price is not None:
        statement = statement.filter(StayProperty.price_per_night <= max_price)
    sort = request.args.get("sort", "recommended")
    if sort == "price":
        statement = statement.order_by(StayProperty.price_per_night)
    elif sort == "rating":
        statement = statement.order_by(StayProperty.sample_rating.desc())
    else:
        statement = statement.order_by(StayProperty.price_per_night)
    items = statement.all()
    cities = [value[0] for value in db.session.query(Destination.name).join(StayProperty).distinct().order_by(Destination.name)]
    return render_template(
        "explore/hotels.html",
        items=items,
        max_price=request.args.get("max_price", ""),
        sort=sort,
        city=city,
        cities=cities,
        property_type=property_type,
        amenity=amenity,
        rating=request.args.get("rating", ""),
    )


@main.get("/food")
def food():
    region = request.args.get("region", "")
    city = request.args.get("city", "")
    query = request.args.get("q", "").strip().casefold()
    items = [
        item for item in FOODS
        if (not region or item["region"] == region)
        and (not city or item["city"] == city)
        and (not query or query in item["dish"].casefold() or query in item["city"].casefold())
    ]
    regions = sorted({item["region"] for item in FOODS})
    cities = sorted({item["city"] for item in FOODS})
    return render_template(
        "explore/food.html",
        items=items,
        regions=regions,
        cities=cities,
        region=region,
        city=city,
        query=request.args.get("q", ""),
    )
