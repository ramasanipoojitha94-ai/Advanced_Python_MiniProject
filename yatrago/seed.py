from datetime import date, datetime, time, timedelta

from yatrago import db
from yatrago.content import DESTINATIONS, HOTELS
from yatrago.discovery_data import DESTINATION_SPOTLIGHTS, TEMPLE_PHOTOS
from yatrago.models import (
    Bus,
    Destination,
    Flight,
    FlightSeat,
    Route,
    Seat,
    StayProperty,
    TransportOption,
    TransportSeat,
    Trip,
    WorldPlace,
)
from yatrago.transport_data import SAMPLE_SERVICES
from yatrago.world_data import world_place_records

DEMO_ROUTES = [
    ("Bengaluru", "Hyderabad", 8.5), ("Bengaluru", "Chennai", 6),
    ("Hyderabad", "Vijayawada", 5), ("Delhi", "Jaipur", 5.5),
    ("Mumbai", "Pune", 4), ("Kochi", "Bengaluru", 10),
    ("Bengaluru", "Mysuru", 3.5), ("Bengaluru", "Coorg", 6),
    ("Bengaluru", "Ooty", 7), ("Chennai", "Tirupati", 4),
    ("Chennai", "Hyderabad", 11), ("Hyderabad", "Bengaluru", 9),
    ("Hyderabad", "Chennai", 11), ("Visakhapatnam", "Hyderabad", 12),
    ("Delhi", "Agra", 4), ("Delhi", "Amritsar", 8),
    ("Delhi", "Shimla", 9), ("Delhi", "Dehradun", 6),
    ("Delhi", "Manali", 13), ("Jaipur", "Udaipur", 7),
    ("Jaipur", "Agra", 5), ("Mumbai", "Goa", 12),
    ("Mumbai", "Ahmedabad", 9), ("Mumbai", "Nashik", 4),
    ("Pune", "Goa", 10), ("Kolkata", "Varanasi", 12),
    ("Kolkata", "Bhubaneswar", 8), ("Bhubaneswar", "Puri", 2),
    ("Guwahati", "Shillong", 4), ("Guwahati", "Gangtok", 12),
    ("Bhopal", "Indore", 4), ("Indore", "Udaipur", 9),
    ("Raipur", "Jabalpur", 7), ("Kochi", "Munnar", 4),
    ("Kochi", "Coorg", 9), ("Bengaluru", "Hampi", 7),
]
DEMO_BUSES = [
    ("Southern Star Travels", "AC Sleeper", "Wi-Fi,Charging point,Water bottle"),
    ("Highway Express", "Volvo Multi-Axle", "Wi-Fi,Charging point,Blanket"),
    ("CityLink Coaches", "AC Seater", "Charging point,Water bottle"),
    ("Night Rider", "Non-AC Sleeper", "Blanket,Reading light"),
]


def seed_demo_data():
    """Create sample buses, route schedules and seat inventory without duplicates."""
    buses = Bus.query.order_by(Bus.id).all()
    if not buses:
        buses = [Bus(operator=o, bus_type=t, amenities=a) for o, t, a in DEMO_BUSES]
        db.session.add_all(buses)
        db.session.flush()

    routes = {}
    for source, destination, _duration in DEMO_ROUTES:
        route = Route.query.filter_by(source=source, destination=destination).first()
        if route is None:
            route = Route(source=source, destination=destination)
            db.session.add(route)
            db.session.flush()
        routes[(source, destination)] = route

    today = date.today()
    for index, (source, destination, duration) in enumerate(DEMO_ROUTES):
        route = routes[(source, destination)]
        for day_offset in range(7):
            travel_date = today + timedelta(days=day_offset)
            for departure_hour, bus_offset in ((6, 0), (21, 1)):
                departure = datetime.combine(travel_date, time(departure_hour, 0))
                bus = buses[(index + bus_offset) % len(buses)]
                trip = Trip.query.filter_by(
                    route_id=route.id, bus_id=bus.id, departure_at=departure
                ).first()
                if trip is None:
                    arrival = departure + timedelta(hours=duration)
                    trip = Trip(
                        route=route,
                        bus=bus,
                        departure_at=departure,
                        arrival_at=arrival,
                        fare=650 + index * 110 + bus_offset * 120,
                    )
                    db.session.add(trip)
                    db.session.flush()
                    db.session.add_all(
                        Seat(trip_id=trip.id, seat_number=f"{row}{column}")
                        for row in range(1, 11)
                        for column in "ABCD"
                    )
    seed_destinations()
    seed_flights()
    seed_transport_options()
    seed_world_places()
    db.session.commit()


