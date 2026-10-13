"""Search data provider seam for demo and future live transport providers."""

from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from hashlib import sha1
from math import asin, cos, radians, sin, sqrt

from yatrago import db
from yatrago.models import (
    Bus,
    Flight,
    FlightSeat,
    Route,
    Seat,
    Trip,
    TransportOption,
    TransportSeat,
)
from yatrago.search_catalog import AIRPORT_DATA
from yatrago.search_catalog import INDIAN_TRAVEL_LOCATIONS


_CITY_COORDINATES = {
    "Agartala": (23.8315, 91.2868), "Agra": (27.1767, 78.0081),
    "Ahmedabad": (23.0225, 72.5714), "Aizawl": (23.7271, 92.7176),
    "Amritsar": (31.6340, 74.8723), "Bengaluru": (12.9716, 77.5946),
    "Bhopal": (23.2599, 77.4126), "Bhubaneswar": (20.2961, 85.8245),
    "Chandigarh": (30.7333, 76.7794), "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558), "Dehradun": (30.3165, 78.0322),
    "Delhi": (28.6139, 77.2090), "Dibrugarh": (27.4728, 94.9120),
    "Dimapur": (25.8629, 93.7538), "Gaya": (24.7914, 84.9994),
    "Goa": (15.2993, 74.1240), "Guwahati": (26.1445, 91.7362),
    "Hubballi": (15.3647, 75.1240), "Hyderabad": (17.3850, 78.4867),
    "Imphal": (24.8170, 93.9368), "Indore": (22.7196, 75.8577),
    "Jaipur": (26.9124, 75.7873), "Jammu": (32.7266, 74.8570),
    "Jodhpur": (26.2389, 73.0243), "Kochi": (9.9312, 76.2673),
    "Kolkata": (22.5726, 88.3639), "Kozhikode": (11.2588, 75.7804),
    "Leh": (34.1526, 77.5771), "Lucknow": (26.8467, 80.9462),
    "Madurai": (9.9252, 78.1198), "Mangaluru": (12.9141, 74.8560),
    "Mumbai": (19.0760, 72.8777), "Mysuru": (12.2958, 76.6394),
    "Nagpur": (21.1458, 79.0882), "New York": (40.7128, -74.0060),
    "Patna": (25.5941, 85.1376), "Port Blair": (11.6234, 92.7265),
    "Puducherry": (11.9416, 79.8083), "Pune": (18.5204, 73.8567),
    "Raipur": (21.2514, 81.6296), "Ranchi": (23.3441, 85.3096),
    "Shillong": (25.5788, 91.8933), "Singapore": (1.3521, 103.8198),
    "Srinagar": (34.0837, 74.7973), "Surat": (21.1702, 72.8311),
    "Thiruvananthapuram": (8.5241, 76.9366),
    "Tiruchirappalli": (10.7905, 78.7047), "Tirupati": (13.6288, 79.4192),
    "Udaipur": (24.5854, 73.7125), "Varanasi": (25.3176, 82.9739),
    "Vijayawada": (16.5062, 80.6480), "Visakhapatnam": (17.6868, 83.2185),
    "Dubai": (25.2048, 55.2708), "Bangkok": (13.7563, 100.5018),
    "Colombo": (6.9271, 79.8612), "London": (51.5072, -0.1276),
    "Paris": (48.8566, 2.3522), "Tokyo": (35.6762, 139.6503),
    "Doha": (25.2854, 51.5310), "Kuala Lumpur": (3.1390, 101.6869),
    "Malé": (4.1755, 73.5093), "Kathmandu": (27.7172, 85.3240),
    "Muscat": (23.5880, 58.3829), "Frankfurt": (50.1109, 8.6821),
    "Amsterdam": (52.3676, 4.9041), "Toronto": (43.6532, -79.3832),
    "Sydney": (-33.8688, 151.2093), "Hong Kong": (22.3193, 114.1694),
    "Abu Dhabi": (24.4539, 54.3773), "San Francisco": (37.7749, -122.4194),
    "Istanbul": (41.0082, 28.9784),
}

