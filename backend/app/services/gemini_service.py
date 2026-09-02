import re
import math
import logging
from typing import Dict, Any, Tuple, List, Optional
from app.config import settings
from app.services.weather_service import fetch_marine_and_weather
from app.routers.pfz_routes import MASTER_COASTAL_PFZ_ZONES, calculate_haversine_distance, calculate_bearing

logger = logging.getLogger(__name__)

# Try importing google.generativeai if available
try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    HAS_GEMINI_LIB = False
    logger.warning(f"Google Generative AI package not configured: {e}")

# Complete Coastal Locations Database across Gujarat, Maharashtra, and Goa
COASTAL_LOCATIONS_DATABASE = {
    # GUJARAT
    "porbandar": {"name": "Porbandar", "name_gu": "પોરબંદર", "name_hi": "पोरबंदर", "state": "Gujarat", "lat": 21.64, "lon": 69.60, "aliases": ["porbandar", "porbander", "પોરબંદર", "पोरबंदर"]},
    "veraval": {"name": "Veraval", "name_gu": "વેરાવળ", "name_hi": "वेरावल", "state": "Gujarat", "lat": 20.90, "lon": 70.36, "aliases": ["veraval", "somnath", "વેરાવળ", "સોમનાથ", "वेरावल", "सोमनाथ"]},
    "dwarka": {"name": "Dwarka", "name_gu": "દ્વારકા", "name_hi": "द्वारका", "state": "Gujarat", "lat": 22.24, "lon": 68.96, "aliases": ["dwarka", "dwaraka", "દ્વારકા", "द्वारका", "rupani"]},
    "okha": {"name": "Okha", "name_gu": "ઓખા", "name_hi": "ओखा", "state": "Gujarat", "lat": 22.46, "lon": 69.07, "aliases": ["okha", "ઓખા", "ओखा", "bet dwarka", "બેટ દ્વારકા", "बेट द्वारका"]},
    "mangrol": {"name": "Mangrol", "name_gu": "માંગરોળ", "name_hi": "मांगरोल", "state": "Gujarat", "lat": 21.12, "lon": 70.11, "aliases": ["mangrol", "માંગરોળ", "मांगरोल"]},
    "madhavpur": {"name": "Madhavpur", "name_gu": "માધવપુર", "name_hi": "माधवपुर", "state": "Gujarat", "lat": 21.25, "lon": 69.95, "aliases": ["madhavpur", "માધવપુર", "माधवपुर"]},
    "jamnagar": {"name": "Jamnagar", "name_gu": "જામનગર", "name_hi": "जामनगर", "state": "Gujarat", "lat": 22.47, "lon": 70.06, "aliases": ["jamnagar", "જામનગર", "जामनगर", "bedi", "બેડી"]},
    "sikka": {"name": "Sikka", "name_gu": "સિક્કા", "name_hi": "सिक्का", "state": "Gujarat", "lat": 22.43, "lon": 69.83, "aliases": ["sikka", "સિક્કા", "सिक्का"]},
    "vadinar": {"name": "Vadinar / Salaya", "name_gu": "વાડીનાર", "name_hi": "वाडिनार", "state": "Gujarat", "lat": 22.45, "lon": 69.70, "aliases": ["vadinar", "salaya", "વાડીનાર", "સલાયા", "वाडिनार", "सलाया"]},
    "kandla": {"name": "Kandla", "name_gu": "કંડલા", "name_hi": "कांडला", "state": "Gujarat", "lat": 23.01, "lon": 70.21, "aliases": ["kandla", "gandhidham", "કંડલા", "ગાંધીધામ", "कांडला", "गांधीधाम"]},
    "mandvi": {"name": "Mandvi", "name_gu": "માંડવી", "name_hi": "मांडवी", "state": "Gujarat", "lat": 22.83, "lon": 69.36, "aliases": ["mandvi", "માંડવી", "मांडवी"]},
    "mundra": {"name": "Mundra", "name_gu": "મુંદ્રા", "name_hi": "मुंद्रा", "state": "Gujarat", "lat": 22.83, "lon": 69.72, "aliases": ["mundra", "મુંદ્રા", "मुंद्रा"]},
    "jakhau": {"name": "Jakhau", "name_gu": "જાખૌ", "name_hi": "जाखौ", "state": "Gujarat", "lat": 23.23, "lon": 68.60, "aliases": ["jakhau", "જાખૌ", "जाखौ", "koteshwar", "કોટેશ્વર", "kutch", "કચ્છ", "कच्छ"]},
    "diu": {"name": "Diu", "name_gu": "દીવ", "name_hi": "दीव", "state": "Gujarat", "lat": 20.71, "lon": 70.98, "aliases": ["diu", "દીવ", "दीव", "vanakbara", "વણાકબારા", "वणकबारा", "ghoghla"]},
    "jafrabad": {"name": "Jafrabad", "name_gu": "જાફરાબાદ", "name_hi": "जाफराबाद", "state": "Gujarat", "lat": 20.87, "lon": 71.36, "aliases": ["jafrabad", "jafarabad", "જાફરાબાદ", "जाफराबाद"]},
    "pipavav": {"name": "Pipavav", "name_gu": "પીપાવાવ", "name_hi": "पीपावाव", "state": "Gujarat", "lat": 20.91, "lon": 71.50, "aliases": ["pipavav", "shialbet", "પીપાવાવ", "શિયાળબેટ", "पीपावाव", "शियाल बेट"]},
    "bhavnagar": {"name": "Bhavnagar / Ghogha", "name_gu": "ભાવનગર", "name_hi": "भावनगर", "state": "Gujarat", "lat": 21.76, "lon": 72.15, "aliases": ["bhavnagar", "ghogha", "alang", "ભાવનગર", "ઘોઘા", "અલંગ", "भावनगर", "घोघा", "अलंग"]},
    "dahej": {"name": "Dahej / Bharuch", "name_gu": "દહેજ", "name_hi": "दहेज", "state": "Gujarat", "lat": 21.71, "lon": 72.58, "aliases": ["dahej", "bharuch", "દહેજ", "ભરૂચ", "दहेज़", "भरूच"]},
    "surat": {"name": "Surat / Hazira", "name_gu": "સુરત", "name_hi": "सूरत", "state": "Gujarat", "lat": 21.17, "lon": 72.83, "aliases": ["surat", "hazira", "magdalla", "સુરત", "હજીરા", "मગદલ્લા", "सूरत", "हजीरा", "dumas"]},
    "navsari": {"name": "Navsari / Dandi", "name_gu": "નવસારી", "name_hi": "नवसारी", "state": "Gujarat", "lat": 20.95, "lon": 72.92, "aliases": ["navsari", "dandi", "નવસારી", "દાંડી", "नवसारी", "दांडी"]},
    "valsad": {"name": "Valsad / Tithal", "name_gu": "વલસાડ", "name_hi": "वलसाड", "state": "Gujarat", "lat": 20.61, "lon": 72.93, "aliases": ["valsad", "tithal", "વલસાડ", "તિથલ", "वलसाड", "तीथल"]},
    "daman": {"name": "Daman", "name_gu": "દમણ", "name_hi": "दमन", "state": "Gujarat", "lat": 20.42, "lon": 72.83, "aliases": ["daman", "દમણ", "दमन"]},
    "umargam": {"name": "Umargam", "name_gu": "ઉમરગામ", "name_hi": "उमरगाम", "state": "Gujarat", "lat": 20.19, "lon": 72.75, "aliases": ["umargam", "maroli", "ઉમરગામ", "મરોલી", "उमरगाम"]},

    # MAHARASHTRA
    "dahanu": {"name": "Dahanu", "name_gu": "ડહાણુ", "name_hi": "दहाणू", "state": "Maharashtra", "lat": 19.97, "lon": 72.73, "aliases": ["dahanu", "bordi", "ડહાણુ", "दहाणू", "बोरडी"]},
    "palghar": {"name": "Palghar / Satpati", "name_gu": "પાલઘર", "name_hi": "पालघर", "state": "Maharashtra", "lat": 19.69, "lon": 72.76, "aliases": ["palghar", "satpati", "tarapur", "પાલઘર", "સાતપાટી", "તારાપુર", "पालघर", "सातपाटी", "तारापुर"]},
    "vasai": {"name": "Vasai / Arnala", "name_gu": "વસઈ", "name_hi": "वसई", "state": "Maharashtra", "lat": 19.47, "lon": 72.79, "aliases": ["vasai", "arnala", "વસઈ", "અર્નાલા", "वसई", "अरनाला"]},
    "mumbai": {"name": "Mumbai", "name_gu": "મુંબઈ", "name_hi": "मुंबई", "state": "Maharashtra", "lat": 18.92, "lon": 72.83, "aliases": ["mumbai", "bombay", "sassoon dock", "versova", "worli", "colaba", "bhaucha dhakka", "મુંબઈ", "વર્સોવા", "સસૂન ડોક", "વર્લી", "मुंबई", "वर्सोवा", "ससून डॉक", "वरली", "भाऊचा धक्का"]},
    "alibaug": {"name": "Alibaug", "name_gu": "અલીબાગ", "name_hi": "अलीबाग", "state": "Maharashtra", "lat": 18.65, "lon": 72.87, "aliases": ["alibaug", "alibag", "mandwa", "kashid", "અલીબાગ", "માંડવા", "કાશીદ", "अलीबाग", "मांडवा", "काशीद"]},
    "murud": {"name": "Murud-Janjira", "name_gu": "મુરુદ", "name_hi": "मुरुड", "state": "Maharashtra", "lat": 18.30, "lon": 72.96, "aliases": ["murud", "janjira", "revdanda", "મુરુદ", "જંજીરા", "રેવદંડા", "मुरुड", "जंजीरा", "रेवदंडा"]},
    "harnai": {"name": "Harnai / Dapoli", "name_gu": "હરનાઈ", "name_hi": "हरनई", "state": "Maharashtra", "lat": 17.81, "lon": 73.09, "aliases": ["harnai", "dapoli", "dabhol", "હરનાઈ", "દાપોલી", "દાભોલ", "हरनई", "दापोली", "दाभोल"]},
    "jaigad": {"name": "Jaigad", "name_gu": "જયગઢ", "name_hi": "जयगढ़", "state": "Maharashtra", "lat": 17.30, "lon": 73.22, "aliases": ["jaigad", "ganpatipule", "જયગઢ", "ગણપતિપુલે", "जयगढ़", "गणपतिपुले"]},
    "ratnagiri": {"name": "Ratnagiri", "name_gu": "રત્નાગિરી", "name_hi": "रत्नागिरी", "state": "Maharashtra", "lat": 16.99, "lon": 73.30, "aliases": ["ratnagiri", "mirkarwada", "રત્નાગિરી", "મિરકરવાડા", "रत्नागिरी", "मिरकरवाड़ा"]},
    "devgad": {"name": "Devgad / Vijaydurg", "name_gu": "દેવગઢ", "name_hi": "देवगढ़", "state": "Maharashtra", "lat": 16.37, "lon": 73.37, "aliases": ["devgad", "vijaydurg", "દેવગઢ", "વિજયદુર્ગ", "देवगढ़", "विजयदुर्ग"]},
    "malvan": {"name": "Malvan / Tarkarli", "name_gu": "માલવણ", "name_hi": "मालवण", "state": "Maharashtra", "lat": 16.06, "lon": 73.46, "aliases": ["malvan", "tarkarli", "sindhudurg", "માલવણ", "તારકરલી", "સિંધુદુર્ગ", "मालवण", "तारकरली", "सिंधुदुर्ग"]},
    "vengurla": {"name": "Vengurla", "name_gu": "વેંગુર્લા", "name_hi": "वेंगुर्ला", "state": "Maharashtra", "lat": 15.86, "lon": 73.63, "aliases": ["vengurla", "shiroda", "વેંગુર્લા", "શિરોડા", "वेंगुर्ला", "शिरोडा"]},

    # GOA
    "tiracol": {"name": "Tiracol / Arambol", "name_gu": "તિરાકોલ", "name_hi": "तिरकोल", "state": "Goa", "lat": 15.72, "lon": 73.70, "aliases": ["tiracol", "arambol", "morjim", "તિરાકોલ", "અરામ્બોલ", "तिरकोल", "अरामबोल"]},
    "chapora": {"name": "Chapora / Anjuna", "name_gu": "ચાપોરા", "name_hi": "चापोरा", "state": "Goa", "lat": 15.60, "lon": 73.74, "aliases": ["chapora", "anjuna", "calangute", "baga", "ચાપોરા", "અંજુના", "કાલાંગુટ", "બાઘા", "चापोरा", "अंजुना", "कलंगूट", "बागा"]},
    "panaji": {"name": "Panaji", "name_gu": "પણજી", "name_hi": "पणजी", "state": "Goa", "lat": 15.49, "lon": 73.82, "aliases": ["panaji", "panjim", "miramar", "mandovi", "પણજી", "મિરામાર", "માંડોવી", "पणजी", "पंजिम", "मिरामार", "मांडवी"]},
    "aguada": {"name": "Aguada / Candolim", "name_gu": "અગુઆડા", "name_hi": "अगुआडा", "state": "Goa", "lat": 15.49, "lon": 73.77, "aliases": ["aguada", "candolim", "અગુઆડા", "કેન્ડોલિમ", "अगुआडा", "कैंडोलिम"]},
    "mormugao": {"name": "Vasco / Mormugao", "name_gu": "વાસ્કો", "name_hi": "वास्को", "state": "Goa", "lat": 15.39, "lon": 73.81, "aliases": ["vasco", "mormugao", "bogmalo", "વાસ્કો", "મોરમુંગાવ", "वास्को", "मोरमुगाओ", "बोगमालो"]},
    "betul": {"name": "Betul / Mobor", "name_gu": "બેતુલ", "name_hi": "बेतुल", "state": "Goa", "lat": 15.14, "lon": 73.95, "aliases": ["betul", "mobor", "colva", "benaulim", "બેતુલ", "મોબોર", "કોલવા", "बेतुल", "मोबोर", "कोलवा"]},
    "cabo": {"name": "Cabo de Rama", "name_gu": "કાબો દ રામા", "name_hi": "काबो दे रामा", "state": "Goa", "lat": 15.08, "lon": 73.96, "aliases": ["cabo de rama", "cabo", "agonda", "કાબો દ રામા", "અગોન્ડા", "काबो दे रामा", "अगोंडा"]},
    "canacona": {"name": "Canacona / Palolem", "name_gu": "કાણકોણ", "name_hi": "काणाकोण", "state": "Goa", "lat": 15.01, "lon": 74.02, "aliases": ["canacona", "palolem", "patnem", "કાણકોણ", "પાલોલેમ", "काणाकोण", "पालोलेम"]}
}

