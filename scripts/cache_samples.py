"""Fetch REAL weather + transit samples once and cache them into data/ so the
offline baseline uses authentic data (no keys needed at run time).

Run:  TRANSITLAND_KEY=... python scripts/cache_samples.py
(Weather needs no key. Transit sample is skipped if TRANSITLAND_KEY is unset.)
"""
import json, os, urllib.request, urllib.parse, pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "night-out-curator/0.1"}

def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())


LAT, LON = 33.4255, -111.9400
DATE = "2026-09-11"


wq = urllib.parse.urlencode({
    "latitude": LAT, "longitude": LON,
    "hourly": "temperature_2m,precipitation_probability,weather_code",
    "timezone": "America/Phoenix", "start_date": DATE, "end_date": DATE,
})
w = get("https://api.open-meteo.com/v1/forecast?" + wq)
weather = {"date": DATE, "lat": LAT, "lon": LON,
           "hourly": {t: {"temp_c": tc, "precip_prob": pp, "weather_code": wc}
                      for t, tc, pp, wc in zip(w["hourly"]["time"],
                                               w["hourly"]["temperature_2m"],
                                               w["hourly"]["precipitation_probability"],
                                               w["hourly"]["weather_code"])}}
(DATA / "weather_sample.json").write_text(json.dumps(weather, indent=2))
print(f"cached weather_sample.json ({len(weather['hourly'])} hourly points)")


key = os.environ.get("TRANSITLAND_KEY")
if key:
    def rt(k): return k.rstrip()
    pairs = [
        ("asu_to_downtown", 33.4242, -111.9281, 33.4484, -112.0740),
        ("millave_short",   33.4255, -111.9400, 33.4300, -111.9250),
    ]
    transit = {}
    for name, flat, flon, tlat, tlon in pairs:
        p = {"fromPlace": f"{flat},{flon}", "toPlace": f"{tlat},{tlon}",
             "date": DATE, "time": "19:00:00", "maxItineraries": 1, "api_key": key}
        try:
            r = get("https://transit.land/api/v2/routing/otp/plan?" + urllib.parse.urlencode(p))
            it = (r.get("plan") or {}).get("itineraries", [])
            if it:
                i = it[0]
                transit[name] = {
                    "from": [flat, flon], "to": [tlat, tlon],
                    "total_min": round(i.get("duration", 0) / 60),
                    "walk_min": round(i.get("walkTime", 0) / 60),
                    "transit_min": round(i.get("transitTime", 0) / 60),
                    "legs": [{"mode": l.get("mode"),
                              "route": l.get("route") or l.get("routeShortName") or "",
                              "from": (l.get("from") or {}).get("name"),
                              "to": (l.get("to") or {}).get("name"),
                              "min": round(l.get("duration", 0) / 60)}
                             for l in i.get("legs", [])],
                }
                print(f"cached transit '{name}': {transit[name]['total_min']} min")
        except Exception as e:
            print(f"transit '{name}' failed: {e}")
    (DATA / "transit_sample.json").write_text(json.dumps(transit, indent=2))
    print("wrote transit_sample.json")
else:
    print("TRANSITLAND_KEY unset — skipping transit cache (offline tool will use a fallback estimate).")