_BUS_TYPES = (
    ("AC Sleeper", "Wi-Fi,Charging point,Blanket"),
    ("Volvo Multi-Axle", "Wi-Fi,Charging point,Water bottle"),
    ("AC Seater", "Charging point,Water bottle"),
    ("Non-AC Sleeper", "Blanket"),
)
_STATE_ROADWAYS = {
    "Andhra Pradesh": "APSRTC",
    "Telangana": "TGSRTC",
    "Karnataka": "KSRTC",
    "Kerala": "Kerala RTC",
    "Tamil Nadu": "TNSTC",
    "Maharashtra": "MSRTC",
    "Rajasthan": "RSRTC",
    "Uttar Pradesh": "UPSRTC",
    "Gujarat": "GSRTC",
    "West Bengal": "SBSTC",
    "Odisha": "OSRTC",
    "Assam": "ASTC",
    "Madhya Pradesh": "MPSRTC",
    "Bihar": "BSRTC",
    "Punjab": "PUNBUS",
    "Himachal Pradesh": "HRTC",
    "Uttarakhand": "UTC",
    "Goa": "Kadamba Transport Corporation",
}
_CITY_STATES = {
    "Agartala": "Tripura", "Agra": "Uttar Pradesh", "Ahmedabad": "Gujarat",
    "Aizawl": "Mizoram", "Amritsar": "Punjab", "Bengaluru": "Karnataka",
    "Bhopal": "Madhya Pradesh", "Bhubaneswar": "Odisha", "Chandigarh": "Punjab",
    "Chennai": "Tamil Nadu", "Coimbatore": "Tamil Nadu", "Dehradun": "Uttarakhand",
    "Delhi": "Delhi", "Dibrugarh": "Assam", "Dimapur": "Nagaland", "Gaya": "Bihar",
    "Goa": "Goa", "Guwahati": "Assam", "Hubballi": "Karnataka",
    "Hyderabad": "Telangana", "Imphal": "Manipur", "Indore": "Madhya Pradesh",
    "Jaipur": "Rajasthan", "Jammu": "Jammu and Kashmir", "Jodhpur": "Rajasthan",
    "Kochi": "Kerala", "Kolkata": "West Bengal", "Kozhikode": "Kerala",
    "Leh": "Ladakh", "Lucknow": "Uttar Pradesh", "Madurai": "Tamil Nadu",
    "Mangaluru": "Karnataka", "Mumbai": "Maharashtra", "Mysuru": "Karnataka",
    "Nagpur": "Maharashtra", "Patna": "Bihar", "Port Blair": "Andaman and Nicobar Islands",
    "Puducherry": "Puducherry", "Pune": "Maharashtra", "Raipur": "Chhattisgarh",
    "Ranchi": "Jharkhand", "Shillong": "Meghalaya", "Srinagar": "Jammu and Kashmir",
    "Surat": "Gujarat", "Thiruvananthapuram": "Kerala",
    "Tiruchirappalli": "Tamil Nadu", "Tirupati": "Andhra Pradesh",
    "Udaipur": "Rajasthan", "Varanasi": "Uttar Pradesh",
    "Vijayawada": "Andhra Pradesh", "Visakhapatnam": "Andhra Pradesh",
    "Alappuzha": "Kerala", "Amaravati": "Andhra Pradesh", "Ayodhya": "Uttar Pradesh",
    "Bilaspur": "Chhattisgarh", "Cherrapunji": "Meghalaya", "Coorg": "Karnataka",
    "Cuttack": "Odisha", "Daman": "Dadra and Nagar Haveli and Daman and Diu",
    "Darjeeling": "West Bengal", "Dhanbad": "Jharkhand", "Dharamshala": "Himachal Pradesh",
    "Durgapur": "West Bengal", "Faridabad": "Haryana", "Gangtok": "Sikkim",
    "Guntur": "Andhra Pradesh", "Gurugram": "Haryana", "Haridwar": "Uttarakhand",
    "Hampi": "Karnataka", "Itanagar": "Arunachal Pradesh", "Jabalpur": "Madhya Pradesh",
    "Jaisalmer": "Rajasthan", "Jalandhar": "Punjab", "Jamshedpur": "Jharkhand",
    "Kavaratti": "Lakshadweep", "Kanpur": "Uttar Pradesh", "Kohima": "Nagaland",
    "Kolhapur": "Maharashtra", "Kota": "Rajasthan", "Kullu": "Himachal Pradesh",
    "Kurnool": "Andhra Pradesh", "Ludhiana": "Punjab", "Margao": "Goa",
    "Mathura": "Uttar Pradesh", "Meerut": "Uttar Pradesh", "Munnar": "Kerala",
    "Muzaffarpur": "Bihar", "Nashik": "Maharashtra", "Nellore": "Andhra Pradesh",
    "New Delhi": "Delhi", "Noida": "Uttar Pradesh", "Ooty": "Tamil Nadu",
    "Panaji": "Goa", "Patiala": "Punjab", "Pelling": "Sikkim", "Prayagraj": "Uttar Pradesh",
    "Pushkar": "Rajasthan", "Rajkot": "Gujarat", "Rishikesh": "Uttarakhand",
    "Rourkela": "Odisha", "Salem": "Tamil Nadu", "Shillong": "Meghalaya",
    "Shimla": "Himachal Pradesh", "Shirdi": "Maharashtra", "Siliguri": "West Bengal",
    "Thanjavur": "Tamil Nadu", "Thrissur": "Kerala", "Tirunelveli": "Tamil Nadu",
    "Tawang": "Arunachal Pradesh", "Ujjain": "Madhya Pradesh", "Vadodara": "Gujarat",
    "Warangal": "Telangana", "Wayanad": "Kerala",
}
_PRIVATE_BUS_TYPES = (
    ("AC Sleeper", "Wi-Fi,Charging point,Blanket"),
    ("Volvo Multi-Axle", "Wi-Fi,Charging point,Water bottle"),
    ("AC Seater", "Charging point,Water bottle"),
    ("Non-AC Sleeper", "Blanket"),
)
_TRAIN_SERVICE_TYPES = (
    ("Express", "Standard", 0.72),
    ("Superfast", "Comfort", 1.05),
    ("Intercity", "Standard", 0.88),
    ("Day service", "Standard", 0.65),
    ("Overnight service", "Sleeper", 1.2),
    ("Premium demo service", "Premium", 1.65),
)
_TRAIN_IMAGE = (
    "https://images.unsplash.com/photo-1474487548417-781cb71495f3"
    "?auto=format&fit=crop&w=1000&q=85"
)


