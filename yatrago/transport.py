from datetime import date, datetime, time, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from yatrago import db
from yatrago.content import photo
from yatrago.models import (
    Destination,
    Bus,
    Flight,
    Route,
    TransportBooking,
    TransportOption,
    TransportSeat,
)
from yatrago.transport_data import MODE_LABELS
from yatrago.transport_services import (
    TransportBookingError,
    cancel_transport_booking,
    create_transport_booking,
)

transport = Blueprint("transport", __name__)
MODES = {
    "bus": ("Buses", "🚌"),
    "flight": ("Flights", "✈️"),
    **{mode: (details[0], details[1]) for mode, details in MODE_LABELS.items()},
}
RESULT_IMAGES = [
    photo("1511919884226-fd3cad34687c"),
    photo("1549317661-bd32c8ce0db2"),
    photo("1517248135467-4c7edcad34c4"),
    photo("1494515843206-f3117d3f51b7"),
    photo("1512453979798-5ea266f8880c"),
    photo("1520250497591-112f2f40a3f4"),
    photo("1503376780353-7e6692767b70"),
    photo("1519501025264-65ba15a82390"),
    photo("1502877338535-766e1452684a"),
    photo("1492144534655-ae79c964c9d7"),
]


def supported_locations():
    locations = set()
    locations.update(value[0] for value in db.session.query(Destination.name).all())
    for origin, destination in db.session.query(TransportOption.origin, TransportOption.destination):
        locations.add(origin)
        locations.add(destination)
    for source, destination in db.session.query(Route.source, Route.destination):
        locations.add(source)
        locations.add(destination)
    for flight in db.session.query(Flight.origin_city, Flight.destination_city):
        locations.update(flight)
    return sorted(locations)


