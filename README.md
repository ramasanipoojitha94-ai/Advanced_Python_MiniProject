# YatraGo — Indian Travel Booking Platform

YatraGo is a responsive Indian travel platform for comparing sample transport options, reserving demonstration journeys and stays, and exploring Indian destinations and regional food. It is a college-project demonstration: schedules, fares, availability, properties, ratings, and recommendations are sample data; the application does not process payments or issue real tickets.

## Features

- Secure registration and login with Werkzeug password hashing, Flask-Login, and CSRF-protected forms.
- Search scheduled demo buses by route and date, then filter and sort results.
- Reserve seats, save passenger details, view bookings, and cancel eligible future bookings. Seat inventory is shared and prevents duplicate reservations.
- Use the compact homepage search for buses, flights, trains, and cabs. The dedicated transport page retains all ten existing demo categories, including rentals, bikes, metro, ferries, autos, and shared rides.
- Reserve demo train seats, book sample taxi journeys and rental periods, and save metro, ferry, auto, and shared-ride itinerary records. Cancellation releases reserved sample train seats.
- Explore a pannable, zoomable world map with OpenStreetMap tiles and required attribution, curated sample markers across India and six international destinations, map/list views, manual search, distance filters, and opt-in browser location.
- Browse sample stays, restaurants, attractions, destinations, and transport markers; save places to your private account, submit unverified traveller reviews, and open external OpenStreetMap links for locations/directions.
- Create private multi-stop trip plans, add map discoveries, enter notes and dates, compare a planned INR budget to actual expenses, and maintain a packing checklist.
- Search one-way and round-trip sample flights between 12 major Indian airports; filter and sort by fare, stops, and duration, then save a passenger booking with reserved sample seats.
- Explore 40 curated India discovery cards across temples, malls and shopping, hill stations, beaches, heritage, nature, cities, and weekend getaways. Destination cards link to database-backed detail pages and saved favourites; the broader catalogue contains more than 60 seeded destinations.
- Search curated nearby-place markers by city, category, budget, rating, and approximate distance, with map and list views. The catalogue includes sample stays, food, worship, shopping, attractions, cafés, and essential-service categories.
- Plan sample weekend trips from Bengaluru, view editorial seasonal suggestions, browse regional food, and use the homepage INR budget calculator or the private itinerary planner.
- Find sample hotels, guesthouses, hostels, and homestays by city, nightly price, property type, amenities, and illustrative guest rating. Save date-based demo reservations with guest names.
- Unified, account-private My Trips history for all transport bookings and stays, with eligible cancellation and destination-based stay recommendations.
- User dashboard backed by actual database records, plus searchable destination, hotel, and food sample-data pages.
- SQLite database, automatic demo-data initialization, responsive layouts, and automated tests.

## Requirements and setup (Windows)

Use Python 3.10 or newer. From the project directory, run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a private `SECRET_KEY` in `.env` before using the application beyond a local demo. The application creates new tables additively in the configured SQLite database and initializes sample data on startup. Existing user accounts and bus bookings are kept; the SQLite startup migration removes a legacy unique-seat constraint while preserving passenger history, so released bus seats can be booked again.

```powershell
python run.py
```

Open `http://127.0.0.1:5000`. Create an account to access My Trips and make bookings. Do not use real personal or payment information in this demonstration.

To run automated tests:

```powershell
python -m pytest
```

To initialize or refresh demo data in an existing database without removing users or bookings:

```powershell
python -m yatrago.seed
```

## Demonstration inventory and limitations

Demo bus routes, flight schedules, fares, and seat inventory are generated for near-future dates when the database is initialized. Curated train, taxi, rental, metro, ferry, auto, and shared transport schedules and fares are seeded from `yatrago/transport_data.py`; these are fixed demonstration records, not live timetables, inventory, fares, operator affiliation, or availability. The search location suggestions use the application's seeded destination and route catalog. Destination and food records are curated in `yatrago/content.py`; stay properties are seeded into SQLAlchemy tables from that source. All listings and all displayed ratings/budgets are illustrative. No paid APIs or third-party services are required.