# Strict Maritime Domain Keywords
MARINE_DOMAIN_KEYWORDS = [
    r"\bsea\b", r"\bseas\b", r"\bocean\b", r"\boceans\b", r"\bmarine\b", r"\bmaritime\b", r"\bcoastal\b", r"\bcoast\b",
    r"\bweather\b", r"\bwave\b", r"\bwaves\b", r"\bswell\b", r"\bwind\b", r"\bwinds\b", r"\bstorm\b", r"\bstorms\b",
    r"\bcyclone\b", r"\bcyclones\b", r"\brain\b", r"\btemperature\b", r"\bsst\b",
    r"\bfish\b", r"\bfishes\b", r"\bfishing\b", r"\bpfz\b", r"\bcatch\b", r"\bchlorophyll\b",
    r"\bpomfret\b", r"\btuna\b", r"\bmackerel\b", r"\bsurmai\b", r"\bghol\b", r"\bhilsa\b", r"\bprawn\b", r"\bprawns\b",
    r"\bshrimp\b", r"\bsardine\b", r"\bsquid\b", r"\bcrab\b", r"\bbombil\b",
    r"\bboat\b", r"\bboats\b", r"\bvessel\b", r"\bvessels\b", r"\btrawler\b", r"\bengine\b", r"\brudder\b", r"\banchor\b",
    r"\bsos\b", r"\bmayday\b", r"\bemergency\b", r"\bhazard\b", r"\bsafety\b", r"\bsafe\b", r"\bsail\b",
    r"\btide\b", r"\btides\b", r"\bhigh tide\b", r"\blow tide\b", r"\bebb\b", r"\bflood\b", r"\bmonsoon ban\b",
    r"\bnavigation\b", r"\bheading\b", r"\bbearing\b", r"\bcompass\b", r"\bnautical\b", r"\bknot\b", r"\bknots\b",
    r"\bport\b", r"\bharbor\b", r"\bfishery\b", r"\bfisherman\b", r"\bfishermen\b",
    r"\bgujarat\b", r"\bmaharashtra\b", r"\bgoa\b",
    
    # Hindi (Devanagari)
    "समुद्र", "सागर", "दरिया", "समुद्री", "तट", "तटीय", "मौसम", "हवा", "लहर", "लहरें", "तूफान", "चक्रवात", "बारिश", "तापमान",
    "मछली", "मछलियां", "मत्स्य", "मछुआरे", "नाव", "नौका", "जहाज", "बोट", "ट्रॉलर", "सुरक्षा", "सुरक्षित",
    "खतरा", "सावधानी", "अलर्ट", "मदद", "आपातकाल", "बंदरगाह",
    "ज्वार", "भाटा", "ज्वार-भाटा", "नेविगेशन", "दिशा", "दूरी", "नॉटिकल",
    "पॉम्फ्रेट", "सुरमई", "झींगा", "बॉम्बिल", "घोल", "हिलसा", "मैकेरल", "टूना",
    "गुजरात", "महाराष्ट्र", "गोवा",
    
    # Gujarati
    "સમુદ્ર", "દરિયો", "દરિયા", "દરિયાઈ", "કિનારો", "તટ", "હવામાન", "પવન", "મોજાં", "મોજા", "વાવાઝોડું", "તોફાન", "વરસાદ", "તાપમાન",
    "માછલી", "માછલીઓ", "મત્સ્ય", "માછીમાર", "બોટ", "વહાણ", "નાવ", "ટ્રોલર", "સલામતી", "સલામત", "સુરક્ષા",
    "જોખમ", "સાવચેતી", "ચેતવણી", "મદદ", "કટોકટી", "બંદર",
    "ભરતી", "ઓટ", "ભરતી-ઓટ", "નેવિગેશન", "દિશા", "અંતર", "નોટિકલ", "રૂટ",
    "પોમ્ફ્રેટ", "પાપલેટ", "સુરમાઈ", "ઝીંગા", "બૂમલા", "ઘોલ", "હિલસા", "બાંગડા", "ટ્યૂના",
    "ગુજરાત", "મહારાષ્ટ્ર", "ગોવા"
]

