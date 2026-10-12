"""Curated sample destination and food data; prices and recommendations are illustrative."""

IMAGE_IDS = [
    "1599661046827-dacff0c0f09a", "1593693411515-c20261bcad6e", "1600100397608-f0109f9d5bf2",
    "1512343879784-a960bf40e7f2", "1561361513-2d000a50f0dc", "1597074866923-dc0589150358",
    "1500530855697-b586d89ba3ee", "1470770841072-f978cf4d019e", "1518837695005-2083093ee35b",
    "1464822759023-fed622ff2c3b", "1501785888041-af3ef285b470", "1470252649378-9c29740c9fa8",
    "1500534623283-312aade485b7", "1516026672322-bc52d61a55d5", "1490750967868-88aa4486c946",
    "1518005020951-eccb494ad742", "1500534314209-a25ddb2bd429", "1500530855697-b586d89ba3ee",
    "1500534623283-312aade485b7", "1470770841072-f978cf4d019e", "1464822759023-fed622ff2c3b",
    "1501785888041-af3ef285b470", "1518837695005-2083093ee35b", "1470252649378-9c29740c9fa8",
    "1516026672322-bc52d61a55d5", "1490750967868-88aa4486c946", "1518005020951-eccb494ad742",
    "1500534314209-a25ddb2bd429", "1530789253388-582c481c54b0", "1524492412937-b28074a5d7da",
    "1518509562904-e7ef99cdcc86", "1500534623283-312aade485b7", "1464822759023-fed622ff2c3b",
    "1501785888041-af3ef285b470", "1518837695005-2083093ee35b", "1470252649378-9c29740c9fa8",
    "1516026672322-bc52d61a55d5", "1490750967868-88aa4486c946", "1518005020951-eccb494ad742",
    "1500534314209-a25ddb2bd429", "1530789253388-582c481c54b0", "1524492412937-b28074a5d7da",
    "1518509562904-e7ef99cdcc86", "1500534623283-312aade485b7", "1464822759023-fed622ff2c3b",
    "1501785888041-af3ef285b470", "1518837695005-2083093ee35b", "1470252649378-9c29740c9fa8",
    "1516026672322-bc52d61a55d5", "1490750967868-88aa4486c946", "1518005020951-eccb494ad742",
    "1500534314209-a25ddb2bd429", "1530789253388-582c481c54b0", "1524492412937-b28074a5d7da",
    "1518509562904-e7ef99cdcc86",
    "1441974231531-c6227db76b6e", "1472396961693-142e6e269027",
    "1507525428034-b723cf961d3e", "1493246507139-91e8fad9978e",
    "1469474968028-56623f02e42e", "1519681393784-d120267933ba",
    "1488646953014-85cb44e25828", "1469854523086-cc02fe5d8800",
    "1511497584788-876760111969", "1473448912268-2022ce9509d8",
    "1426604966848-d7adac402bff", "1544735716-392fe2489ffa",
    "1540541338287-41700207dee6", "1490730141103-6cac27aaab94",
    "1465188162913-8fb5709d6d57", "1519608487953-e999c86e7455",
    "1433086966358-54859d0ed716", "1500534314209-a25ddb2bd429",
    "1470071459604-3b5ec3a7fe05", "1482938289607-e9573fc25ebb",
    "1504893524553-b855bce32c67", "1454496522488-7a8e488e8606",
    "1528127269322-539801943592",
]
IMAGE_IDS = list(dict.fromkeys(IMAGE_IDS))


def photo(image_id):
    return f"https://images.unsplash.com/photo-{image_id}?auto=format&fit=crop&w=1000&q=85"


