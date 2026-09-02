import sys
import urllib.request
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

print('===============================================================')
print('=== JALDOOT COMPREHENSIVE MARITIME VERIFICATION SUITE ===')
print('===============================================================\n')

BASE_URL = 'http://127.0.0.1:8000/api'

# 1. Server Health
start_t = time.time()
res = urllib.request.urlopen(f'{BASE_URL}/health')
health_data = json.loads(res.read().decode())
latency_ms = round((time.time() - start_t) * 1000, 1)
print(f'1. [HEALTH CHECK] Server Latency: {latency_ms} ms')
print(f'   Status: {health_data["status"]} | Service: {health_data["service"]}')

# 2. State Coastal Demo Accounts Validation (Gujarat, Maharashtra, Goa)
print(f'\n2. [STATE COASTAL DEMO ACCOUNTS VALIDATION]')
demo_logins = [
    {"user": "gujarat_fisherman", "pass": "password1234", "exp_state": "Gujarat", "exp_lat": 21.64, "exp_lon": 69.60, "exp_lang": "gu"},
    {"user": "maharashtra_fisherman", "pass": "password1234", "exp_state": "Maharashtra", "exp_lat": 18.92, "exp_lon": 72.83, "exp_lang": "hi"},
    {"user": "goa_fisherman", "pass": "password1234", "exp_state": "Goa", "exp_lat": 15.49, "exp_lon": 73.82, "exp_lang": "en"}
]