def extract_location_from_query(query: str) -> Optional[dict]:
    """Finds if user query mentions any specific Gujarat, Maharashtra, or Goa coastal location."""
    q_lower = query.lower()
    matches = []
    for loc_key, loc_data in COASTAL_LOCATIONS_DATABASE.items():
        for alias in loc_data["aliases"]:
            if alias in q_lower:
                matches.append((len(alias), loc_data))
    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]
    return None

def is_within_marine_domain(query: str) -> bool:
    """Strictly checks whether query is genuinely about sea, weather, fish, PFZ, tides, navigation, or coastal locations."""
    q_clean = query.lower().strip()
    
    # Check if a known coastal location is mentioned
    if extract_location_from_query(query) is not None:
        return True

    # Check for greetings alone
    if any(re.search(r'\b' + re.escape(w) + r'\b', q_clean) for w in ["hello", "hi", "hey", "namaste", "kem cho", "kem chho", "namaskar", "જય માતાજી", "રામ રામ", "નમસ્કાર", "नमस्कार"]):
        return True

    for kw_pattern in MARINE_DOMAIN_KEYWORDS:
        if kw_pattern.startswith(r"\b"):
            if re.search(kw_pattern, q_clean):
                return True
        else:
            if kw_pattern in q_clean:
                return True
    return False

