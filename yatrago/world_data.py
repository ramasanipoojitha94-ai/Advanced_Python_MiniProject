"""Illustrative global map markers; none represent verified live businesses."""

from yatrago.content import photo
from yatrago.discovery_data import NEARBY_PLACE_SPOTLIGHTS

WORLD_PLACES = [
    ("Bengaluru City Walk", "destination", "City", "Bengaluru", "India", "Central Bengaluru, Karnataka", 12.9716, 77.5946, "A sample city discovery point for Bengaluru's gardens, cafés and creative districts.", "1519501025264-65ba15a82390", None, None, "INR", "Sample destination guide", "", "", "Not verified"),
    ("Garden City Guesthouse", "hotel", "Guesthouse", "Bengaluru", "India", "Indiranagar, Bengaluru, Karnataka", 12.9784, 77.6408, "Illustrative sample guesthouse listing; not a real-time offer.", "1566073771259-6a8506099945", 2100, 2100, "INR", "Wi-Fi · breakfast sample", "", "", "Not verified"),
    ("South Indian Table", "restaurant", "Regional cuisine", "Bengaluru", "India", "Church Street, Bengaluru, Karnataka", 12.9751, 77.6048, "Demo recommendation for South Indian dishes; not a verified restaurant listing.", "1547573854-74d2a71d0826", 450, 450, "INR", "Sample price per person", "South Indian", "Vegetarian options", "Not verified"),
    ("Lalbagh Botanical Garden", "attraction", "Nature", "Bengaluru", "India", "Mavalli, Bengaluru, Karnataka", 12.9507, 77.5848, "Sample map marker for the historic botanical garden.", "1470252649378-9c29740c9fa8", 30, 30, "INR", "Sample entry estimate", "", "", "Not verified"),
    ("Bengaluru City Railway Station", "transport", "Railway station", "Bengaluru", "India", "Majestic, Bengaluru, Karnataka", 12.9767, 77.5713, "Sample transport landmark; confirm station services with the operator.", "1474487548417-781cb71495f3", None, None, "INR", "Transport marker only", "", "", "Not verified"),
    ("Delhi Heritage Walk", "destination", "Heritage", "Delhi", "India", "Old Delhi, New Delhi", 28.6139, 77.2090, "A sample discovery point near central Delhi heritage districts.", "1524492412937-b28074a5d7da", None, None, "INR", "Sample destination guide", "", "", "Not verified"),
    ("Old Delhi Guest House", "hotel", "Budget hotel", "Delhi", "India", "Paharganj, New Delhi", 28.6448, 77.2167, "Illustrative sample stay listing; rates and availability are not live.", "1445019980597-93fa8acb246c", 1700, 1700, "INR", "Sample price per night", "", "", "Not verified"),
    ("Chandni Chowk Food Trail", "restaurant", "Street food", "Delhi", "India", "Chandni Chowk, Old Delhi", 28.6562, 77.2300, "Sample food discovery marker for the Old Delhi market area.", "1555939594-58d7cb561ad1", 350, 350, "INR", "Sample price per person", "North Indian", "Vegetarian and non-vegetarian", "Not verified"),
    ("India Gate", "attraction", "Landmark", "Delhi", "India", "Kartavya Path, New Delhi", 28.6129, 77.2295, "Sample landmark marker; opening details should be confirmed locally.", "1500530855697-b586d89ba3ee", 0, 0, "INR", "Sample free attraction", "", "", "Not verified"),
    ("New Delhi Railway Station", "transport", "Railway station", "Delhi", "India", "Ajmeri Gate, New Delhi", 28.6424, 77.2197, "Sample transport landmark; not a live service or schedule feed.", "1474487548417-781cb71495f3", None, None, "INR", "Transport marker only", "", "", "Not verified"),
    ("Fort Kochi Stay", "hotel", "Homestay", "Kochi", "India", "Fort Kochi, Kerala", 9.9658, 76.2421, "Illustrative homestay sample near Kochi's historic waterfront.", "1542314831-068cd1dbfeeb", 2600, 2600, "INR", "Sample price per night · Wi-Fi", "", "", "Not verified"),
    ("Harbour Spice Kitchen", "restaurant", "Seafood", "Kochi", "India", "Fort Kochi, Kerala", 9.9667, 76.2430, "Sample Kerala dining recommendation; business details are unverified.", "1517248135467-4c7edcad34c4", 700, 700, "INR", "Sample price per person", "Kerala · seafood", "Non-vegetarian", "Not verified"),
    ("Fort Kochi Waterfront", "attraction", "Culture", "Kochi", "India", "Fort Kochi, Kerala", 9.9650, 76.2400, "Sample coastal heritage discovery marker.", "1518837695005-2083093ee35b", 0, 0, "INR", "Sample free attraction", "", "", "Not verified"),
    ("Chhatrapati Shivaji Terminus", "transport", "Railway station", "Mumbai", "India", "Fort, Mumbai, Maharashtra", 18.9402, 72.8356, "Sample heritage station marker; check operator for travel information.", "1474487548417-781cb71495f3", None, None, "INR", "Transport marker only", "", "", "Not verified"),
    ("Marine Drive", "attraction", "Coast", "Mumbai", "India", "Marine Drive, Mumbai, Maharashtra", 18.9440, 72.8235, "Sample public waterfront discovery point.", "1507525428034-b723cf961d3e", 0, 0, "INR", "Sample free attraction", "", "", "Not verified"),
    ("Times Square", "destination", "City", "New York", "United States", "Manhattan, New York, NY", 40.7580, -73.9855, "Illustrative international city marker; details and listings are demo content.", "1480714378408-67cf0d13bc1b", None, None, "USD", "Sample destination guide", "", "", "Not verified"),
    ("Manhattan Sample Stay", "hotel", "Hotel", "New York", "United States", "Midtown Manhattan, New York, NY", 40.7527, -73.9772, "Fictional sample property marker; no real hotel inventory is connected.", "1566073771259-6a8506099945", 14500, 180, "USD", "Demo nightly rate · sample amenities", "", "", "Not verified"),
    ("Central Park", "attraction", "Park", "New York", "United States", "Central Park, New York, NY", 40.7829, -73.9654, "Sample attraction marker for a well-known public park.", "1470252649378-9c29740c9fa8", 0, 0, "USD", "Sample free attraction", "", "", "Not verified"),
    ("Soho Café Sample", "restaurant", "Café", "New York", "United States", "SoHo, Manhattan, New York, NY", 40.7233, -73.9985, "Fictional café recommendation; cuisine, hours and rating are not verified.", "1517248135467-4c7edcad34c4", 2800, 35, "USD", "Demo price per person", "Café", "Vegetarian options", "Not verified"),
    ("King's Cross Station", "transport", "Railway station", "London", "United Kingdom", "Euston Road, London", 51.5308, -0.1238, "Sample transport marker; check the operator for current service information.", "1474487548417-781cb71495f3", None, None, "GBP", "Transport marker only", "", "", "Not verified"),
    ("Eiffel Tower District", "attraction", "Landmark", "Paris", "France", "Champ de Mars, Paris", 48.8584, 2.2945, "Sample attraction map marker; no tickets or opening details are offered.", "1500530855697-b586d89ba3ee", 0, 0, "EUR", "Sample location only", "", "", "Not verified"),
    ("Shinjuku Sample Stay", "hotel", "Hostel", "Tokyo", "Japan", "Shinjuku, Tokyo", 35.6938, 139.7034, "Fictional demo hostel marker for map and itinerary demonstrations.", "1445019980597-93fa8acb246c", 4800, 5200, "JPY", "Illustrative nightly price", "", "", "Not verified"),
    ("Tokyo Station", "transport", "Railway station", "Tokyo", "Japan", "Marunouchi, Chiyoda City, Tokyo", 35.6812, 139.7671, "Sample transport landmark; no timetable or ticket inventory is connected.", "1474487548417-781cb71495f3", None, None, "JPY", "Transport marker only", "", "", "Not verified"),
    ("Gardens by the Bay", "attraction", "Nature", "Singapore", "Singapore", "Marina Gardens Drive, Singapore", 1.2816, 103.8636, "Sample attraction marker for itinerary planning.", "1500530855697-b586d89ba3ee", 0, 0, "SGD", "Sample location only", "", "", "Not verified"),
    ("Sydney Harbour", "destination", "Coast", "Sydney", "Australia", "Circular Quay, Sydney NSW", -33.8568, 151.2153, "Illustrative global destination marker; all recommendations are demonstration data.", "1507525428034-b723cf961d3e", None, None, "AUD", "Sample destination guide", "", "", "Not verified"),
    ("Dubai Creek Sample Ride", "transport", "Ferry terminal", "Dubai", "United Arab Emirates", "Dubai Creek, Dubai", 25.2631, 55.2972, "Sample water-transport location only; confirm services with local operators.", "1518837695005-2083093ee35b", None, None, "AED", "Transport marker only", "", "", "Not verified"),
]


def world_place_records():
    records = [
        {
            "name": row[0],
            "place_type": row[1],
            "category": row[2],
            "city": row[3],
            "country": row[4],
            "address": row[5],
            "latitude": row[6],
            "longitude": row[7],
            "description": row[8],
            "image": photo(row[9]),
            "sample_rating": None,
            "price_inr": row[10],
            "local_price": row[11],
            "local_currency": row[12],
            "amenities": row[13],
            "cuisine": row[14],
            "dietary": row[15],
            "opening_hours": row[16],
        }
        for row in WORLD_PLACES
    ]
    return records + NEARBY_PLACE_SPOTLIGHTS