def _distance_km(origin, destination):
    origin_point = _CITY_COORDINATES.get(origin)
    destination_point = _CITY_COORDINATES.get(destination)
    if not origin_point or not destination_point:
        return 420
    lat1, lon1 = map(radians, origin_point)
    lat2, lon2 = map(radians, destination_point)
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return max(45, round(6371 * 2 * asin(sqrt(value)) * 1.18))


def _remaining_departures(day, hours):
    now = datetime.now()
    if day > date.today():
        return [datetime.combine(day, time(hour)) for hour in hours]
    times = [
        datetime.combine(day, time(hour))
        for hour in hours
        if datetime.combine(day, time(hour)) > now
    ]
    if times:
        return times
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return [
        next_hour + timedelta(hours=offset)
        for offset in (0, 3)
        if (next_hour + timedelta(hours=offset)).date() == day
    ]


class TransportSearchProvider(ABC):
    """Interface for providers returning DB-backed options accepted by booking flows."""

    is_live = False

    @abstractmethod
    def bus_departures(self, origin, destination, day):
        raise NotImplementedError

    @abstractmethod
    def flight_departures(self, origin, destination, day):
        raise NotImplementedError

    @abstractmethod
    def train_departures(self, origin, destination, day):
        raise NotImplementedError


class DemoTransportSearchProvider(TransportSearchProvider):
    """Create clearly illustrative, date-specific rows for the local booking demo."""

    def bus_departures(self, origin, destination, day):
        route = Route.query.filter(
            db.func.lower(Route.source) == origin.casefold(),
            db.func.lower(Route.destination) == destination.casefold(),
        ).first()
        if route is None:
            route = Route(source=origin, destination=destination)
            db.session.add(route)
            db.session.flush()

        departures = Trip.query.filter(
            Trip.route_id == route.id,
            db.func.date(Trip.departure_at) == day.isoformat(),
            Trip.departure_at > datetime.now(),
        ).order_by(Trip.departure_at).all()
        roadways = []
        for city in (origin, destination):
            state = _CITY_STATES.get(city)
            corporation = _STATE_ROADWAYS.get(state)
            if corporation and corporation not in roadways:
                roadways.append(corporation)
        if not roadways:
            roadways = ["Public roadways demo"]
        operator_specs = [
            (f"{name} (DEMO DATA)", _BUS_TYPES[index % len(_BUS_TYPES)])
            for index, name in enumerate(roadways)
        ]
        operator_specs.extend(
            (
                f"Private bus operator {chr(65 + index)} (DEMO DATA)",
                _PRIVATE_BUS_TYPES[index % len(_PRIVATE_BUS_TYPES)],
            )
            for index in range(8 - len(operator_specs))
        )
        scheduled_operators = {
            trip.bus.operator for trip in departures
        }
        if all(operator in scheduled_operators for operator, _bus in operator_specs):
            return departures

        distance = _distance_km(origin, destination)
        duration_minutes = max(90, round(distance / 55 * 60 / 15) * 15 + 30)
        schedule_hours = tuple(range(5, 23, 2))
        for index, departure in enumerate(_remaining_departures(day, schedule_hours)):
            if index >= len(operator_specs):
                break
            operator, (bus_type, amenities) = operator_specs[index]
            bus = Bus.query.filter_by(operator=operator, bus_type=bus_type).first()
            if bus is None:
                bus = Bus(operator=operator, bus_type=bus_type, amenities=amenities)
                db.session.add(bus)
                db.session.flush()
            if Trip.query.filter_by(
                route_id=route.id, bus_id=bus.id, departure_at=departure
            ).first():
                continue
            base_fare = max(350, round(distance * 1.35 / 50) * 50)
            trip = Trip(
                route_id=route.id,
                bus_id=bus.id,
                departure_at=departure,
                arrival_at=departure + timedelta(minutes=duration_minutes),
                fare=base_fare + index * 150,
            )
            db.session.add(trip)
            db.session.flush()
            db.session.add_all(
                Seat(trip_id=trip.id, seat_number=f"{row}{column}")
                for row in range(1, 7)
                for column in "ABCD"
            )
            departures.append(trip)
        db.session.commit()
        return Trip.query.filter(
            Trip.route_id == route.id,
            db.func.date(Trip.departure_at) == day.isoformat(),
            Trip.departure_at > datetime.now(),
        ).order_by(Trip.departure_at).all()

    def flight_departures(self, origin, destination, day):
        origin_code, origin_airport, _origin_country = AIRPORT_DATA[origin]
        destination_code, destination_airport, _destination_country = AIRPORT_DATA[destination]
        departures = Flight.query.filter(
            Flight.origin_city == origin,
            Flight.destination_city == destination,
            db.func.date(Flight.departure_at) == day.isoformat(),
            Flight.departure_at > datetime.now(),
        ).order_by(Flight.departure_at).all()
        schedule_hours = (6, 9, 12, 15, 18, 21)
        if len(departures) >= len(schedule_hours):
            return departures

        distance = _distance_km(origin, destination)
        duration_minutes = max(75, round((distance / 720 * 60 + 65) / 15) * 15)
        for index, departure in enumerate(_remaining_departures(day, schedule_hours)):
            number = f"D{origin_code}{destination_code}{index + 1}"
            if Flight.query.filter_by(
                flight_number=number, departure_at=departure
            ).first():
                continue
            flight = Flight(
                origin_city=origin,
                origin_airport=origin_airport,
                origin_code=origin_code,
                destination_city=destination,
                destination_airport=destination_airport,
                destination_code=destination_code,
                airline="Demo air service (not a real airline)",
                flight_number=number,
                departure_at=departure,
                arrival_at=departure + timedelta(minutes=duration_minutes),
                stops=1 if distance > 3000 else 0,
                fare_economy=max(2500, round((2200 + distance * 0.42 + index * 350) / 100) * 100),
                fare_business=max(8500, round((8200 + distance * 1.1 + index * 900) / 100) * 100),
            )
            db.session.add(flight)
            db.session.flush()
            db.session.add_all(
                FlightSeat(flight_id=flight.id, seat_number=f"{row}{column}")
                for row in range(1, 7)
                for column in "ABCD"
            )
            departures.append(flight)
        db.session.commit()
        return Flight.query.filter(
            Flight.origin_city == origin,
            Flight.destination_city == destination,
            db.func.date(Flight.departure_at) == day.isoformat(),
            Flight.departure_at > datetime.now(),
        ).order_by(Flight.departure_at).all()

    def train_departures(self, origin, destination, day):
        indian_cities = {city.casefold() for city in INDIAN_TRAVEL_LOCATIONS}
        if origin.casefold() not in indian_cities or destination.casefold() not in indian_cities:
            return []
        current = TransportOption.query.filter(
            TransportOption.mode == "train",
            TransportOption.origin == origin,
            TransportOption.destination == destination,
            db.func.date(TransportOption.departure_at) == day.isoformat(),
            TransportOption.departure_at > datetime.now(),
        ).order_by(TransportOption.departure_at).all()
        if len(current) >= len(_TRAIN_SERVICE_TYPES):
            return current

        distance = _distance_km(origin, destination)
        route_token = sha1(f"{origin.casefold()}|{destination.casefold()}".encode()).hexdigest()[:8].upper()
        departure_times = _remaining_departures(day, (5, 8, 11, 14, 17, 20))
        for index, departure in enumerate(departure_times):
            if index >= len(_TRAIN_SERVICE_TYPES):
                break
            service_type, comfort, fare_multiplier = _TRAIN_SERVICE_TYPES[index]
            service_code = f"DT{route_token}{index + 1}"
            if TransportOption.query.filter_by(
                service_code=service_code, departure_at=departure
            ).first():
                continue
            speed = 62 if service_type == "Express" else 78
            duration = max(75, round((distance / speed * 60 + 35) / 15) * 15)
            fare = max(90, round(distance * fare_multiplier * 0.7 / 10) * 10)
            option = TransportOption(
                mode="train",
                origin=origin,
                destination=destination,
                provider="Demo rail service (DEMO DATA)",
                service_type=service_type,
                service_code=service_code,
                departure_at=departure,
                duration_minutes=duration,
                stops=1 if distance > 300 else 0,
                fare=fare,
                price_basis="per_person",
                comfort=comfort,
                amenities="Illustrative route and fare · sample seat inventory",
                image=_TRAIN_IMAGE,
            )
            db.session.add(option)
            db.session.flush()
            db.session.add_all(
                TransportSeat(option_id=option.id, seat_number=f"{row}{column}")
                for row in range(1, 9)
                for column in "ABCD"
            )
        db.session.commit()
        return TransportOption.query.filter(
            TransportOption.mode == "train",
            TransportOption.origin == origin,
            TransportOption.destination == destination,
            db.func.date(TransportOption.departure_at) == day.isoformat(),
            TransportOption.departure_at > datetime.now(),
        ).order_by(TransportOption.departure_at).all()


demo_transport_provider = DemoTransportSearchProvider()