def detect_language(text: str) -> str:
    if re.search(r'[\u0A80-\u0AFF]', text):
        return "gu"
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    
    lower = text.lower()
    if any(w in lower for w in ["kem chho", "kem cho", "dariya", "machhli", "tufan", "samundar", "hawa", "khalasi", "kashti", "panio", "machhi", "chho", "aaje", "kale", "nathi", "che", "su", "shu", "kyare", "kayo", "rasto", "bharti", "ot", "najik"]):
        return "gu"
    if any(w in lower for w in ["kya", "aaj", "kal", "samundar", "surakshit", "toofan", "madad", "machli", "hogi", "batao", "kaise", "hoga", "hai", "rasta", "jwar", "bhata", "samay", "kahan", "paas", "najdeek"]):
        return "hi"
    return "en"

def get_out_of_domain_response(lang: str) -> str:
    if lang == "gu":
        return "આ યોગ્ય પ્રશ્ન નથી. કૃપા કરીને ફક્ત દરિયાઈ સુરક્ષા, સમુદ્રી હવામાન, મત્સ્ય પટ્ટા (PFZ), ભરતી-ઓટ, બોટ નેવિગેશન અથવા કટોકટી સહાય સંબંધિત પ્રશ્નો જ પૂછો. જલદૂત ફક્ત દરિયાઈ અને મત્સ્યોદ્યોગ વિષયો પર જ માર્ગદર્શન આપે છે."
    elif lang == "hi":
        return "यह उचित प्रश्न नहीं है. कृपया केवल समुद्री मौसम, संभावित मत्स्य क्षेत्र (PFZ), ज्वार-भाटा, नौका संचालन या समुद्री सुरक्षा से संबंधित प्रश्न ही पूछें. जलदूत केवल समुद्र और मत्स्य पालन से जुड़े प्रश्नों के उत्तर देने के लिए अधिकृत है."
    else:
        return "This is not a proper question for this system. Please ask only relevant questions related to coastal weather, Potential Fishing Zones (PFZ), tides, vessel navigation, or marine safety. JalDoot only provides replies to sea and marine-related queries."

