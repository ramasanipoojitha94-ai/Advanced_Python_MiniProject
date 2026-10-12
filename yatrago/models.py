from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from yatrago import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    flight_bookings = db.relationship("FlightBooking", back_populates="user", cascade="all, delete-orphan")
    stay_bookings = db.relationship("StayBooking", back_populates="user", cascade="all, delete-orphan")
    saved_destinations = db.relationship("SavedDestination", back_populates="user", cascade="all, delete-orphan")
    recent_destinations = db.relationship("RecentDestination", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(80), nullable=False)
    destination = db.Column(db.String(80), nullable=False)
    __table_args__ = (db.UniqueConstraint("source", "destination", name="uq_route_endpoints"),)
    trips = db.relationship("Trip", back_populates="route", cascade="all, delete-orphan")


class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operator = db.Column(db.String(100), nullable=False)
    bus_type = db.Column(db.String(60), nullable=False)
    amenities = db.Column(db.String(250), nullable=False, default="")
    trips = db.relationship("Trip", back_populates="bus")


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("route.id"), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey("bus.id"), nullable=False)
    departure_at = db.Column(db.DateTime, nullable=False, index=True)
    arrival_at = db.Column(db.DateTime, nullable=False)
    fare = db.Column(db.Integer, nullable=False)
    route = db.relationship("Route", back_populates="trips")
    bus = db.relationship("Bus", back_populates="trips")
    seats = db.relationship("Seat", back_populates="trip", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="trip")
    __table_args__ = (
        db.UniqueConstraint("route_id", "bus_id", "departure_at", name="uq_trip_schedule"),
        db.CheckConstraint("fare > 0", name="ck_trip_positive_fare"),
    )


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    total_fare = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="bookings")
    trip = db.relationship("Trip", back_populates="bookings")
    passengers = db.relationship("Passenger", back_populates="booking", cascade="all, delete-orphan")
    seats = db.relationship("Seat", back_populates="booking")
    __table_args__ = (db.CheckConstraint("status IN ('confirmed', 'cancelled')", name="ck_booking_status"),)


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    seat_number = db.Column(db.String(5), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=True, index=True)
    trip = db.relationship("Trip", back_populates="seats")
    booking = db.relationship("Booking", back_populates="seats")
    __table_args__ = (db.UniqueConstraint("trip_id", "seat_number", name="uq_trip_seat"),)


class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False, index=True)
    seat_id = db.Column(db.Integer, db.ForeignKey("seat.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    booking = db.relationship("Booking", back_populates="passengers")
    seat = db.relationship("Seat")
    __table_args__ = (
        db.CheckConstraint("age BETWEEN 1 AND 120", name="ck_passenger_age"),
    )


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    region = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    budget_min = db.Column(db.Integer, nullable=False)
    budget_max = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(400), nullable=False)
    attractions = db.Column(db.String(400), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    saved_by = db.relationship("SavedDestination", back_populates="destination", cascade="all, delete-orphan")
    properties = db.relationship("StayProperty", back_populates="destination")
    __table_args__ = (
        db.UniqueConstraint("name", "state", name="uq_destination_name_state"),
        db.CheckConstraint("budget_min > 0 AND budget_max >= budget_min", name="ck_destination_budget"),
    )

    @property
    def budget(self):
        return f"₹{self.budget_min:,}–{self.budget_max:,} / day"


class SavedDestination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="saved_destinations")
    destination = db.relationship("Destination", back_populates="saved_by")
    __table_args__ = (db.UniqueConstraint("user_id", "destination_id", name="uq_user_saved_destination"),)


class RecentDestination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=False, index=True)
    viewed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="recent_destinations")
    destination = db.relationship("Destination")
    __table_args__ = (db.UniqueConstraint("user_id", "destination_id", name="uq_user_recent_destination"),)


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin_city = db.Column(db.String(80), nullable=False, index=True)
    origin_airport = db.Column(db.String(120), nullable=False)
    origin_code = db.Column(db.String(3), nullable=False, index=True)
    destination_city = db.Column(db.String(80), nullable=False, index=True)
    destination_airport = db.Column(db.String(120), nullable=False)
    destination_code = db.Column(db.String(3), nullable=False, index=True)
    airline = db.Column(db.String(100), nullable=False)
    flight_number = db.Column(db.String(12), nullable=False)
    departure_at = db.Column(db.DateTime, nullable=False, index=True)
    arrival_at = db.Column(db.DateTime, nullable=False)
    stops = db.Column(db.Integer, nullable=False, default=0)
    fare_economy = db.Column(db.Integer, nullable=False)
    fare_business = db.Column(db.Integer, nullable=False)
    seats = db.relationship("FlightSeat", back_populates="flight", cascade="all, delete-orphan")
    __table_args__ = (
        db.UniqueConstraint("flight_number", "departure_at", name="uq_flight_schedule"),
        db.CheckConstraint("stops >= 0 AND fare_economy > 0 AND fare_business > 0", name="ck_flight_fares"),
    )


class FlightBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    outbound_flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"), nullable=False)
    return_flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"), nullable=True)
    cabin_class = db.Column(db.String(20), nullable=False)
    total_fare = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="flight_bookings")
    outbound_flight = db.relationship("Flight", foreign_keys=[outbound_flight_id])
    return_flight = db.relationship("Flight", foreign_keys=[return_flight_id])
    passengers = db.relationship("FlightPassenger", back_populates="booking", cascade="all, delete-orphan")
    seats = db.relationship("FlightSeat", back_populates="booking")
    __table_args__ = (
        db.CheckConstraint("cabin_class IN ('Economy', 'Business')", name="ck_flight_booking_cabin"),
        db.CheckConstraint("status IN ('confirmed', 'cancelled')", name="ck_flight_booking_status"),
    )


class FlightSeat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("flight.id"), nullable=False)
    seat_number = db.Column(db.String(5), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("flight_booking.id"), nullable=True, index=True)
    flight = db.relationship("Flight", back_populates="seats")
    booking = db.relationship("FlightBooking", back_populates="seats")
    __table_args__ = (db.UniqueConstraint("flight_id", "seat_number", name="uq_flight_seat"),)


class FlightPassenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("flight_booking.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    outbound_seat_id = db.Column(db.Integer, db.ForeignKey("flight_seat.id"), nullable=False)
    return_seat_id = db.Column(db.Integer, db.ForeignKey("flight_seat.id"), nullable=True)
    booking = db.relationship("FlightBooking", back_populates="passengers")
    outbound_seat = db.relationship("FlightSeat", foreign_keys=[outbound_seat_id])
    return_seat = db.relationship("FlightSeat", foreign_keys=[return_seat_id])
    __table_args__ = (
        db.CheckConstraint("age BETWEEN 1 AND 120", name="ck_flight_passenger_age"),
    )


class StayProperty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    property_type = db.Column(db.String(30), nullable=False)
    price_per_night = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.String(300), nullable=False)
    sample_rating = db.Column(db.Float, nullable=True)
    location_note = db.Column(db.String(160), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    destination = db.relationship("Destination", back_populates="properties")
    bookings = db.relationship("StayBooking", back_populates="property")
    __table_args__ = (
        db.CheckConstraint("price_per_night > 0", name="ck_property_positive_price"),
        db.CheckConstraint("sample_rating IS NULL OR (sample_rating >= 1 AND sample_rating <= 5)", name="ck_property_rating"),
    )

    @property
    def city(self):
        return self.destination.name

    @property
    def rating(self):
        return f"Sample rating · {self.sample_rating:.1f}" if self.sample_rating else "Sample property · no rating"


class StayBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    property_id = db.Column(db.Integer, db.ForeignKey("stay_property.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(40), nullable=False)
    total_fare = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="stay_bookings")
    property = db.relationship("StayProperty", back_populates="bookings")
    guests_info = db.relationship("StayGuest", back_populates="booking", cascade="all, delete-orphan")
    __table_args__ = (
        db.CheckConstraint("check_out > check_in", name="ck_stay_dates"),
        db.CheckConstraint("guests BETWEEN 1 AND 8", name="ck_stay_guest_count"),
        db.CheckConstraint("status IN ('confirmed', 'cancelled')", name="ck_stay_booking_status"),
    )


class StayGuest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("stay_booking.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    booking = db.relationship("StayBooking", back_populates="guests_info")


class TransportOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(24), nullable=False, index=True)
    origin = db.Column(db.String(100), nullable=False, index=True)
    destination = db.Column(db.String(100), nullable=False, index=True)
    provider = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(40), nullable=False)
    service_code = db.Column(db.String(20), nullable=False)
    departure_at = db.Column(db.DateTime, nullable=False, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    stops = db.Column(db.Integer, nullable=False, default=0)
    fare = db.Column(db.Integer, nullable=False)
    price_basis = db.Column(db.String(20), nullable=False, default="per_person")
    comfort = db.Column(db.String(30), nullable=False, default="Standard")
    amenities = db.Column(db.String(250), nullable=False, default="")
    image = db.Column(db.String(500), nullable=False)
    seats = db.relationship("TransportSeat", back_populates="option", cascade="all, delete-orphan")
    bookings = db.relationship(
        "TransportBooking", foreign_keys="TransportBooking.option_id", back_populates="option"
    )
    __table_args__ = (
        db.UniqueConstraint("service_code", "departure_at", name="uq_transport_schedule"),
        db.CheckConstraint(
            "mode IN ('train','cab','car','bike','metro','ferry','auto','shared')",
            name="ck_transport_mode",
        ),
        db.CheckConstraint("duration_minutes > 0 AND fare > 0", name="ck_transport_duration_fare"),
        db.CheckConstraint(
            "price_basis IN ('per_person','per_vehicle','per_day')",
            name="ck_transport_price_basis",
        ),
    )


class TransportBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey("transport_option.id"), nullable=False)
    return_option_id = db.Column(db.Integer, db.ForeignKey("transport_option.id"), nullable=True)
    travel_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    passengers = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    pickup_address = db.Column(db.String(200), nullable=True)
    dropoff_address = db.Column(db.String(200), nullable=True)
    trip_type = db.Column(db.String(24), nullable=False, default="oneway")
    rental_driver = db.Column(db.String(24), nullable=True)
    total_fare = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User")
    option = db.relationship("TransportOption", foreign_keys=[option_id], back_populates="bookings")
    return_option = db.relationship("TransportOption", foreign_keys=[return_option_id])
    seats = db.relationship("TransportSeat", back_populates="booking")
    passenger_details = db.relationship(
        "TransportPassenger", back_populates="booking", cascade="all, delete-orphan"
    )
    __table_args__ = (
        db.CheckConstraint("passengers BETWEEN 1 AND 8", name="ck_transport_booking_passengers"),
        db.CheckConstraint("total_fare > 0", name="ck_transport_booking_total"),
        db.CheckConstraint("status IN ('confirmed','cancelled')", name="ck_transport_booking_status"),
    )


class TransportSeat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey("transport_option.id"), nullable=False)
    seat_number = db.Column(db.String(5), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey("transport_booking.id"), nullable=True, index=True)
    option = db.relationship("TransportOption", back_populates="seats")
    booking = db.relationship("TransportBooking", back_populates="seats")
    __table_args__ = (db.UniqueConstraint("option_id", "seat_number", name="uq_transport_seat"),)


class TransportPassenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("transport_booking.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    booking = db.relationship("TransportBooking", back_populates="passenger_details")
    __table_args__ = (db.CheckConstraint("age BETWEEN 1 AND 120", name="ck_transport_passenger_age"),)


class WorldPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    place_type = db.Column(db.String(24), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="")
    city = db.Column(db.String(80), nullable=False, index=True)
    country = db.Column(db.String(80), nullable=False, index=True)
    address = db.Column(db.String(180), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(400), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    sample_rating = db.Column(db.Float, nullable=True)
    price_inr = db.Column(db.Integer, nullable=True)
    local_price = db.Column(db.Integer, nullable=True)
    local_currency = db.Column(db.String(3), nullable=False, default="INR")
    amenities = db.Column(db.String(250), nullable=False, default="")
    cuisine = db.Column(db.String(80), nullable=False, default="")
    dietary = db.Column(db.String(30), nullable=False, default="")
    opening_hours = db.Column(db.String(100), nullable=False, default="Not verified")
    __table_args__ = (
        db.CheckConstraint(
            "place_type IN ('hotel','restaurant','attraction','transport','destination')",
            name="ck_world_place_type",
        ),
        db.CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_world_place_latitude"),
        db.CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_world_place_longitude"),
        db.CheckConstraint(
            "sample_rating IS NULL OR (sample_rating >= 1 AND sample_rating <= 5)",
            name="ck_world_place_rating",
        ),
        db.CheckConstraint("price_inr IS NULL OR price_inr >= 0", name="ck_world_place_price"),
    )


class SavedWorldPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("world_place.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    place = db.relationship("WorldPlace")
    __table_args__ = (db.UniqueConstraint("user_id", "place_id", name="uq_user_saved_world_place"),)


class TravelPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    budget_inr = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(1000), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    stops = db.relationship("PlanStop", back_populates="plan", cascade="all, delete-orphan", order_by="PlanStop.position")
    expenses = db.relationship("PlanExpense", back_populates="plan", cascade="all, delete-orphan")
    packing_items = db.relationship("PackingItem", back_populates="plan", cascade="all, delete-orphan")
    __table_args__ = (
        db.CheckConstraint("budget_inr IS NULL OR budget_inr >= 0", name="ck_plan_budget"),
        db.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_plan_dates",
        ),
    )


class PlanStop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("travel_plan.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("world_place.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    visit_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.String(500), nullable=False, default="")
    position = db.Column(db.Integer, nullable=False, default=0)
    plan = db.relationship("TravelPlan", back_populates="stops")
    place = db.relationship("WorldPlace")
    __table_args__ = (
        db.CheckConstraint("position >= 0", name="ck_plan_stop_position"),
        db.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="ck_plan_stop_coordinates",
        ),
    )


class PlanExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("travel_plan.id"), nullable=False, index=True)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(160), nullable=False)
    amount_inr = db.Column(db.Integer, nullable=False)
    spent_on = db.Column(db.Date, nullable=False, default=lambda: datetime.now().date())
    plan = db.relationship("TravelPlan", back_populates="expenses")
    __table_args__ = (
        db.CheckConstraint(
            "category IN ('transport','stay','food','activity','other')",
            name="ck_plan_expense_category",
        ),
        db.CheckConstraint("amount_inr >= 0", name="ck_plan_expense_amount"),
    )


class PackingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("travel_plan.id"), nullable=False, index=True)
    label = db.Column(db.String(120), nullable=False)
    is_packed = db.Column(db.Boolean, nullable=False, default=False)
    plan = db.relationship("TravelPlan", back_populates="packing_items")
    __table_args__ = (db.UniqueConstraint("plan_id", "label", name="uq_plan_packing_item"),)


class PlaceReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("world_place.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    place = db.relationship("WorldPlace")
    __table_args__ = (
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_place_review_rating"),
        db.UniqueConstraint("user_id", "place_id", name="uq_user_place_review"),
    )
