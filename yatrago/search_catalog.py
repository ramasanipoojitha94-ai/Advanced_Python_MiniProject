"""Supported demo travel locations and airport aliases.

Airport identity data is factual; all schedules and fares generated for these
locations remain illustrative demonstration data.
"""

INDIAN_TRAVEL_LOCATIONS = (
    "Agartala", "Agra", "Ahmedabad", "Aizawl", "Alappuzha", "Amaravati",
    "Amritsar", "Ayodhya", "Bengaluru", "Bhopal", "Bhubaneswar", "Bilaspur",
    "Chandigarh", "Chennai", "Cherrapunji", "Coimbatore", "Coorg", "Cuttack",
    "Daman", "Darjeeling", "Dehradun", "Delhi", "Dhanbad", "Dharamshala",
    "Dimapur", "Dibrugarh", "Durgapur", "Faridabad", "Gaya", "Gangtok",
    "Gurugram", "Guwahati", "Guntur", "Haridwar", "Hampi", "Hubballi",
    "Imphal", "Indore", "Itanagar", "Jabalpur", "Jaipur", "Jaisalmer",
    "Jalandhar", "Jammu", "Jamshedpur", "Jodhpur", "Kavaratti", "Kanpur",
    "Kochi", "Kohima", "Kolkata", "Kolhapur", "Kota", "Kozhikode", "Kullu",
    "Kurnool", "Leh", "Lucknow", "Ludhiana", "Madurai", "Mangaluru",
    "Margao", "Mathura", "Meerut", "Mumbai", "Munnar", "Muzaffarpur",
    "Mysuru", "Nagpur", "Nashik", "Nellore", "New Delhi", "Noida", "Ooty",
    "Panaji", "Patiala", "Patna", "Pelling", "Port Blair", "Prayagraj",
    "Puducherry", "Pune", "Pushkar", "Raipur", "Rajkot", "Ranchi",
    "Rishikesh", "Rourkela", "Salem", "Shillong", "Shimla", "Shirdi",
    "Siliguri", "Srinagar", "Surat", "Thanjavur", "Thiruvananthapuram",
    "Thrissur", "Tiruchirappalli", "Tirupati", "Tirunelveli", "Tawang",
    "Udaipur", "Ujjain", "Vadodara", "Varanasi", "Vijayawada",
    "Visakhapatnam", "Warangal", "Wayanad",
)