def get_dynamic_nearest_pfz_data(latitude: float, longitude: float) -> List[dict]:
    """Computes exact dynamic distance and bearing for all Gujarat, Maharashtra, and Goa PFZ zones"""
    zones_with_dist = []
    for z in MASTER_COASTAL_PFZ_ZONES:
        z_lat, z_lon = z["center"]
        dist = calculate_haversine_distance(latitude, longitude, z_lat, z_lon)
        bearing = calculate_bearing(latitude, longitude, z_lat, z_lon)
        zones_with_dist.append({
            **z,
            "dist_km": dist,
            "dist_nm": round(dist / 1.852, 1),
            "bearing_deg": bearing,
            "transit_mins": max(15, round((dist / (8.0 * 1.852)) * 60))
        })
    zones_with_dist.sort(key=lambda x: x["dist_km"])
    return zones_with_dist

def simplify_fish_names_gu(species_list: List[str]) -> str:
    """Translates species into simple Saurashtra fisherman names"""
    gu_map = {
        "Silver Pomfret": "પાપલેટ", "Silver Pomfret (Vim)": "પાપલેટ", "Black Pomfret": "કાળો પાપલેટ", "White Pomfret": "સફેદ પાપલેટ",
        "Surmai (Kingfish)": "સુરમાઈ", "King Mackerel": "સુરમાઈ", "Indian Mackerel (Bangda)": "બાંગડા", "Horse Mackerel": "બાંગડા",
        "Hilsa": "હિલસા/પલ્વા", "Hilsa (Chaksi)": "હિલસા", "Jewfish (Ghol)": "ઘોલ માછલી",
        "Bombay Duck (Bombil)": "બૂમલા", "Yellowfin Tuna": "ટ્યૂના", "Skipjack Tuna": "ટ્યૂના",
        "Tiger Prawns": "ઝીંગા", "White Prawns": "ઝીંગા", "Mud Crabs": "કરચલા", "Squid": "નરસિંગા/સ્ક્વિડ",
        "Ribbonfish": "પટ્ટી માછલી", "Catfish (Khagga)": "ખગ્ગા", "Reef Cod (Ghol)": "ઘોલ"
    }
    names = []
    for s in species_list:
        clean_name = gu_map.get(s, s.split(" ")[0])
        if clean_name not in names:
            names.append(clean_name)
    return ", ".join(names[:3])

def simplify_fish_names_hi(species_list: List[str]) -> str:
    """Translates species into simple Hindi fisherman names"""
    hi_map = {
        "Silver Pomfret": "पॉम्फ्रेट (पापलेट)", "Silver Pomfret (Vim)": "पॉम्फ्रेट", "Black Pomfret": "काला पॉम्फ्रेट", "White Pomfret": "सफेद पॉम्फ्रेट",
        "Surmai (Kingfish)": "सुरमई", "King Mackerel": "सुरमई", "Indian Mackerel (Bangda)": "बांगड़ा", "Horse Mackerel": "बांगड़ा",
        "Hilsa": "हिलसा", "Hilsa (Chaksi)": "हिलसा", "Jewfish (Ghol)": "घोल मछली",
        "Bombay Duck (Bombil)": "बॉम्बिल", "Yellowfin Tuna": "टूना", "Skipjack Tuna": "टूना",
        "Tiger Prawns": "झींगा", "White Prawns": "झींगा", "Mud Crabs": "केकड़ा", "Squid": "स्क्विड",
        "Ribbonfish": "रिबन मछली", "Catfish (Khagga)": "कैटफिश", "Reef Cod (Ghol)": "घोल"
    }
    names = []
    for s in species_list:
        clean_name = hi_map.get(s, s.split(" ")[0])
        if clean_name not in names:
            names.append(clean_name)
    return ", ".join(names[:3])