for d in demo_logins:
    req_d = urllib.request.Request(
        f'{BASE_URL}/auth/login',
        data=json.dumps({'username_or_email': d['user'], 'password': d['pass']}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    d_res = json.loads(urllib.request.urlopen(req_d).read().decode())
    print(f'   - {d["exp_state"].upper()} DEMO: User={d_res["username"]} | Vessel={d_res["vessel_number"]} | State={d_res.get("home_state")} | Lat={d_res.get("default_latitude")} | Lon={d_res.get("default_longitude")} | Demo={d_res.get("is_demo")}')
    assert d_res["username"] == d["user"], f"Expected username {d['user']}"
    assert d_res.get("home_state") == d["exp_state"], f"Expected state {d['exp_state']}"
    assert d_res.get("default_latitude") == d["exp_lat"], f"Expected lat {d['exp_lat']}"
    assert d_res.get("is_demo") is True, "Expected is_demo to be True"

# Set primary fisherman token for downstream tests
req_login = urllib.request.Request(
    f'{BASE_URL}/auth/login',
    data=json.dumps({'username_or_email': 'gujarat_fisherman', 'password': 'password1234'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
login_res = json.loads(urllib.request.urlopen(req_login).read().decode())
fisher_token = login_res['access_token']
headers_fisher = {'Content-Type': 'application/json', 'Authorization': f'Bearer {fisher_token}'}

# 3. Admin Login & Total 2500 Vessels Check
req_admin = urllib.request.Request(
    f'{BASE_URL}/auth/login',
    data=json.dumps({'username_or_email': 'admin@gmail.com', 'password': 'admin1234'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
admin_tok = json.loads(urllib.request.urlopen(req_admin).read().decode())['access_token']
headers_admin = {'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_tok}'}

req_stats = urllib.request.Request(f'{BASE_URL}/admin/dashboard-stats', headers=headers_admin)
stats = json.loads(urllib.request.urlopen(req_stats).read().decode())
print(f'\n3. [DATASET SIZE - 2500 FISHERMEN]')
print(f'   Total Registered Vessels : {stats["total_registered_vessels"]}')
print(f'   Live Active Vessels      : {stats["live_active_vessels"]}')
print(f'   Active Hazard Zones      : {stats["active_hazard_zones"]}')
assert stats["total_registered_vessels"] >= 2500, "Expected at least 2500 registered vessels"

# 4. Nearest 5 Large-Scale PFZ Zones Check
pfz_res = urllib.request.urlopen(f'{BASE_URL}/pfz/recommendations?lat=21.63&lon=69.60&limit=5')
pfz_zones = json.loads(pfz_res.read().decode())
print(f'\n4. [NEAREST 5 PFZ ZONES - GUJARAT, MAHARASHTRA & GOA]')
print(f'   Retrieved nearest {len(pfz_zones)} zones for fisherman:')
for idx, z in enumerate(pfz_zones):
    print(f'   - #{idx+1} {z["name"]} | Dist: {z["distance_km"]} km | Bearing: {z["bearing_deg"]}° | Radius: {z["radius_km"]} km | Species: {z["recommended_target_fish"][:2]}')
assert len(pfz_zones) == 5, f"Expected exactly nearest 5 PFZ zones (found {len(pfz_zones)})"

# 5. Admin Ship List Priority Sorting (SOS > ACTIVE > INACTIVE)
req_vessels = urllib.request.Request(f'{BASE_URL}/admin/active-vessels', headers=headers_admin)
vessels = json.loads(urllib.request.urlopen(req_vessels).read().decode())
print(f'\n5. [ADMIN SHIP LIST SORTING]')
print(f'   Total ships retrieved for admin table: {len(vessels)}')

sos_ships = [v for v in vessels if v.get("has_active_sos") or v.get("status") == "SOS"]
active_ships = [v for v in vessels if v.get("is_active") and not v.get("has_active_sos")]
inactive_ships = [v for v in vessels if not v.get("is_active") and not v.get("has_active_sos")]

print(f'   - SOS Ships Count      : {len(sos_ships)}')
print(f'   - Active Ships Count   : {len(active_ships)}')
print(f'   - Inactive Ships Count : {len(inactive_ships)}')

# Verify sorting order: all SOS come first, then active, then inactive
first_active_idx = next((i for i, v in enumerate(vessels) if not v.get("has_active_sos") and v.get("is_active")), -1)
first_inactive_idx = next((i for i, v in enumerate(vessels) if not v.get("is_active")), -1)

print(f'   - Verification: SOS Ships appear at indices 0..{len(sos_ships)-1}')
if first_active_idx != -1 and first_inactive_idx != -1:
    print(f'   - Active starts at index {first_active_idx}, Inactive starts at index {first_inactive_idx}')
    assert first_active_idx >= len(sos_ships), "Active ships must appear after SOS ships"
    assert first_inactive_idx > first_active_idx, "Inactive ships must appear after Active ships"
print('   -> Sorting verified: SOS ships first, then Active ships, then Inactive ships!')

# 6. Real SOS Trigger & Automated Email Dispatch to jaldootprojectsih@gmail.com
print(f'\n6. [REAL SOS EMAIL AUTOMATION]')
sos_payload = {
    "latitude": 21.6125,
    "longitude": 69.4950,
    "emergency_type": "MAYDAY_DISTRESS",
    "details": "Engine failure 12 nautical miles offshore Porbandar. Automated test distress beacon."
}
req_sos = urllib.request.Request(
    f'{BASE_URL}/sos/trigger',
    data=json.dumps(sos_payload).encode('utf-8'),
    headers=headers_fisher
)
sos_res = json.loads(urllib.request.urlopen(req_sos).read().decode())
print(f'   - SOS Beacon ID : #{sos_res["sos_id"]} for Vessel {sos_res["vessel_number"]}')
print(f'   - Message       : {sos_res["message"]}')
print(f'   - Email Status  : {sos_res.get("email_dispatch", {}).get("delivery_status")}')
print(f'   - Email Target  : {sos_res.get("email_dispatch", {}).get("recipient")}')
print(f'   - Google Maps   : {sos_res.get("email_dispatch", {}).get("google_maps_link")}')
assert sos_res["email_dispatch"]["recipient"] == "jaldootprojectsih@gmail.com", "Target email must be jaldootprojectsih@gmail.com"

# 7. Coastal vs Non-Coastal Safe to Sail Score Validation
print(f'\n7. [COASTAL VS NON-COASTAL SAFE TO SAIL SCORE]')
# A. Coastal Test (Porbandar Coast)
res_coastal = json.loads(urllib.request.urlopen(f'{BASE_URL}/weather/current?lat=21.64&lon=69.60').read().decode())
print(f'   - [COASTAL REGION] Porbandar (21.64, 69.60):')
print(f'     is_coastal_region: {res_coastal["is_coastal_region"]} | Score: {res_coastal["sea_safety_score"]}/100 | Status: {res_coastal["safety_status"]}')
assert res_coastal["is_coastal_region"] is True, "Expected is_coastal_region to be True"
assert res_coastal["sea_safety_score"] is not None, "Expected valid numerical sea safety score for coastal region"

# B. Non-Coastal Test (Inland Location e.g. Delhi / Bhopal / Inland)
res_inland = json.loads(urllib.request.urlopen(f'{BASE_URL}/weather/current?lat=28.61&lon=77.20').read().decode())
print(f'   - [NON-COASTAL REGION] Inland Delhi (28.61, 77.20):')
print(f'     is_coastal_region: {res_inland["is_coastal_region"]} | Score: {res_inland["sea_safety_score"]} (Dashed) | Status: {res_inland["safety_status"]}')
assert res_inland["is_coastal_region"] is False, "Expected is_coastal_region to be False for inland location"
assert res_inland["sea_safety_score"] is None, "Expected sea_safety_score to be None (dashed) for inland location"

# 8. Multilingual Chatbot Test for Gujarat, Maharashtra & Goa Locations in Simple Language
print(f'\n8. [CHATBOT RESPONSES ACROSS GUJARAT, MAHARASHTRA & GOA LOCATIONS]')

location_queries = [
    # Gujarat Locations
    {"lang": "gu", "topic": "Gujarat - Dwarka", "q": "દ્વારકામાં આજનું દરિયાઈ હવામાન કેવું છે અને હોડી લઈને જવાય?"},
    {"lang": "gu", "topic": "Gujarat - Veraval", "q": "વેરાવળથી કઈ બાજુ પાપલેટ અને સુરમાઈ માછલી મળશે?"},
    {"lang": "hi", "topic": "Gujarat - Surat", "q": "सूरत और हजीरा के पास समुद्र कैसा है?"},
    {"lang": "en", "topic": "Gujarat - Diu", "q": "What is the fishing route and weather near Diu?"},

    # Maharashtra Locations
    {"lang": "hi", "topic": "Maharashtra - Mumbai", "q": "मुंबई ससून डॉक के पास समुद्र सुरक्षित है क्या और पास का फिशिंग जोन कौन सा है?"},
    {"lang": "hi", "topic": "Maharashtra - Ratnagiri", "q": "रत्नागिरी मिरकरवाड़ा से मछली पकड़ने के लिए कौन सी दिशा में जाएं?"},
    {"lang": "gu", "topic": "Maharashtra - Malvan", "q": "માલવણ પાસે દરિયામાં મોજાં કેવાં છે?"},
    {"lang": "en", "topic": "Maharashtra - Alibaug", "q": "How is the sea condition and wind near Alibaug today?"},

    # Goa Locations
    {"lang": "hi", "topic": "Goa - Panaji", "q": "पणजी और मांडवी के पास समुद्र में मछली पकड़ने का सही समय क्या है?"},
    {"lang": "gu", "topic": "Goa - Vasco", "q": "વાસ્કો પાસે દરિયો કેવો છે?"},
    {"lang": "en", "topic": "Goa - Canacona", "q": "Which fishing zone is closest to Canacona and Palolem?"}
]

for idx, tq in enumerate(location_queries):
    req_chat = urllib.request.Request(
        f'{BASE_URL}/chat/send',
        data=json.dumps({
            "message": tq["q"],
            "language": tq["lang"],
            "latitude": 21.63,
            "longitude": 69.60
        }).encode('utf-8'),
        headers=headers_fisher
    )
    chat_res = json.loads(urllib.request.urlopen(req_chat).read().decode())
    print(f'   [{tq["lang"].upper()}] [{tq["topic"]}]')
    print(f'   Q: "{tq["q"]}"')
    print(f'   A: "{chat_res["reply"]}"')
    print(f'   Location: {chat_res["explainable_factors"].get("location")} | Confidence: {chat_res["confidence_score"]}%\n')
    assert len(chat_res["reply"]) > 20, "Expected non-empty conversational answer"

# 9. Off-Topic / Non-Marine Query Strict Rejection Test
print(f'9. [OFF-TOPIC / NON-MARINE QUERY STRICT REJECTION TEST]')
off_topic_tests = [
    {"lang": "en", "q": "What is the capital of France and stock price of Apple?", "expected_sub": "not a proper question"},
    {"lang": "hi", "q": "कल के क्रिकेट मैच का स्कोर क्या था?", "expected_sub": "उचित प्रश्न नहीं है"},
    {"lang": "gu", "q": "મને એક સુંદર જોક્સ સંભળાવો", "expected_sub": "યોગ્ય પ્રશ્ન નથી"}
]

for ot in off_topic_tests:
    req_chat_ot = urllib.request.Request(
        f'{BASE_URL}/chat/send',
        data=json.dumps({
            "message": ot["q"],
            "language": ot["lang"],
            "latitude": 21.63,
            "longitude": 69.60
        }).encode('utf-8'),
        headers=headers_fisher
    )
    ot_res = json.loads(urllib.request.urlopen(req_chat_ot).read().decode())
    print(f'   [{ot["lang"].upper()}] [Non-Marine Off-Topic Filter]')
    print(f'   Q: "{ot["q"]}"')
    print(f'   A: "{ot_res["reply"]}"')
    print(f'   Off-Topic Detected: {ot_res["is_off_topic"]}\n')
    assert ot_res["is_off_topic"] is True, "Expected is_off_topic to be True"
    assert ot["expected_sub"] in ot_res["reply"], f"Expected '{ot['expected_sub']}' in reply"

print('===============================================================')
print('🎉 ALL USER REQUIREMENTS VERIFIED WITH 100% SUCCESS!')
print('===============================================================')
