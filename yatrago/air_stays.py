from datetime import date, datetime, time, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from yatrago import db
from yatrago.content import FLIGHT_IMAGES
from yatrago.models import (
    Destination,
    Flight,
    FlightBooking,
    FlightSeat,
    StayBooking,
    StayProperty,
)
from yatrago.search_catalog import AIRPORT_DATA, AIRPORTS, resolve_airport
from yatrago.search_providers import demo_transport_provider
from yatrago.travel_services import (
    TravelBookingError,
    book_flight,
    book_stay,
    cancel_flight_booking,
    cancel_stay_booking,
)

travel = Blueprint("travel", __name__)


def _search_flights(
    origin, destination, travel_day, cabin_class, max_price, max_stops, sort,
    depart_time=None, passengers=1,
):
    demo_transport_provider.flight_departures(origin, destination, travel_day)
    query = Flight.query.filter(
        Flight.origin_city == origin,
        Flight.destination_city == destination,
        func.date(Flight.departure_at) == travel_day.isoformat(),
        Flight.departure_at > datetime.now(),
    )
    if depart_time:
        query = query.filter(
            Flight.departure_at >= datetime.combine(travel_day, depart_time)
        )
    fare_field = Flight.fare_economy if cabin_class == "Economy" else Flight.fare_business
    if max_price is not None and max_price > 0:
        query = query.filter(fare_field <= max_price)
    if max_stops in (0, 1):
        query = query.filter(Flight.stops <= max_stops)
    if sort == "price":
        query = query.order_by(fare_field, Flight.departure_at)
    elif sort == "duration":
        query = query.order_by(func.julianday(Flight.arrival_at) - func.julianday(Flight.departure_at))
    elif sort == "stops":
        query = query.order_by(Flight.stops, fare_field)
    elif sort == "departure":
        query = query.order_by(Flight.departure_at)
    else:
        query = query.order_by(fare_field, Flight.departure_at)
    flights = query.all()
    flights = [
        flight for flight in flights
        if sum(seat.booking_id is None for seat in flight.seats) >= passengers
    ]
    for index, flight in enumerate(flights):
        flight.available_seats = sum(seat.booking_id is None for seat in flight.seats)
        flight.sample_image = FLIGHT_IMAGES[index % len(FLIGHT_IMAGES)]
        flight.origin_airport_display = AIRPORTS.get(
            flight.origin_city, (flight.origin_code, flight.origin_airport)
        )[1]
        flight.destination_airport_display = AIRPORTS.get(
            flight.destination_city, (flight.destination_code, flight.destination_airport)
        )[1]
    return flights


@travel.get("/flights")
def flights():
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    outbound_text = request.args.get("depart_date", "").strip()
    departure_time_text = request.args.get("depart_time", "").strip()
    return_text = request.args.get("return_date", "").strip()
    trip_type = request.args.get("trip_type", "oneway")
    cabin_class = request.args.get("cabin_class", "Economy")
    passengers = request.args.get("passengers", default=1, type=int)
    sort = request.args.get("sort", "price")
    max_price = request.args.get("max_price", type=int)
    raw_stops = request.args.get("max_stops", "")
    max_stops = int(raw_stops) if raw_stops in {"0", "1"} else None
    results = []
    return_results = []
    error = None
    is_search = bool(origin and destination and outbound_text)
    if is_search:
        try:
            outbound_day = date.fromisoformat(outbound_text)
            return_day = date.fromisoformat(return_text) if trip_type == "roundtrip" else None
            departure_time = time.fromisoformat(departure_time_text) if departure_time_text else None
            origin = resolve_airport(origin)
            destination = resolve_airport(destination)
            if not origin or not destination:
                raise ValueError("Choose airports by city, airport name, or IATA code.")
            if origin == destination:
                raise ValueError("Choose two different airports.")
            if cabin_class not in {"Economy", "Business"}:
                raise ValueError("Choose Economy or Business cabin.")
            if trip_type not in {"oneway", "roundtrip"} or not 1 <= passengers <= 6:
                raise ValueError("Choose a trip type and between 1 and 6 passengers.")
            if outbound_day < date.today() or (
                return_day and (return_day <= outbound_day or return_day < date.today())
            ):
                raise ValueError("Choose valid future travel dates.")
            results = _search_flights(
                origin, destination, outbound_day, cabin_class, max_price, max_stops, sort,
                departure_time, passengers,
            )
            if return_day:
                return_results = _search_flights(
                    destination, origin, return_day, cabin_class, None, None, "price",
                    passengers=passengers,
                )
        except ValueError as exc:
            error = str(exc) or "Choose valid travel dates."
            results = []
    return render_template(
        "flights/search.html",
        airports=sorted(AIRPORTS.items()),
        airport_data=AIRPORT_DATA,
        origin=origin,
        destination=destination,
        depart_date=outbound_text,
        depart_time=departure_time_text,
        return_date=return_text,
        trip_type=trip_type,
        cabin_class=cabin_class,
        passengers=passengers,
        sort=sort,
        max_price=request.args.get("max_price", ""),
        max_stops=raw_stops,
        results=results,
        return_results=return_results,
        is_search=is_search,
        error=error,
    )