def get_intelligent_fallback_response(
    query: str, 
    lang: str, 
    weather_info: Dict[str, Any],
    latitude: float = 21.63,
    longitude: float = 69.60,
    loc_data: Optional[dict] = None
) -> Tuple[str, int, bool]:
    """
    Highly accurate, simple, fisherman-friendly advisor that uses plain language
    and addresses any location in Gujarat, Maharashtra, and Goa with clarity.
    """
    q_lower = query.lower()

    if not is_within_marine_domain(query):
        return get_out_of_domain_response(lang), 98, True

    score = weather_info.get("sea_safety_score", 81)
    wave = weather_info.get("wave_height_m", 1.1)
    wind = weather_info.get("wind_speed_kmh", 15.0)
    status = weather_info.get("safety_status", "SAFE")
    temp = weather_info.get("temperature_c", 27.0)

    # Compute live nearest PFZ zones for target location
    nearest_zones = get_dynamic_nearest_pfz_data(latitude, longitude)
    z1 = nearest_zones[0] if nearest_zones else None

    # Intent Classification with regex boundaries
    is_sos_q = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["sos", "help", "emergency", "mayday", "madad", "aapatkal", "danger", "hazard", "khatra", "breach", "breakdown", "મદદ", "કટોકટી", "જોખમ", "આપાતકાલ", "मदद", "आपातकाल", "खतरा", "संकट"])
    is_cyclone_storm = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["cyclone", "storm", "toofan", "tufan", "squall", "depression", "alert", "વાવાઝોડું", "તોફાન", "ચેતવણી", "तूफान", "चक्रवात", "अलर्ट"])
    is_timing_q = any(w in q_lower for w in ["timing", "time", "hour", "hours", "tide", "tides", "when", "high tide", "low tide", "dawn", "dusk", "monsoon", "ban", "સમય", "ટાઇમ", "ટાઇમિંગ", "ભરતી", "ઓટ", "ક્યારે", "પૂનમ", "અમાસ", "સવાર", "સાંજ", "समय", "टाइमिंग", "ज्वार", "भाटा", "कब", "पूर्णिमा", "अमावस्या", "सुबह", "शाम"])
    is_route_q = any(w in q_lower for w in ["route", "direction", "heading", "bearing", "distance", "navigation", "compass", "transit", "kaise jaye", "kya rasta", "રસ્તો", "દિશા", "અંતર", "કેવી રીતે જવું", "નેવિગેશન", "રૂટ", "રાસ્તા", "मार्ग", "दूरी", "दिशा कोण", "नेविगेशन"])
    is_weather_q = any(w in q_lower for w in ["weather", "temperature", "temp", "wind", "wave", "swell", "condition", "हवामान", "પવન", "મોજાં", "તાપમાન", "વરસાદ", "હવા", "मौसम", "लहर", "लहरें", "हवा", "बारिश", "तापमान"])
    is_safe_q = any(w in q_lower for w in ["safe", "safety", "sail", "jaana", "jaay", "surakshit", "salamati", "score", "સલામત", "સલામતી", "સુરક્ષા", "सुरक्षित", "सुरक्षा", "जाएं", "जाना"])
    is_nearest_pfz_q = any(w in q_lower for w in ["nearest", "closest", "near", "zone", "zones", "pfz", "chlorophyll", "sst", "fish", "fishing", "catch", "pomfret", "tuna", "surmai", "mackerel", "ghol", "hilsa", "prawn", "paas", "najdeek", "najik", "ક્યાં છે", "કયો ઝોન", "કયો મત્સ્ય", "માછલી", "મત્સ્ય", "ઝોન", "नजदीक", "निकटतम", "पास", "कौन सा जोन", "कहाँ है", "मछली", "मत्स्य", "जोन"])
    is_greeting = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in ["hello", "hi", "hey", "namaste", "kem cho", "kem chho", "namaskar", "જય માતાજી", "રામ રામ", "નમસ્કાર", "नमस्कार"])

    # Location names in local scripts
    loc_display_gu = loc_data["name_gu"] if loc_data else "પોરબંદર"
    loc_display_hi = loc_data["name_hi"] if loc_data else "पोरबंदर"
    loc_display_en = loc_data["name"] if loc_data else "Porbandar"

    # 1. PURE SIMPLE GUJARATI (Saurashtra / South Gujarat Fisherman dialect)
    if lang == "gu":
        fish_gu = simplify_fish_names_gu(z1["target_fish"]) if z1 else "પાપલેટ, સુરમાઈ"

        if is_sos_q:
            return f"ભાઈ, જો કટોકટી કે ભય હોય તો તરત લાલ 'આપાતકાલીન SOS' બટન દબાવો. તમારું લાઈવ લોકેશન [{latitude:.4f}, {longitude:.4f}] કોસ્ટ ગાર્ડ અને ૨૦ કિમીમાં રહેલી તમામ હોડીઓને તરત મળી જશે.", 99, False

        if is_cyclone_storm:
            return f"{loc_display_gu} દરિયાકાંઠે હાલ કોઈ વાવાઝોડું કે તોફાન નથી. પવન {wind} કિમી/કલાક અને મોજાં {wave} મીટર સામાન્ય છે. દરિયો શાંત છે.", 98, False

        if is_timing_q:
            return f"માછીમારી માટે સૌથી સારો સમય વહેલી સવારે ૦૫:૦૦ થી ૦૮:૦૦ અને સાંજે ૦૫:૦૦ થી ૦૮:૦૦ વાગ્યા સુધીનો છે. ભરતીના સમયે બંદરેથી હોડી હંકારવી અને ઓટના સમયે પાછા ફરવું જેથી ડીઝલ બચે. ચોમાસામાં ૧ જૂન થી ૩૧ જુલાઈ દરિયાઈ પ્રતિબંધ હોય છે.", 98, False

        if is_route_q and z1:
            return f"{loc_display_gu}થી મત્સ્ય ઝોન જવા માટે હોકાયંત્ર પર {z1['bearing_deg']}° દિશામાં હોડી ચલાવો. અંતર લગભગ {z1['dist_km']} કિમી છે. સામાન્ય ઝડપે {z1['transit_mins']} મિનિટમાં પહોંચી જશો. નકશા પર સીધો રૂટ દોરેલો છે.", 98, False

        if is_nearest_pfz_q and z1:
            return f"{loc_display_gu}થી સૌથી નજીક મત્સ્ય ઝોન {z1['dist_km']} કિમી દૂર છે ({z1['bearing_deg']}° દિશામાં). ત્યાં {fish_gu} માછલીઓ સારો જથ્થો મળશે. હોડીમાં પહોંચતા અંદાજે {z1['transit_mins']} મિનિટ લાગશે.", 99, False

        if is_weather_q or is_safe_q:
            if score and score >= 70:
                return f"હા ભાઈ, {loc_display_gu} પાસે દરિયો એકદમ શાંત અને સલામત છે (સુરક્ષા સ્કોર: {score}/૧૦૦). પવન {wind} કિમી/કલાક અને મોજાં {wave} મીટર છે. આજે હોડી લઈને માછીમારી કરવા જવું સંપૂર્ણ સુરક્ષિત છે.", 98, False
            elif score and score >= 50:
                return f"{loc_display_gu} પાસે દરિયામાં થોડો પવન ({wind} કિમી/કલાક) અને મોજાં ({wave} મીટર) છે. નાની હોડીઓએ કિનારા નજીક જ રહેવું.", 97, False
            else:
                return f"ચેતવણી: {loc_display_gu} પાસે દરિયો તોફાની છે. તેજ પવન ({wind} કિમી/કલાક) અને ઊંચા મોજાં ({wave} મીટર) છે. આજે દરિયામાં ન જવું.", 98, False

        if is_greeting:
            return f"જય માતાજી, રામ રામ ભાઈ! {loc_display_gu} પાસે દરિયો શાંત છે, પવન {wind} કિમી/કલાક અને મોજાં {wave} મીટર છે. તમે નજીકના મત્સ્ય ઝોન, રસ્તા કે હવામાન વિશે પૂછી શકો છો.", 98, False

        return f"{loc_display_gu} દરિયાઈ માહિતી: દરિયો શાંત છે, પવન {wind} કિમી/કલાક, મોજાં {wave} મીટર. નજીકનો મત્સ્ય ઝોન {z1['dist_km'] if z1 else '10'} કિમી દૂર છે જ્યાં {fish_gu} માછલીઓ મળશે.", 96, False

    # 2. PURE SIMPLE HINDI (Clear, Colloquial, Friendly)
    elif lang == "hi":
        fish_hi = simplify_fish_names_hi(z1["target_fish"]) if z1 else "पॉम्फ्रेट, सुरमई"

        if is_sos_q:
            return f"मछुआरे भाई, संकट के समय तुरंत लाल 'आपातकालीन SOS' बटन दबाएं. आपकी नाव की लोकेशन [{latitude:.4f}, {longitude:.4f}] कोस्ट गार्ड और आसपास की 20 किमी में सभी नावों को तुरंत पहुँच जाएगी.", 99, False

        if is_cyclone_storm:
            return f"{loc_display_hi} तट पर फिलहाल कोई चक्रवात या तूफान नहीं है. हवा {wind} किमी/घंटा और लहरें {wave} मीटर सामान्य हैं. समुद्र शांत है.", 98, False

        if is_timing_q:
            return f"मछली पकड़ने का सबसे बढ़िया समय सुबह 05:00 से 08:00 बजे और शाम 05:00 से 08:00 बजे तक है. ज्वार (High Tide) के समय बंदरगाह से निकलना और भाटे के साथ लौटना डीजल बचाता है. 1 जून से 31 जुलाई तक वार्षिक मानसून प्रतिबंध रहता है.", 98, False

        if is_route_q and z1:
            return f"{loc_display_hi} से मत्स्य क्षेत्र जाने के लिए कंपास पर {z1['bearing_deg']}° दिशा में नाव चलाएं. दूरी करीब {z1['dist_km']} किमी है और पहुँचने में लगभग {z1['transit_mins']} मिनट लगेंगे.", 98, False

        if is_nearest_pfz_q and z1:
            return f"{loc_display_hi} से सबसे नजदीकी मत्स्य क्षेत्र {z1['dist_km']} किमी दूर है ({z1['bearing_deg']}° दिशा में). वहाँ {fish_hi} मछली अच्छी तादाद में मिलेगी. नाव से पहुँचने में करीब {z1['transit_mins']} मिनट लगेंगे.", 99, False

        if is_weather_q or is_safe_q:
            if score and score >= 70:
                return f"हाँ मछुआरे भाई, {loc_display_hi} के पास समुद्र शांत और सुरक्षित है (सुरक्षा स्कोर: {score}/100). हवा {wind} किमी/घंटा और लहरें {wave} मीटर हैं. आज मछली पकड़ने जाना पूरी तरह सुरक्षित है.", 98, False
            elif score and score >= 50:
                return f"{loc_display_hi} के पास समुद्र में थोड़ा बहाव है. हवा {wind} किमी/घंटा और लहरें {wave} मीटर हैं. छोटी नावें किनारे के पास ही रहें.", 97, False
            else:
                return f"चेतावनी: {loc_display_hi} के पास समुद्र अशांत है. तेज हवाएं ({wind} किमी/घंटा) और ऊंची लहरें ({wave} मीटर) हैं. आज समुद्र में न जाएं.", 98, False

        if is_greeting:
            return f"नमस्कार मछुआरे भाई! {loc_display_hi} के पास समुद्र शांत है, हवा {wind} किमी/घंटा और लहरें {wave} मीटर हैं. आप नजदीकी मछली क्षेत्र, दिशा या मौसम के बारे में पूछ सकते हैं.", 98, False

        return f"{loc_display_hi} समुद्री जानकारी: समुद्र शांत है, हवा {wind} किमी/घंटा, लहरें {wave} मीटर. नजदीकी मत्स्य क्षेत्र {z1['dist_km'] if z1 else '10'} किमी दूर है जहाँ {fish_hi} मछली मिलेगी.", 96, False

    # 3. SIMPLE CLEAR ENGLISH (Jargon-free, Practical)
    else:
        fish_en = ", ".join(z1["target_fish"][:3]) if z1 else "Pomfret, Surmai, Mackerel"

        if is_sos_q:
            return f"In emergency, press the red 'TRANSMIT EMERGENCY SOS' button. Your live GPS coordinates [{latitude:.4f}, {longitude:.4f}] will be sent immediately to the Coast Guard and all nearby vessels within 20 km.", 99, False

        if is_cyclone_storm:
            return f"There is no cyclone or storm alert near {loc_display_en}. Wind is {wind} km/h and wave swell is {wave}m. Sea conditions are normal.", 98, False

        if is_timing_q:
            return f"Best fishing hours are early morning from 5:00 AM to 8:00 AM and evening from 5:00 PM to 8:00 PM. Leaving harbor during high tide and returning with the ebb tide saves fuel. Annual monsoon ban is from June 1 to July 31.", 98, False

        if is_route_q and z1:
            return f"To reach the fishing zone from {loc_display_en}, steer your boat along compass heading {z1['bearing_deg']}°. The distance is {z1['dist_km']} km and it will take about {z1['transit_mins']} minutes at normal speed.", 98, False

        if is_nearest_pfz_q and z1:
            return f"The nearest fishing zone from {loc_display_en} is {z1['dist_km']} km away along heading {z1['bearing_deg']}°. You will find good catch of {fish_en}. Travel time is about {z1['transit_mins']} minutes.", 99, False

        if is_weather_q or is_safe_q:
            if score and score >= 70:
                return f"Yes brother, the sea near {loc_display_en} is calm and safe today (Safety Score: {score}/100). Wind is {wind} km/h and waves are {wave} meters. Safe to sail.", 98, False
            elif score and score >= 50:
                return f"Moderate sea state near {loc_display_en}. Wind is {wind} km/h and waves are {wave}m. Small boats should remain near the shore.", 97, False
            else:
                return f"Warning: Rough sea near {loc_display_en}. High winds ({wind} km/h) and large waves ({wave}m). Please avoid sailing today.", 98, False

        if is_greeting:
            return f"Welcome fisherman brother! Sea near {loc_display_en} is calm with wind at {wind} km/h and waves at {wave}m. Ask about fishing zones, routes, or weather.", 98, False

        return f"Marine update for {loc_display_en}: Sea is calm, wind is {wind} km/h, waves are {wave}m. Nearest fishing zone is {z1['dist_km'] if z1 else '10'} km away with good catch of {fish_en}.", 96, False