_DESTINATION_ROWS = [
    ("Bengaluru", "Karnataka", "South", "City", 2200, 5000, "October–February", "A leafy, creative city with garden escapes, café culture, and a lively evening scene.", "Lalbagh · Cubbon Park · Bengaluru Palace"),
    ("Mysuru", "Karnataka", "South", "Heritage", 1800, 3800, "October–February", "A graceful heritage city known for its palace, yoga traditions, and fragrant markets.", "Mysore Palace · Chamundi Hills · Devaraja Market"),
    ("Coorg", "Karnataka", "South", "Nature", 2500, 5500, "October–March", "Coffee country of misty hills, forest trails, waterfalls, and welcoming homestays.", "Abbey Falls · Raja’s Seat · coffee estates"),
    ("Ooty", "Tamil Nadu", "South", "Hill station", 2200, 5000, "October–June", "A Nilgiri hill town of cool mornings, tea gardens, and winding mountain railways.", "Nilgiri Mountain Railway · Doddabetta · Botanical Garden"),
    ("Chennai", "Tamil Nadu", "South", "Coast", 2200, 5000, "November–February", "A coastal capital where classical arts, historic neighbourhoods, and a long city beach meet.", "Marina Beach · Fort St. George · Kapaleeshwarar Temple"),
    ("Hyderabad", "Telangana", "South", "Heritage", 2000, 4500, "October–February", "A city of Deccan history, monumental architecture, and much-loved local food.", "Charminar · Golconda Fort · Chowmahalla Palace"),
    ("Kochi", "Kerala", "South", "Culture", 2200, 4800, "October–March", "An easygoing harbour city shaped by spice-trade history, galleries, and island ferries.", "Fort Kochi · Mattancherry Palace · Chinese fishing nets"),
    ("Munnar", "Kerala", "South", "Hill station", 2400, 5500, "September–March", "A cool highland retreat of tea-covered slopes, quiet trails, and cloud-wrapped valleys.", "Tea Museum · Eravikulam · Top Station"),
    ("Wayanad", "Kerala", "South", "Nature", 2300, 5200, "October–May", "A green mountain district of wildlife, spice farms, waterfalls, and ancient caves.", "Edakkal Caves · Soochipara Falls · Banasura Sagar"),
    ("Hampi", "Karnataka", "South", "Heritage", 1500, 3200, "October–February", "A remarkable landscape of Vijayanagara ruins, giant boulders, and riverside paths.", "Virupaksha Temple · Vittala Temple · Hampi Bazaar"),
    ("Tirupati", "Andhra Pradesh", "South", "Spiritual", 1800, 4000, "September–March", "A celebrated pilgrimage town set against the forested Tirumala hills.", "Sri Venkateswara Temple · Sri Kapileswara Swamy Temple"),
    ("Visakhapatnam", "Andhra Pradesh", "South", "Coast", 2000, 4500, "October–March", "A relaxed Bay of Bengal city with beaches, viewpoints, and green Eastern Ghats nearby.", "RK Beach · Kailasagiri · Submarine Museum"),
    ("Delhi", "Delhi", "North", "Heritage", 2400, 5500, "October–March", "A layered capital where grand Mughal landmarks stand beside lively modern districts.", "Humayun’s Tomb · Red Fort · Qutub Minar"),
    ("Jaipur", "Rajasthan", "North", "Heritage", 2500, 5500, "October–March", "Rose-coloured palaces, energetic bazaars, and sweeping views across the Aravallis.", "Amber Fort · Hawa Mahal · City Palace"),
    ("Udaipur", "Rajasthan", "West", "Heritage", 2800, 6500, "October–March", "A romantic lake city of hilltop palaces, old lanes, and sunset boat rides.", "City Palace · Lake Pichola · Sajjangarh"),
    ("Agra", "Uttar Pradesh", "North", "Heritage", 2000, 4500, "October–March", "A historic Mughal city home to one of the world’s most celebrated monuments.", "Taj Mahal · Agra Fort · Mehtab Bagh"),
    ("Varanasi", "Uttar Pradesh", "North", "Spiritual", 1600, 3800, "October–March", "Ancient riverfront ghats, music, narrow lanes, and living traditions along the Ganges.", "Dashashwamedh Ghat · Sarnath · Assi Ghat"),
    ("Lucknow", "Uttar Pradesh", "North", "Food", 1800, 4200, "November–February", "A gracious city of Awadhi cuisine, distinctive architecture, and old-world hospitality.", "Bara Imambara · Rumi Darwaza · Hazratganj"),
    ("Amritsar", "Punjab", "North", "Spiritual", 1800, 4200, "October–March", "A warm, energetic city centred around the luminous Golden Temple and storied food lanes.", "Golden Temple · Jallianwala Bagh · Partition Museum"),
    ("Shimla", "Himachal Pradesh", "North", "Hill station", 2800, 6200, "March–June · December–January", "A classic mountain escape with colonial-era streets and far-reaching Himalayan views.", "The Ridge · Mall Road · Jakhoo Temple"),
    ("Manali", "Himachal Pradesh", "North", "Adventure", 3000, 7000, "March–June · October", "An alpine base for riverside days, mountain trails, and high-pass adventures.", "Solang Valley · Old Manali · Hadimba Temple"),
    ("Dehradun", "Uttarakhand", "North", "Nature", 2000, 4500, "March–June · September–November", "A relaxed valley city and easy starting point for the Garhwal mountains.", "Robber’s Cave · Forest Research Institute · Sahastradhara"),
    ("Rishikesh", "Uttarakhand", "North", "Adventure", 1800, 4500, "September–April", "A riverside town for quiet ashrams, forested walks, and gentle adventure.", "Lakshman Jhula area · Triveni Ghat · river rafting"),
    ("Mumbai", "Maharashtra", "West", "City", 2800, 6500, "November–February", "India’s restless coastal metropolis pairs historic landmarks with contemporary culture.", "Gateway of India · Marine Drive · Elephanta Caves"),
    ("Pune", "Maharashtra", "West", "City", 2200, 5000, "October–February", "A lively cultural city with leafy neighbourhoods, historic forts, and a youthful food scene.", "Shaniwar Wada · Aga Khan Palace · Sinhagad"),
    ("Goa", "Goa", "West", "Beach", 2800, 7000, "November–February", "Sunlit shores, leafy villages, and Portuguese-influenced old quarters make space to unwind.", "Fontainhas · Basilica of Bom Jesus · coastal beaches"),
    ("Ahmedabad", "Gujarat", "West", "Heritage", 2000, 4500, "November–February", "A UNESCO-recognised historic centre with intricate stepwells and a thriving design scene.", "Adalaj Stepwell · Sabarmati Ashram · old city pols"),
    ("Surat", "Gujarat", "West", "Food", 1800, 4000, "November–February", "A vibrant riverside city celebrated for textiles, lively markets, and Gujarati snacks.", "Dutch Garden · Dumas Beach · Gopi Talav"),
    ("Nashik", "Maharashtra", "West", "Spiritual", 2000, 4500, "October–March", "A historic Godavari-side city surrounded by vineyards and Sahyadri scenery.", "Trimbakeshwar · Pandavleni Caves · vineyard trails"),
    ("Kolkata", "West Bengal", "East", "Culture", 2000, 4800, "October–February", "A characterful cultural capital of grand architecture, bookshops, art, and sweets.", "Victoria Memorial · Howrah Bridge · Kumartuli"),
    ("Bhubaneswar", "Odisha", "East", "Heritage", 1800, 4200, "November–February", "The temple city is a compelling gateway to Odisha’s coast and classical heritage.", "Lingaraj Temple · Udayagiri Caves · Dhauli"),
    ("Puri", "Odisha", "East", "Beach", 1800, 4500, "November–February", "A welcoming Bay of Bengal pilgrimage and beach town with a long sandy shoreline.", "Jagannath Temple · Puri Beach · Raghurajpur"),
    ("Darjeeling", "West Bengal", "East", "Hill station", 2500, 5600, "March–May · October–November", "Tea gardens, mountain railways, and Himalayan sunrises give this hill town its charm.", "Tiger Hill · Batasia Loop · tea gardens"),
    ("Guwahati", "Assam", "Northeast", "Spiritual", 1900, 4300, "October–April", "A lively Brahmaputra gateway to Assam’s wildlife, river islands, and culture.", "Kamakhya Temple · river cruise · Umananda"),
    ("Shillong", "Meghalaya", "Northeast", "Hill station", 2200, 5000, "October–April", "Pine-covered ridges, local music, and waterfalls create a refreshing hill escape.", "Ward’s Lake · Shillong Peak · Elephant Falls"),
    ("Gangtok", "Sikkim", "Northeast", "Hill station", 2500, 6000, "March–May · October–December", "A mountain capital of monasteries, colourful markets, and far-reaching Kanchenjunga views.", "Rumtek Monastery · MG Marg · Tashi View Point"),
    ("Tawang", "Arunachal Pradesh", "Northeast", "Adventure", 3000, 7000, "April–June · September–October", "A high Himalayan town reached by dramatic passes and known for its serene monastery.", "Tawang Monastery · Sela Pass · Madhuri Lake"),
    ("Bhopal", "Madhya Pradesh", "Central", "Culture", 1800, 4200, "October–March", "A city of tranquil lakes, generous green spaces, and nearby prehistoric art.", "Upper Lake · Sanchi day trip · Bhimbetka"),
    ("Indore", "Madhya Pradesh", "Central", "Food", 1800, 4200, "October–March", "A friendly central-India city with a celebrated night food market and palaces.", "Rajwada · Sarafa Bazaar · Lal Bagh Palace"),
    ("Khajuraho", "Madhya Pradesh", "Central", "Heritage", 2000, 4500, "October–March", "An extraordinary collection of intricately carved medieval temples in a quiet setting.", "Western Group of Temples · Archaeological Museum"),
    ("Jabalpur", "Madhya Pradesh", "Central", "Nature", 1900, 4400, "October–March", "A riverside base for marble cliffs, forest reserves, and dramatic waterfalls.", "Bhedaghat · Dhuandhar Falls · Madan Mahal Fort"),
    ("Raipur", "Chhattisgarh", "Central", "Nature", 1800, 4200, "October–March", "A convenient city base for discovering central India’s forests, crafts, and waterfalls.", "Nandan Van · Mahant Ghasidas Museum · Sirpur day trip"),
]