def seed_destinations():
    destinations = {}
    for item in DESTINATIONS + DESTINATION_SPOTLIGHTS:
        destination = Destination.query.filter_by(name=item["name"], state=item["state"]).first()
        if destination is None:
            destination = Destination(
                name=item["name"],
                state=item["state"],
                region=item["region"],
                category=item["category"],
                budget_min=item["budget_min"],
                budget_max=item["budget_max"],
                season=item["season"],
                description=item["description"],
                attractions=item["attractions"],
                image=item["image"],
            )
            db.session.add(destination)
            db.session.flush()
        elif item["name"] in TEMPLE_PHOTOS:
            destination.image = TEMPLE_PHOTOS[item["name"]]["image"]
        destinations[item["name"]] = destination

    for item in HOTELS:
        destination = destinations.get(item["city"])
        if destination is None:
            continue
        if not StayProperty.query.filter_by(name=item["name"], destination_id=destination.id).first():
            rating = float(item["rating"].split("·")[1]) if "·" in item["rating"] else None
            db.session.add(
                StayProperty(
                    destination_id=destination.id,
                    name=item["name"],
                    property_type=item["property_type"],
                    price_per_night=item["price"],
                    amenities=item["amenities"],
                    sample_rating=rating,
                    location_note=item["location_note"],
                    image=item["image"],
                )
            )


AIRPORTS = {
    "Bengaluru": ("BLR", "Kempegowda International Airport"),
    "Delhi": ("DEL", "Indira Gandhi International Airport"),
    "Mumbai": ("BOM", "Chhatrapati Shivaji Maharaj International Airport"),
    "Hyderabad": ("HYD", "Rajiv Gandhi International Airport"),
    "Chennai": ("MAA", "Chennai International Airport"),
    "Kolkata": ("CCU", "Netaji Subhas Chandra Bose International Airport"),
    "Kochi": ("COK", "Cochin International Airport"),
    "Goa": ("GOI", "Manohar International Airport"),
    "Pune": ("PNQ", "Pune Airport"),
    "Ahmedabad": ("AMD", "Sardar Vallabhbhai Patel International Airport"),
    "Jaipur": ("JAI", "Jaipur International Airport"),
    "Lucknow": ("LKO", "Chaudhary Charan Singh International Airport"),
    "Dubai": ("DXB", "Dubai International Airport"),
    "Singapore": ("SIN", "Singapore Changi Airport"),
    "Bangkok": ("BKK", "Suvarnabhumi Airport"),
    "Colombo": ("CMB", "Bandaranaike International Airport"),
}
_FLIGHT_ROUTES = [
    ("Bengaluru", "Delhi"), ("Bengaluru", "Mumbai"), ("Bengaluru", "Hyderabad"),
    ("Bengaluru", "Chennai"), ("Bengaluru", "Kolkata"), ("Bengaluru", "Kochi"),
    ("Bengaluru", "Goa"), ("Delhi", "Mumbai"), ("Delhi", "Jaipur"),
    ("Delhi", "Lucknow"), ("Delhi", "Kolkata"), ("Delhi", "Ahmedabad"),
    ("Mumbai", "Pune"), ("Mumbai", "Goa"), ("Mumbai", "Ahmedabad"),
    ("Mumbai", "Chennai"), ("Mumbai", "Hyderabad"), ("Hyderabad", "Chennai"),
    ("Hyderabad", "Kochi"), ("Chennai", "Kolkata"), ("Kolkata", "Lucknow"),
    ("Kochi", "Goa"), ("Jaipur", "Mumbai"), ("Ahmedabad", "Bengaluru"),
    ("Bengaluru", "Singapore"), ("Delhi", "Dubai"), ("Mumbai", "Dubai"),
    ("Chennai", "Colombo"), ("Kolkata", "Bangkok"),
]
FLIGHT_ROUTES = list(dict.fromkeys(
    _FLIGHT_ROUTES + [(destination, origin) for origin, destination in _FLIGHT_ROUTES]
))
AIRLINES = ("Akasa Air", "IndiGo", "Air India", "SpiceJet", "Air India Express")