@transport.get("/transport")
def search():
    mode = request.args.get("mode", "bus").strip().lower()
    if mode not in MODES:
        mode = "bus"
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    travel_text = request.args.get("date", "").strip()
    return_text = request.args.get("return_date", "").strip()
    departure_time = request.args.get("departure_time", "").strip()
    trip_type = request.args.get("trip_type", "oneway")
    passengers = request.args.get("passengers", 1, type=int)
    service_type = request.args.get("service_type", "").strip()
    bus_type = request.args.get("bus_type", "").strip()
    cabin_class = request.args.get("cabin_class", "Economy").strip()
    sort = request.args.get("sort", "price")
    max_price = request.args.get("max_price", type=int)
    max_stops = request.args.get("max_stops", type=int)
    results = []
    return_results = []
    error = None
    is_search = bool(origin and travel_text)
    if is_search:
        try:
            day = date.fromisoformat(travel_text)
            return_day = date.fromisoformat(return_text) if return_text else None
            if origin not in supported_locations():
                raise ValueError("Choose a starting location from the supported list.")
            if mode not in {"car", "bike"} and destination not in supported_locations():
                raise ValueError("Choose a destination from the supported list.")
            if (
                destination
                and origin.casefold() == destination.casefold()
                and mode not in {"car", "bike"}
            ):
                raise ValueError("Choose different starting and ending locations.")
            if day < date.today():
                raise ValueError("Choose a travel date that is today or later.")
            if not 1 <= passengers <= 8:
                raise ValueError("Choose between 1 and 8 passengers.")
            if trip_type not in {"oneway", "roundtrip", "rental"}:
                raise ValueError("Choose a supported trip type.")
            if trip_type == "roundtrip" and mode not in {"cab", "flight"}:
                raise ValueError("Round trips are available for taxis and flights.")
            if mode in {"car", "bike"} and (
                trip_type != "rental" or return_day is None or return_day <= day
            ):
                raise ValueError("Choose a rental return date after the pickup date.")
            if trip_type == "roundtrip" and (return_day is None or return_day <= day):
                raise ValueError("Choose a return date after your departure date.")
            if mode == "bus":
                recent = {
                    "mode": mode, "origin": origin, "destination": destination,
                    "date": travel_text, "trip_type": trip_type,
                }
                session["transport_recent_searches"] = (
                    [recent] + [
                        item for item in session.get("transport_recent_searches", [])
                        if item != recent
                    ]
                )[:5]
                return redirect(url_for(
                    "main.search", source=origin, destination=destination,
                    date=travel_text, passengers=passengers, departure_time=departure_time,
                    bus_type=bus_type,
                ))
            if mode == "flight":
                if cabin_class not in {"Economy", "Business"}:
                    raise ValueError("Choose Economy or Business cabin class.")
                recent = {
                    "mode": mode, "origin": origin, "destination": destination,
                    "date": travel_text, "trip_type": trip_type,
                }
                session["transport_recent_searches"] = (
                    [recent] + [
                        item for item in session.get("transport_recent_searches", [])
                        if item != recent
                    ]
                )[:5]
                return redirect(url_for(
                    "travel.flights",
                    origin=origin,
                    destination=destination,
                    depart_date=travel_text,
                    return_date=return_text,
                    depart_time=departure_time,
                    cabin_class=cabin_class,
                    trip_type="roundtrip" if trip_type == "roundtrip" else "oneway",
                    passengers=passengers,
                ))
            query = TransportOption.query.filter(
                TransportOption.mode == mode,
                TransportOption.origin == origin,
                func.date(TransportOption.departure_at) == day.isoformat(),
            )
            if mode not in {"car", "bike"}:
                query = query.filter(TransportOption.destination == destination)
            if departure_time:
                try:
                    requested_time = time.fromisoformat(departure_time)
                except ValueError:
                    raise ValueError("Choose a valid departure time.") from None
                query = query.filter(
                    TransportOption.departure_at >= datetime.combine(day, requested_time)
                )
            if service_type:
                query = query.filter(TransportOption.service_type == service_type)
            if max_price and max_price > 0:
                query = query.filter(TransportOption.fare <= max_price)
            if max_stops in (0, 1):
                query = query.filter(TransportOption.stops <= max_stops)
            if sort == "price":
                query = query.order_by(TransportOption.fare, TransportOption.departure_at)
            elif sort == "duration":
                query = query.order_by(TransportOption.duration_minutes, TransportOption.fare)
            else:
                query = query.order_by(TransportOption.departure_at)
            results = query.all()
            for index, option in enumerate(results):
                option.sample_image = RESULT_IMAGES[index % len(RESULT_IMAGES)]
                option.available_seats = sum(seat.booking_id is None for seat in option.seats)
            if mode == "cab" and trip_type == "roundtrip" and return_day:
                return_results = TransportOption.query.filter(
                    TransportOption.mode == mode,
                    TransportOption.origin == destination,
                    TransportOption.destination == origin,
                    func.date(TransportOption.departure_at) == return_day.isoformat(),
                ).order_by(TransportOption.fare).all()
            prior = session.get("transport_recent_searches", [])
            recent = {
                "mode": mode, "origin": origin, "destination": destination,
                "date": travel_text, "trip_type": trip_type,
            }
            session["transport_recent_searches"] = (
                [recent] + [item for item in prior if item != recent]
            )[:5]
        except ValueError as exc:
            error = str(exc) or "Check your transport search details."
    service_types = []
    if mode not in {"bus", "flight"}:
        service_types = [
            value[0] for value in db.session.query(TransportOption.service_type)
            .filter(TransportOption.mode == mode).distinct().order_by(TransportOption.service_type)
        ]
    return render_template(
        "transport/search.html",
        modes=MODES,
        mode=mode,
        mode_label=MODES[mode][0],
        origin=origin,
        destination=destination,
        travel_date=travel_text,
        return_date=return_text,
        departure_time=departure_time,
        trip_type=trip_type,
        passengers=passengers,
        service_type=service_type,
        service_types=service_types,
        bus_types=[
            value[0] for value in db.session.query(Bus.bus_type).distinct().order_by(Bus.bus_type)
        ],
        selected_bus_type=bus_type,
        cabin_class=cabin_class,
        sort=sort,
        max_price=request.args.get("max_price", ""),
        max_stops=request.args.get("max_stops", ""),
        results=results,
        return_results=return_results,
        is_search=is_search,
        error=error,
        locations=supported_locations(),
        recent_searches=session.get("transport_recent_searches", []),
    )