DESTINATIONS = [
    {
        "name": row[0], "state": row[1], "region": row[2], "category": row[3],
        "budget_min": row[4], "budget_max": row[5], "season": row[6],
        "description": row[7], "attractions": row[8],
        "budget": f"₹{row[4]:,}–{row[5]:,} / day",
        "image": photo(IMAGE_IDS[index]),
    }
    for index, row in enumerate(_DESTINATION_ROWS)
]

_STAY_IMAGES = [
    "1566073771259-6a8506099945", "1445019980597-93fa8acb246c", "1542314831-068cd1dbfeeb",
    "1571896349842-33c89424de2d", "1564501049412-61c2a3083791", "1510798831971-661eb04b3739",
    "1611892440504-42a792e24d32", "1590490360182-c33d57733427", "1578683010236-d716f9a3f461",
    "1564013799919-ab600027ffc6", "1520250497591-112f2f40a3f4", "1566665797739-1674de7a421a",
]
_STAY_CITIES = [
    ("Bengaluru", "Karnataka", "Garden City Guesthouse", "Guesthouse", 1450, "Wi-Fi, breakfast, garden", "Sample rating · 4.4", "Near central Bengaluru"),
    ("Mysuru", "Karnataka", "Palace View Homestay", "Homestay", 1350, "Wi-Fi, breakfast, family rooms", "Sample rating · 4.6", "Mysuru city area"),
    ("Coorg", "Karnataka", "Coffee Leaf Cottage", "Homestay", 2200, "Coffee, garden, parking", "Sample rating · 4.7", "Coorg region"),
    ("Ooty", "Tamil Nadu", "Blue Hills Lodge", "Guesthouse", 1800, "Heating, Wi-Fi, breakfast", "Sample rating · 4.3", "Ooty town area"),
    ("Chennai", "Tamil Nadu", "Marina House Stay", "Budget hotel", 1650, "Wi-Fi, AC, breakfast", "Sample rating · 4.2", "Central Chennai"),
    ("Hyderabad", "Telangana", "Deccan Courtyard Rooms", "Budget hotel", 1750, "Wi-Fi, AC, café", "Sample rating · 4.5", "Hyderabad city area"),
    ("Kochi", "Kerala", "Harbour Lane Hostel", "Hostel", 850, "Wi-Fi, shared kitchen, lounge", "Sample rating · 4.3", "Fort Kochi area"),
    ("Munnar", "Kerala", "Tea Valley Retreat", "Homestay", 2100, "Mountain view, breakfast, garden", "Sample rating · 4.7", "Munnar region"),
    ("Wayanad", "Kerala", "Forest Edge Rooms", "Homestay", 1950, "Garden, parking, breakfast", "Sample rating · 4.5", "Wayanad region"),
    ("Hampi", "Karnataka", "Boulder Town Guesthouse", "Guesthouse", 1100, "Wi-Fi, bicycle hire, café", "Sample rating · 4.4", "Hampi bazaar area"),
    ("Tirupati", "Andhra Pradesh", "Temple Town Stay", "Budget hotel", 1250, "Wi-Fi, family rooms, parking", "Sample rating · 4.2", "Tirupati town"),
    ("Visakhapatnam", "Andhra Pradesh", "Coastal Breeze Rooms", "Budget hotel", 1600, "Wi-Fi, AC, breakfast", "Sample rating · 4.3", "Visakhapatnam city area"),
]
HOTELS = [
    {
        "name": row[2], "city": row[0], "state": row[1], "property_type": row[3],
        "price": row[4], "rating": row[5], "amenities": row[6], "location_note": row[7],
        "image": photo(_STAY_IMAGES[index]),
    }
    for index, row in enumerate(_STAY_CITIES)
]

