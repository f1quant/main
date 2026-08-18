import base64
import json
import zlib
import requests
import fastf1

YEAR = 2026
EVENT = "Australian Grand Prix"   # change if needed
SESSION = "R"                     # R, Q, FP1, FP2, FP3, SQ, S, etc.

fastf1.Cache.enable_cache("fastf1_cache")

# Build/get the session path
session = fastf1.get_session(YEAR, EVENT, SESSION)

# In some versions/api states, api_path may only be populated after a lightweight load
if not getattr(session, "api_path", None):
    session.load(laps=False, telemetry=False, weather=False, messages=False)

api_path = session.api_path
stream_url = f"https://livetiming.formula1.com{api_path}CarData.z.jsonStream"

resp = requests.get(stream_url, timeout=30)
resp.raise_for_status()

def decode_payload(payload: str):
    payload = payload.strip()

    # Sometimes the payload is quoted JSON text
    if payload.startswith('"') and payload.endswith('"'):
        payload = json.loads(payload)

    # Non-zipped feeds can already be JSON
    if payload.startswith("{") or payload.startswith("["):
        return json.loads(payload)

    raw = base64.b64decode(payload)

    # CarData.z is compressed; raw DEFLATE is the usual case
    for wbits in (-zlib.MAX_WBITS, zlib.MAX_WBITS):
        try:
            return json.loads(zlib.decompress(raw, wbits))
        except zlib.error:
            pass

    raise ValueError("Could not decompress payload")

records = []
for line in resp.text.splitlines():
    line = line.strip()
    if not line:
        continue

    # F1 jsonStream lines start with a 12-char session timestamp, e.g. 00:00:12:345
    ts = line[:12]
    payload = line[12:]
    data = decode_payload(payload)
    records.append({"session_time": ts, "data": data})

for ri, record in enumerate(records):
    if ri != 3000: continue
    for ei, entry in enumerate(record["data"]["Entries"]):
        for car_num, car_data in entry["Cars"].items():
            for channel, channel_data in car_data["Channels"].items():
                print(f"Record {ri}, Entry {ei}, Car {car_num}, Channel {channel}: {channel_data}")
    
# print(json.dumps(records[0], indent=2)[:2000])