# city: (IATA code, airport name, country)
AIRPORT_DATA = {
    "Agartala": ("IXA", "Maharaja Bir Bikram Airport", "India"),
    "Agra": ("AGR", "Agra Airport", "India"),
    "Ahmedabad": ("AMD", "Sardar Vallabhbhai Patel International Airport", "India"),
    "Aizawl": ("AJL", "Lengpui Airport", "India"),
    "Amritsar": ("ATQ", "Sri Guru Ram Dass Jee International Airport", "India"),
    "Ayodhya": ("AYJ", "Maharishi Valmiki International Airport", "India"),
    "Bengaluru": ("BLR", "Kempegowda International Airport", "India"),
    "Bhopal": ("BHO", "Raja Bhoj Airport", "India"),
    "Bhubaneswar": ("BBI", "Biju Patnaik International Airport", "India"),
    "Chandigarh": ("IXC", "Shaheed Bhagat Singh International Airport", "India"),
    "Chennai": ("MAA", "Chennai International Airport", "India"),
    "Coimbatore": ("CJB", "Coimbatore International Airport", "India"),
    "Dehradun": ("DED", "Jolly Grant Airport", "India"),
    "Delhi": ("DEL", "Indira Gandhi International Airport", "India"),
    "Dibrugarh": ("DIB", "Dibrugarh Airport", "India"),
    "Dimapur": ("DMU", "Dimapur Airport", "India"),
    "Gaya": ("GAY", "Gaya Airport", "India"),
    "Goa": ("GOI", "Dabolim Airport", "India"),
    "Guwahati": ("GAU", "Lokpriya Gopinath Bordoloi International Airport", "India"),
    "Hubballi": ("HBX", "Hubballi Airport", "India"),
    "Hyderabad": ("HYD", "Rajiv Gandhi International Airport", "India"),
    "Imphal": ("IMF", "Bir Tikendrajit International Airport", "India"),
    "Indore": ("IDR", "Devi Ahilya Bai Holkar Airport", "India"),
    "Jaipur": ("JAI", "Jaipur International Airport", "India"),
    "Jammu": ("IXJ", "Jammu Airport", "India"),
    "Jodhpur": ("JDH", "Jodhpur Airport", "India"),
    "Kochi": ("COK", "Cochin International Airport", "India"),
    "Kolkata": ("CCU", "Netaji Subhas Chandra Bose International Airport", "India"),
    "Kozhikode": ("CCJ", "Calicut International Airport", "India"),
    "Leh": ("IXL", "Kushok Bakula Rimpochee Airport", "India"),
    "Lucknow": ("LKO", "Chaudhary Charan Singh International Airport", "India"),
    "Madurai": ("IXM", "Madurai Airport", "India"),
    "Mangaluru": ("IXE", "Mangaluru International Airport", "India"),
    "Mumbai": ("BOM", "Chhatrapati Shivaji Maharaj International Airport", "India"),
    "Mysuru": ("MYQ", "Mysore Airport", "India"),
    "Nagpur": ("NAG", "Dr. Babasaheb Ambedkar International Airport", "India"),
    "Patna": ("PAT", "Jay Prakash Narayan Airport", "India"),
    "Pune": ("PNQ", "Pune Airport", "India"),
    "Raipur": ("RPR", "Swami Vivekananda Airport", "India"),
    "Ranchi": ("IXR", "Birsa Munda Airport", "India"),
    "Shillong": ("SHL", "Shillong Airport", "India"),
    "Srinagar": ("SXR", "Sheikh ul-Alam International Airport", "India"),
    "Surat": ("STV", "Surat International Airport", "India"),
    "Thiruvananthapuram": ("TRV", "Thiruvananthapuram International Airport", "India"),
    "Tiruchirappalli": ("TRZ", "Tiruchirappalli International Airport", "India"),
    "Tirupati": ("TIR", "Tirupati Airport", "India"),
    "Udaipur": ("UDR", "Maharana Pratap Airport", "India"),
    "Varanasi": ("VNS", "Lal Bahadur Shastri International Airport", "India"),
    "Vijayawada": ("VGA", "Vijayawada International Airport", "India"),
    "Visakhapatnam": ("VTZ", "Visakhapatnam International Airport", "India"),
    "Port Blair": ("IXZ", "Veer Savarkar International Airport", "India"),
    "Puducherry": ("PNY", "Puducherry Airport", "India"),
    "Dubai": ("DXB", "Dubai International Airport", "United Arab Emirates"),
    "Singapore": ("SIN", "Singapore Changi Airport", "Singapore"),
    "Bangkok": ("BKK", "Suvarnabhumi Airport", "Thailand"),
    "Colombo": ("CMB", "Bandaranaike International Airport", "Sri Lanka"),
    "London": ("LHR", "Heathrow Airport", "United Kingdom"),
    "Paris": ("CDG", "Charles de Gaulle Airport", "France"),
    "New York": ("JFK", "John F. Kennedy International Airport", "United States"),
    "Tokyo": ("HND", "Haneda Airport", "Japan"),
    "Doha": ("DOH", "Hamad International Airport", "Qatar"),
    "Kuala Lumpur": ("KUL", "Kuala Lumpur International Airport", "Malaysia"),
    "Malé": ("MLE", "Velana International Airport", "Maldives"),
    "Kathmandu": ("KTM", "Tribhuvan International Airport", "Nepal"),
    "Muscat": ("MCT", "Muscat International Airport", "Oman"),
    "Frankfurt": ("FRA", "Frankfurt Airport", "Germany"),
    "Amsterdam": ("AMS", "Amsterdam Airport Schiphol", "Netherlands"),
    "Toronto": ("YYZ", "Toronto Pearson International Airport", "Canada"),
    "Sydney": ("SYD", "Sydney Airport", "Australia"),
    "Hong Kong": ("HKG", "Hong Kong International Airport", "Hong Kong"),
    "Abu Dhabi": ("AUH", "Zayed International Airport", "United Arab Emirates"),
    "San Francisco": ("SFO", "San Francisco International Airport", "United States"),
    "Istanbul": ("IST", "Istanbul Airport", "Türkiye"),
}

AIRPORTS = {
    city: (code, name)
    for city, (code, name, _country) in AIRPORT_DATA.items()
}

_AIRPORT_ALIASES = {
    alias.casefold(): city
    for city, (code, name, _country) in AIRPORT_DATA.items()
    for alias in (city, code, name)
}
_TRAVEL_LOCATION_ALIASES = {
    location.casefold(): location
    for location in set(INDIAN_TRAVEL_LOCATIONS) | set(AIRPORT_DATA)
}
_TRAVEL_LOCATION_ALIASES["new delhi"] = "Delhi"


def canonical_travel_location(value):
    """Resolve known city spelling variants while keeping custom city names usable."""
    cleaned = " ".join(value.split())
    return _TRAVEL_LOCATION_ALIASES.get(cleaned.casefold(), cleaned.title())


def resolve_airport(value):
    """Return a canonical airport city for a city, airport name, or IATA code."""
    return _AIRPORT_ALIASES.get(value.strip().casefold())