@travel.get("/flights/<int:flight_id>/book")
@login_required
def flight_booking_form(flight_id):
    flight = db.session.get(Flight, flight_id)
    if not flight or flight.departure_at <= datetime.now():
        abort(404)
    passengers = request.args.get("passengers", 1, type=int)
    cabin_class = request.args.get("cabin_class", "Economy")
    trip_type = request.args.get("trip_type", "oneway")
    return_date = request.args.get("return_date", "")
    if not 1 <= passengers <= 6 or cabin_class not in {"Economy", "Business"}:
        abort(400)
    return_flights = []
    if trip_type == "roundtrip":
        try:
            return_day = date.fromisoformat(return_date)
        except ValueError:
            abort(400)
        return_flights = _search_flights(
            flight.destination_city, flight.origin_city, return_day, cabin_class, None, None, "price"
        )
    return render_template(
        "flights/book.html",
        flight=flight,
        return_flights=return_flights,
        return_date=return_date,
        trip_type=trip_type,
        cabin_class=cabin_class,
        passengers=passengers,
    )


@travel.post("/flights/<int:flight_id>/book")
@login_required
def create_flight_booking(flight_id):
    try:
        passenger_count = request.form.get("passenger_count", 0, type=int)
        if not 1 <= passenger_count <= 6:
            raise TravelBookingError("Flight bookings are limited to 1–6 travellers.")
        return_id = request.form.get("return_flight_id", type=int)
        trip_type = request.form.get("trip_type")
        return_date = None
        if trip_type == "roundtrip" and not return_id:
            raise TravelBookingError("Choose a return flight to complete your round trip.")
        if trip_type == "roundtrip":
            try:
                return_date = date.fromisoformat(request.form.get("return_date", ""))
            except ValueError:
                raise TravelBookingError("Choose a valid return date.") from None
        passenger_details = [
            {
                "name": request.form.get(f"name_{index}", ""),
                "age": request.form.get(f"age_{index}", ""),
                "gender": request.form.get(f"gender_{index}", ""),
            }
            for index in range(passenger_count)
        ]
        booking = book_flight(
            current_user,
            flight_id,
            return_id,
            return_date,
            request.form.get("cabin_class", ""),
            passenger_details,
        )
    except (TravelBookingError, ValueError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("travel.flight_booking_form", flight_id=flight_id))
    flash("Your demo flight seats have been saved.", "success")
    return redirect(url_for("travel.flight_confirmation", reference=booking.reference))


@travel.get("/flights/booking/<reference>")
@login_required
def flight_confirmation(reference):
    booking = FlightBooking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    destination = Destination.query.filter_by(name=booking.outbound_flight.destination_city).first()
    nearby_stays = StayProperty.query.filter_by(destination_id=destination.id).limit(3).all() if destination else []
    return render_template("flights/confirmation.html", booking=booking, nearby_stays=nearby_stays)


@travel.post("/flights/booking/<reference>/cancel")
@login_required
def cancel_flight(reference):
    booking = FlightBooking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    try:
        cancel_flight_booking(booking, current_user)
        flash("Your sample flight booking has been cancelled.", "success")
    except TravelBookingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.trips"))


@travel.get("/stays/<int:property_id>")
def stay_detail(property_id):
    property_item = db.session.get(StayProperty, property_id)
    if not property_item:
        abort(404)
    return render_template("stays/detail.html", property_item=property_item)


@travel.route("/stays/<int:property_id>/book", methods=["GET", "POST"])
@login_required
def stay_booking(property_id):
    property_item = db.session.get(StayProperty, property_id)
    if not property_item:
        abort(404)
    if request.method == "POST":
        try:
            check_in = date.fromisoformat(request.form.get("check_in", ""))
            check_out = date.fromisoformat(request.form.get("check_out", ""))
            guest_count = request.form.get("guest_count", 0, type=int)
            if not 1 <= guest_count <= 8:
                raise TravelBookingError("Stay reservations are limited to 1–8 guests.")
            names = [request.form.get(f"guest_{index}", "") for index in range(guest_count)]
            booking = book_stay(
                current_user,
                property_item.id,
                check_in,
                check_out,
                names,
                request.form.get("room_type", ""),
            )
        except (ValueError, TypeError) as exc:
            flash(str(exc) or "Enter valid stay dates.", "error")
            return render_template("stays/book.html", property_item=property_item)
        flash("Your sample stay reservation is saved.", "success")
        return redirect(url_for("travel.stay_confirmation", reference=booking.reference))
    return render_template("stays/book.html", property_item=property_item)


@travel.get("/stays/booking/<reference>")
@login_required
def stay_confirmation(reference):
    booking = StayBooking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    nearby_stays = StayProperty.query.filter_by(
        destination_id=booking.property.destination_id
    ).filter(StayProperty.id != booking.property_id).limit(3).all()
    return render_template("stays/confirmation.html", booking=booking, nearby_stays=nearby_stays)


@travel.post("/stays/booking/<reference>/cancel")
@login_required
def cancel_stay(reference):
    booking = StayBooking.query.filter_by(reference=reference, user_id=current_user.id).first_or_404()
    try:
        cancel_stay_booking(booking, current_user)
        flash("Your sample stay reservation has been cancelled.", "success")
    except TravelBookingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.trips"))
