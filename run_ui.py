"""Local-only browser interface; credentials stay in the Python process."""
import argparse
import json
import os
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from datetime import date, datetime

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")
from multi_agent import MultiAgentRunner
from discovery import AREAS, DiscoveryError, discover_venues, requested_cuisine
from tools import search_venues
from google_maps import PHOENIX, google_discovery

RUN_LOCK = threading.Lock()


class UIRequest(BaseModel):
    request: str = Field(min_length=1, max_length=2000)
    stop_types: list[Literal["dinner", "dessert", "cafe", "bar", "after"]] = Field(min_length=1, max_length=4)
    budget_pp: float = Field(gt=0, le=500)
    party_size: int = Field(ge=1, le=20)
    target_hour: int = Field(ge=0, le=23)
    max_walk_m: int = Field(ge=0, le=5000)
    allow_transit: bool = True
    mood: Literal["chill", "lively", "quiet", "casual", "romantic", ""] = "chill"
    vegan_required: bool = False
    mock: bool = False
    max_attempts: int = Field(default=8, ge=1, le=8)
    data_mode: Literal["live", "fixture"] = "fixture"
    search_area: Literal["tempe", "phoenix", "metro"] = "tempe"
    radius_m: int = Field(default=5000, ge=500, le=30000)
    candidate_limit: int = Field(default=60, ge=1, le=120)
    cuisine: Literal["", "indian", "italian", "mexican", "chinese", "thai", "japanese", "mediterranean", "american"] = ""
    venue_provider: Literal["geoapify", "google"] = "geoapify"
    outing_date: date = Field(default_factory=lambda: datetime.now(PHOENIX).date())


def run_request(payload, on_progress=None):
    request = UIRequest.model_validate(payload)
    values = request.model_dump(mode="json")
    data_mode = values.pop("data_mode")
    area = AREAS[values.pop("search_area")]
    text = values.pop("request")
    constraints = {key: value for key, value in values.items() if key not in {"mock", "max_attempts"}}
    constraints["area"] = area
    constraints["cuisine"] = requested_cuisine(text, request.cuisine)
    scenario = {"name": "browser_run", "request": text, "constraints": constraints}
    runner = MultiAgentRunner(mock=request.mock, max_attempts=request.max_attempts, live_discovery=data_mode == "live")
    result = runner.run(scenario, on_progress=on_progress)
    result["display_source"] = "New run"
    return result


def browse_request(payload):
    request = UIRequest.model_validate(payload)
    area = AREAS[request.search_area]
    if request.data_mode == "live":
        args = (["dinner", "dessert", "cafe", "bar"], area["lat"], area["lon"], request.radius_m,
            request.candidate_limit, requested_cuisine(request.request, request.cuisine))
        result = google_discovery(*args, area_name=area["name"]) if request.venue_provider == "google" else discover_venues(*args)
    else:
        venues = []
        for kind in ["dinner", "after"]:
            venues.extend(search_venues.invoke({"category": kind, "near_lat": area["lat"],
                                                "near_lon": area["lon"], "radius_m": request.radius_m}))
        for venue in venues:
            venue.update(source="Fixture catalog", verification="Synthetic annotations; branch unverified")
        result = {"venues": venues, "source": "Fixture catalog", "matching_count": len(venues),
                  "returned_count": len(venues), "truncated": False,
                  "coverage_note": "Reproducible pilot fixtures, not current business data."}
    return {**result, "area": area, "data_mode": request.data_mode}


class UIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def reply(self, status, body, content_type="application/json"):
        data = json.dumps(body, allow_nan=False).encode("utf-8") if content_type == "application/json" else body
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)

    def local_request(self):
        hostname = urlparse("http://" + self.headers.get("Host", "")).hostname
        origin = self.headers.get("Origin")
        return hostname in {"127.0.0.1", "localhost"} and (
            not origin or origin == "http://" + self.headers.get("Host", ""))

    def do_GET(self):
        if not self.local_request():
            self.reply(403, {"error": "Local access only."})
            return
        path = urlparse(self.path).path
        if path == "/api/config":
            self.reply(200, {"provider": os.getenv("LLM_PROVIDER", "openai"),
                             "model": os.getenv("LLM_MODEL", "default"),
                             "region": os.getenv("AWS_REGION", ""), "stop_limit": 4,
                             "maps_embed_key": os.getenv("GOOGLE_MAPS_EMBED_KEY", ""),
                             "discovery_provider": "Google Maps" if os.getenv("GOOGLE_MAPS_API_KEY") else "Geoapify" if os.getenv("GEOAPIFY_KEY") else "OpenStreetMap / Overpass"})
            return
        if path == "/api/sample":
            sample = ROOT / "artifacts" / "bedrock_flow.json"
            if sample.exists():
                result = json.loads(sample.read_text(encoding="utf-8"))
                result["display_source"] = "Saved run"
                self.reply(200, result)
            else:
                self.reply(200, {"status": "empty"})
            return
        files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                 "/style.css": ("style.css", "text/css"), "/theme.css": ("theme.css", "text/css")}
        if path not in files:
            self.reply(404, {"error": "Not found."})
            return
        name, content_type = files[path]
        self.reply(200, (ROOT / "ui" / name).read_bytes(), content_type)

    def do_POST(self):
        if not self.local_request():
            self.reply(403, {"error": "Local access only."})
            return
        if self.path not in {"/api/run", "/api/venues"}:
            self.reply(404, {"error": "Not found."})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.reply(415, {"error": "JSON request required."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                self.reply(413, {"error": "Request size is invalid."})
                return
            payload = json.loads(self.rfile.read(length))
            UIRequest.model_validate(payload)
        except (ValueError, ValidationError):
            self.reply(400, {"error": "Check the requested stops, budget, time and party size."})
            return
        if not RUN_LOCK.acquire(blocking=False):
            self.reply(409, {"error": "Another run is in progress. Try again after it finishes."})
            return
        if self.path == "/api/run" and "application/x-ndjson" in self.headers.get("Accept", ""):
            self.stream_run(payload)
            return
        try:
            self.reply(200, browse_request(payload) if self.path == "/api/venues" else run_request(payload))
        except DiscoveryError as error:
            self.reply(503, {"error": str(error)})
        except ValueError:
            self.reply(400, {"error": "Choose Fixture catalog for Mock planning, or browse live places without LLM calls."})
        except Exception:
            self.reply(502, {"error": "The planner could not finish. Check provider access or try mock mode."})
        finally:
            RUN_LOCK.release()

    def stream_run(self, payload):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()

        def emit(event):
            self.wfile.write((json.dumps(event, allow_nan=False) + "\n").encode("utf-8"))
            self.wfile.flush()

        try:
            emit({"type": "progress", "node": "Starting", "detail": "Request accepted"})
            result = run_request(payload, on_progress=emit)
            emit({"type": "result", "result": result})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except DiscoveryError as error:
            emit({"type": "error", "error": str(error)})
        except TimeoutError:
            emit({"type": "error", "error": "Planning exceeded its time budget. Narrow the search or use fewer stops."})
        except Exception:
            emit({"type": "error", "error": "Planning could not finish. Check provider access and available venue evidence."})
        finally:
            self.close_connection = True
            RUN_LOCK.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), UIHandler)
    print(f"Night-Out Curator: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()