@transport.get("/transport/<int:option_id>/book")
@login_required
def booking_form(option_id):
    option = db.session.get(TransportOption, option_id)
    if option is None:
        abort(404)
    passenger_count = request.args.get("passengers", 1, type=int)
    if not 1 <= passenger_count <= 8:
        abort(400)
    trip_type = request.args.get("trip_type", "oneway")
    return_date_text = request.args.get("return_date", "")
    return_options = []
    if option.mode == "cab" and trip_type == "roundtrip":
        try:
            return_day = date.fromisoformat(return_date_text)
        except ValueError:
            abort(400)
        return_options = TransportOption.query.filter(
            TransportOption.mode == "cab",
            TransportOption.origin == option.destination,
            TransportOption.destination == option.origin,
            func.date(TransportOption.departure_at) == return_day.isoformat(),
        ).order_by(TransportOption.fare).all()
    available_seats = [
        seat for seat in option.seats if seat.booking_id is None
    ] if option.mode == "train" else []
    return render_template(
        "transport/book.html",
        option=option,
        passenger_count=passenger_count,
        trip_type=trip_type,
        return_date=return_date_text,
        return_options=return_options,
        available_seats=available_seats,
    )


@transport.post("/transport/<int:option_id>/book")
@login_required
def create_booking(option_id):
    option = db.session.get(TransportOption, option_id)
    if not option:
        abort(404)
    return_date_text = request.form.get("rental_return_date") or request.form.get("return_date", "")
    try:
        passenger_count = request.form.get("passenger_count", 0, type=int)
        if not 1 <= passenger_count <= 8:
            raise TransportBookingError("Choose between 1 and 8 passengers.")
        trip_type = request.form.get("trip_type", "oneway")
        return_option_id = request.form.get("return_option_id", type=int)
        return_date = date.fromisoformat(return_date_text) if return_date_text else None
        passengers = [
            {
                "name": request.form.get(f"name_{index}", ""),
                "age": request.form.get(f"age_{index}", ""),
            }
            for index in range(passenger_count)
        ]
        seat_ids = [int(value) for value in request.form.getlist("seat_ids")]
        booking = create_transport_booking(
            current_user,
            option.id,
            passengers,
            trip_type=trip_type,
            return_option_id=return_option_id,
            return_date=return_date,
            pickup_address=request.form.get("pickup_address", ""),
            dropoff_address=request.form.get("dropoff_address", ""),
            rental_driver=request.form.get("rental_driver", ""),
            seat_ids=seat_ids,
        )
    except (TransportBookingError, ValueError) as exc:
        flash(str(exc) or "Enter valid transport booking details.", "error")
        return redirect(url_for(
            "transport.booking_form",
            option_id=option.id,
            passengers=request.form.get("passenger_count", 1),
            trip_type=request.form.get("trip_type", "oneway"),
            return_date=return_date_text,
        ))
    flash("Your sample transport booking has been saved.", "success")
    return redirect(url_for("transport.confirmation", reference=booking.reference))


@transport.get("/transport/booking/<reference>")
@login_required
def confirmation(reference):
    booking = TransportBooking.query.filter_by(
        reference=reference, user_id=current_user.id
    ).first_or_404()
    destination = Destination.query.filter_by(name=booking.option.destination).first()
    return render_template(
        "transport/confirmation.html", booking=booking, destination=destination
    )


@transport.post("/transport/booking/<reference>/cancel")
@login_required
def cancel(reference):
    booking = TransportBooking.query.filter_by(
        reference=reference, user_id=current_user.id
    ).first_or_404()
    try:
        cancel_transport_booking(booking, current_user)
        flash("Your sample transport booking has been cancelled.", "success")
    except TransportBookingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.trips"))