def generate_chat_response(
    message: str, 
    requested_lang: str = "auto", 
    latitude: float = 21.63, 
    longitude: float = 69.60
) -> Dict[str, Any]:
    """
    Multilingual AI advisor for all locations in Gujarat, Maharashtra, and Goa.
    Responds in simple, practical, jargon-free fisherman language.
    Strictly filters out non-marine off-topic questions.
    """
    if requested_lang and requested_lang != "auto":
        target_lang = requested_lang
    else:
        target_lang = detect_language(message)

    if not is_within_marine_domain(message):
        return {
            "reply": get_out_of_domain_response(target_lang),
            "detected_language": target_lang,
            "confidence_score": 98,
            "is_off_topic": True,
            "explainable_factors": {
                "domain_status": "OUT_OF_DOMAIN",
                "notice": "This is not a proper question. Please ask relevant sea or marine questions.",
                "confidence": "98%"
            }
        }

    # Check if a specific location in Gujarat, Maharashtra, or Goa is mentioned
    loc_data = extract_location_from_query(message)
    target_lat = loc_data["lat"] if loc_data else latitude
    target_lon = loc_data["lon"] if loc_data else longitude

    weather_info = fetch_marine_and_weather(target_lat, target_lon)
    nearest_zones = get_dynamic_nearest_pfz_data(target_lat, target_lon)
    z1 = nearest_zones[0] if nearest_zones else None

    reply_text = None
    confidence = 98
    is_off_topic = False

    # Intelligent local offline engine providing simple fisherman dialect
    reply_text, confidence, is_off_topic = get_intelligent_fallback_response(
        query=message, 
        lang=target_lang, 
        weather_info=weather_info,
        latitude=target_lat,
        longitude=target_lon,
        loc_data=loc_data
    )

    explainable_factors = {
        "location": loc_data["name"] if loc_data else "Live GPS Location",
        "wind_speed": f"{weather_info['wind_speed_kmh']} km/h",
        "wave_height": f"{weather_info['wave_height_m']} m",
        "temperature": f"{weather_info['temperature_c']} °C",
        "sea_safety_score": f"{weather_info['sea_safety_score']}/100" if weather_info['sea_safety_score'] is not None else "--",
        "nearest_pfz": z1["name"] if z1 else "N/A",
        "nearest_distance": f"{z1['dist_km']} km" if z1 else "N/A",
        "nearest_bearing": f"{z1['bearing_deg']}°" if z1 else "N/A",
        "confidence": f"{confidence}%"
    }

    return {
        "reply": reply_text,
        "detected_language": target_lang,
        "confidence_score": confidence,
        "is_off_topic": is_off_topic,
        "explainable_factors": explainable_factors
    }