The world map spans the globe, but its searchable pins are a small, curated demonstration catalogue in `yatrago/world_data.py` and `yatrago/discovery_data.py`, not a places, hotel, restaurant, or geocoding API. India discovery cards, nearby categories, images, price examples, and seasonal/weekend suggestions are also curated demo content, not verified live listings or recommendations. Search works across seeded city/country/address/category records; arbitrary address lookup and live nearby-business discovery are not configured. Browser location is requested only after the visitor selects **Use my location**, remains in browser memory, and is not saved. Straight-line distances use approximate sample coordinates and are not road/walking directions. The map uses OpenStreetMap's public tile service with attribution; it does not prefetch tiles or provide offline downloads. Follow the [tile usage policy](https://operations.osmfoundation.org/policies/tiles/).

Global local-currency amounts and INR prices are illustrative sample values, not exchange-rate conversions. No weather, foreign-exchange, genuine price-alert, verified emergency-contact, provider availability, or live routing API is configured. External map links may provide directions using OpenStreetMap's own service; YatraGo does not calculate route distances or journey times. User-submitted reviews are labelled unverified. The planner, saved map places, expenses, and packing checklist are account-private. Group sharing and an admin management console are not enabled; no admin role or public user-management endpoint is exposed.

Flight, bus, and train seat reservations are saved to the local database and protect their sample inventory from double booking. Transport bookings are demo itinerary records; only train seats are reserved against shared sample inventory. Rental periods, cabs, metros, ferries, autos, and shared rides do not lock provider inventory. Stay reservations are saved for itinerary demonstration but do not claim or lock live property-room inventory. This project has no payment gateway, real operator/airline data, railway ticket inventory, ticket issuance, real vehicle or hotel reservations, or external integrations. Search fares and journey durations are illustrative.

## Project structure

```text
yatrago/
  __init__.py          Flask application factory and extensions
  auth.py              Registration, login, logout
  content.py           Clearly labeled destination, hotel, and food samples
  discovery_data.py    India discovery collections and nearby sample markers
  models.py            SQLAlchemy models and relationships
  routes.py            Home, bus search, dashboard, trips, and explorer pages
  bookings.py          Booking and cancellation business logic and routes
  air_stays.py         Sample flight search, stays, reservation and history routes
  travel_services.py   Transactional flight and stay booking services
  transport.py         Multi-mode transport search, booking and history routes
  transport_data.py    Curated demo transport options and categories
  transport_services.py Validation and transactional transport booking logic
  world.py             World discovery API, saved places, reviews and planner
  world_data.py        Curated global map-marker sample data
  migrations.py        Safe SQLite migration retaining historical passengers
  seed.py              Idempotent demo schedule and seat initialization
templates/             Shared server-rendered Flask/Jinja page templates
static/css/            Responsive visual design
static/js/             Search, responsive navigation, seat forms and image fallbacks
static/js/world-map.js Leaflet map, sample search, location permission and map/list UI
static/images/         Local graceful-fallback travel illustration
tests/                 Authentication, search, transport, and booking tests
run.py                 Local development entry point
```

## Advanced Python concepts for presentation

- **Object-oriented programming:** SQLAlchemy model classes represent users, destinations, bus and transport options, trips, seats, bookings, and passengers; relationships connect the entities.
- **Modules and reusable functions:** the application factory, route blueprints, seed helper, and bus/flight/stay/transport/world services keep setup, presentation, and business rules separate.
- **Decorators:** `@login_required` protects account-specific routes; Flask route decorators map URLs to view functions.
- **Database operations and constraints:** SQLAlchemy relationships and unique constraints model shared bus, flight, and train seat inventory, private saved places and trip plans, expense logs, reviews, and packing lists. Booking services validate passenger data, update seats, and commit bookings in one transaction; the SQLite migration keeps legacy passenger records while allowing released seats to be resold.
- **Exception handling and validation:** invalid form input receives useful feedback, and database integrity failures are rolled back and surfaced as booking errors.
- **Automated testing:** pytest exercises registration, authentication, multi-mode search, transport validation, booking, cancellation, and seat availability against an isolated SQLite database.

## Limitations

This is an educational demonstration, not a commercial booking service. It has no payment gateway, live operator inventory, real hotel reservations, or external integrations. Cancellation is available only for confirmed bookings before departure.