FOODS = [
    {"dish": "Masala Dosa", "region": "Karnataka", "city": "Bengaluru", "price": "₹80–180", "description": "Crisp rice-and-lentil crepe with spiced potato, chutneys, and sambar.", "image": photo("1668236543090-82eba5ee5976")},
    {"dish": "Hyderabadi Biryani", "region": "Telangana", "city": "Hyderabad", "price": "₹180–350", "description": "Fragrant dum-cooked rice layered with warming spices and herbs.", "image": photo("1563379091339-03246963d51a")},
    {"dish": "Pav Bhaji", "region": "Maharashtra", "city": "Mumbai", "price": "₹100–220", "description": "A buttery, spiced vegetable mash served alongside toasted bread rolls.", "image": photo("1606491956689-2ea866880c84")},
    {"dish": "Dal Baati Churma", "region": "Rajasthan", "city": "Jaipur", "price": "₹160–300", "description": "Baked wheat baati paired with lentils and sweet, crumbly churma.", "image": photo("1547592180-85f173990554")},
    {"dish": "Appam with Stew", "region": "Kerala", "city": "Kochi", "price": "₹120–260", "description": "Soft-centered, lacy rice pancakes with gently spiced coconut stew.", "image": photo("1512621776951-a57141f2eefd")},
    {"dish": "Chole Bhature", "region": "Delhi", "city": "Delhi", "price": "₹100–220", "description": "Tangy chickpea curry served alongside airy, deep-fried bread.", "image": photo("1626132647523-66f5bf380027")},
]

BUS_IMAGES = [
    photo("1544620347-c4fd4a3d5957"),
    photo("1570125909232-eb263c188f7e"),
    photo("1494515843206-f3117d3f51b7"),
    photo("1509749836634-16e145f15b8e"),
]

FLIGHT_IMAGES = [
    photo("1436491865332-7a61a109cc05"),
    photo("1529070538774-1843cb3265df"),
    photo("1517479149777-5f3b1511d5ad"),
]