def seed_flights():
    existing_buses = Flight.query.count()
    if existing_buses:
        return
    today = date.today()
    for route_index, (origin, destination) in enumerate(FLIGHT_ROUTES):
        origin_code, origin_airport = AIRPORTS[origin]
        destination_code, destination_airport = AIRPORTS[destination]
        airline = AIRLINES[route_index % len(AIRLINES)]
        flight_number = f"{['QP','6E','AI','SG','IX'][route_index % 5]}{101 + route_index:03d}"
        for day_offset in range(1, 15):
            travel_day = today + timedelta(days=day_offset)
            hour = 6 + (route_index * 3) % 15
            departure = datetime.combine(travel_day, time(hour, (route_index * 7) % 60))
            duration_hours = 1 + (abs(route_index * 13) % 3)
            arrival = departure + timedelta(hours=duration_hours, minutes=15)
            flight = Flight(
                origin_city=origin,
                origin_airport=origin_airport,
                origin_code=origin_code,
                destination_city=destination,
                destination_airport=destination_airport,
                destination_code=destination_code,
                airline=airline,
                flight_number=flight_number,
                departure_at=departure,
                arrival_at=arrival,
                stops=1 if route_index % 5 == 0 else 0,
                fare_economy=2800 + route_index * 95,
                fare_business=9500 + route_index * 180,
            )
            db.session.add(flight)
            db.session.flush()
            db.session.add_all(
                FlightSeat(flight_id=flight.id, seat_number=f"{row}{column}")
                for row in range(1, 7)
                for column in "ABCD"
            )


def seed_transport_options():
    if TransportOption.query.count():
        return
    today = date.today()
    sample_rows = list(SAMPLE_SERVICES)
    for row in SAMPLE_SERVICES:
        if row[0] == "cab":
            reversed_code = row[5] + "R"
            sample_rows.append((row[0], row[2], row[1], row[3], row[4], reversed_code, *row[6:]))
    options = []
    for index, row in enumerate(sample_rows):
        mode, origin, destination, provider, service_type, code, duration, stops, fare, basis, comfort, amenities, image_id = row
        for day_offset in range(1, 15):
            departure = datetime.combine(
                today + timedelta(days=day_offset),
                time(6 + (index * 3) % 15, (index * 11) % 60),
            )
            options.append(TransportOption(
                mode=mode,
                origin=origin,
                destination=destination,
                provider=provider,
                service_type=service_type,
                service_code=code,
                departure_at=departure,
                duration_minutes=duration,
                stops=stops,
                fare=fare,
                price_basis=basis,
                comfort=comfort,
                amenities=amenities,
                image=f"https://images.unsplash.com/photo-{image_id}?auto=format&fit=crop&w=1000&q=85",
            ))
    db.session.add_all(options)
    db.session.flush()
    seats = []
    for option in options:
        if option.mode == "train":
            seats.extend(
                TransportSeat(option_id=option.id, seat_number=f"{row_no}{column}")
                for row_no in range(1, 9)
                for column in "ABCD"
            )
    db.session.add_all(seats)


def seed_world_places():
    """Add curated global map examples without replacing saved user data."""
    for original_record in world_place_records():
        record = dict(original_record)
        if record["name"] == "Meenakshi Temple Discovery Point":
            record["image"] = TEMPLE_PHOTOS["Meenakshi Temple"]["image"]
        exists = WorldPlace.query.filter_by(
            name=record["name"],
            city=record["city"],
            country=record["country"],
        ).first()
        if not exists:
            db.session.add(WorldPlace(**record))
        elif record["name"] == "Meenakshi Temple Discovery Point":
            exists.image = record["image"]


if __name__ == "__main__":
    from yatrago import create_app

    create_app()
    print("YatraGo database and demo schedules are ready.")
