#!/usr/bin/env python3
"""
Polydime Industries — BA Team Tracker
======================================
Backend server.py  |  Python 3.x  |  No extra libraries needed
Run:  python server.py
Then open:  http://localhost:8080  (or http://<your-ip>:8080 from other devices)

All data is stored in  tracker_data.json  in the same folder.
"""

import json
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
# All of these can be overridden with environment variables, which is how
# Railway / Render (and any other host) will configure the app in production.
# Locally, if the env vars aren't set, the same defaults as before are used.

PORT        = int(os.environ.get("PORT", 8080))
HOST        = "0.0.0.0"          # accept connections from all network devices

# DATA_DIR should point at a persistent volume when deployed (e.g. Railway
# Volume mounted at /data). Defaults to the current folder for local use.
DATA_DIR    = os.environ.get("DATA_DIR", ".")
DATA_FILE   = os.path.join(DATA_DIR, "tracker_data.json")
HTML_FILE   = "polydime-ba-tracker.html"

ADMIN_PASS  = os.environ.get("ADMIN_PASS", "Sanju123")
MEMBER_PASS = os.environ.get("MEMBER_PASS", "BATeam123")

COLORS = [
    {"color": "#4F8BFF", "bg": "rgba(79,139,255,0.2)"},
    {"color": "#00D4C8", "bg": "rgba(0,212,200,0.2)"},
    {"color": "#B47FFF", "bg": "rgba(180,127,255,0.2)"},
    {"color": "#FFB347", "bg": "rgba(255,179,71,0.2)"},
    {"color": "#FF4D6A", "bg": "rgba(255,77,106,0.2)"},
    {"color": "#5CFF9D", "bg": "rgba(92,255,157,0.2)"},
]

DEFAULT_MEMBERS = [
    {"id": "m1", "name": "Alice Chen",    "role": "Business Analyst",  "color": "#4F8BFF", "bg": "rgba(79,139,255,0.2)"},
    {"id": "m2", "name": "Bob Rahman",    "role": "Senior BA",          "color": "#00D4C8", "bg": "rgba(0,212,200,0.2)"},
    {"id": "m3", "name": "Priya Nair",    "role": "Product Manager",    "color": "#B47FFF", "bg": "rgba(180,127,255,0.2)"},
    {"id": "m4", "name": "David Perera",  "role": "Junior BA",          "color": "#FFB347", "bg": "rgba(255,179,71,0.2)"},
]

# ─── Data layer ───────────────────────────────────────────────────────────────
_lock = threading.Lock()

def load_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        data = {
            "members": [dict(m, createdAt=datetime.utcnow().isoformat()) for m in DEFAULT_MEMBERS],
            "entries": []
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Request handler ──────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    # silence default access log (comment out to see all requests)
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()}  {fmt % args}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, content):
        body = content if isinstance(content, bytes) else content.encode()
        self.send_response(200)
        self.send_header("Content-Type",   "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, msg, status=400):
        self.send_json({"error": msg}, status)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    # ── routing ──────────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"

        # ── serve the HTML app ──
        if path in ("/", "/index", "/app"):
            if os.path.exists(HTML_FILE):
                with open(HTML_FILE, "rb") as f:
                    self.send_html(f.read())
            else:
                self.send_html(f"<h2>Error: {HTML_FILE} not found in server folder.</h2>".encode())
            return

        # ── API: GET /api/members ──
        if path == "/api/members":
            with _lock:
                data = load_data()
            self.send_json(data["members"])
            return

        # ── API: GET /api/entries  (optional ?memberId=xxx) ──
        if path == "/api/entries":
            qs       = parse_qs(parsed.query)
            member_id = qs.get("memberId", [None])[0]
            with _lock:
                data = load_data()
            entries = data["entries"]
            if member_id:
                entries = [e for e in entries if e.get("memberId") == member_id]
            self.send_json(entries)
            return

        # ── API: GET /api/status ──
        if path == "/api/status":
            with _lock:
                data = load_data()
            self.send_json({
                "status":   "online",
                "members":  len(data["members"]),
                "entries":  len(data["entries"]),
                "dataFile": DATA_FILE,
                "time":     datetime.utcnow().isoformat()
            })
            return

        self.send_error_json("Not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        # ── API: POST /api/members  — add a member ──
        if path == "/api/members":
            body = self.read_body()
            name = (body.get("name") or "").strip()
            if not name:
                self.send_error_json("name is required")
                return
            with _lock:
                data = load_data()
                color_idx = len(data["members"]) % len(COLORS)
                member = {
                    "id":        "m" + str(int(time.time() * 1000)),
                    "name":      name,
                    "role":      (body.get("role") or "Team Member").strip(),
                    "color":     COLORS[color_idx]["color"],
                    "bg":        COLORS[color_idx]["bg"],
                    "createdAt": datetime.utcnow().isoformat(),
                }
                data["members"].append(member)
                save_data(data)
            self.send_json(member, 201)
            return

        # ── API: POST /api/entries  — save a daily log ──
        if path == "/api/entries":
            body = self.read_body()
            member_id = (body.get("memberId") or "").strip()
            if not member_id:
                self.send_error_json("memberId is required")
                return
            with _lock:
                data = load_data()
                # Verify member exists
                member = next((m for m in data["members"] if m["id"] == member_id), None)
                if not member:
                    self.send_error_json("Member not found", 404)
                    return
                entry = {
                    "id":          "e" + str(int(time.time() * 1000)),
                    "memberId":    member_id,
                    "memberName":  member["name"],
                    "memberRole":  member["role"],
                    "date":        body.get("date", ""),
                    "project":     body.get("project", ""),
                    "tasks":       body.get("tasks", []),
                    "hours":       body.get("hours", ""),
                    "status":      body.get("status", "In Progress"),
                    "blockers":    body.get("blockers", ""),
                    "tomorrow":    body.get("tomorrow", ""),
                    "submittedAt": datetime.utcnow().isoformat(),
                }
                data["entries"].append(entry)
                save_data(data)
            self.send_json(entry, 201)
            return

        # ── API: POST /api/login  — validate credentials ──
        if path == "/api/login":
            body     = self.read_body()
            member_id = body.get("memberId", "")
            password  = body.get("password", "")

            if member_id == "__admin__":
                if password != ADMIN_PASS:
                    self.send_error_json("Incorrect admin password.", 401)
                    return
                self.send_json({"ok": True, "isAdmin": True,
                                "user": {"id": "__admin__", "name": "Administrator",
                                         "role": "Admin", "color": "#4F8BFF",
                                         "bg": "rgba(79,139,255,0.2)"}})
                return

            if password != MEMBER_PASS:
                self.send_error_json('Incorrect password.', 401)
                return

            with _lock:
                data   = load_data()
                member = next((m for m in data["members"] if m["id"] == member_id), None)
            if not member:
                self.send_error_json("Member not found.", 404)
                return
            self.send_json({"ok": True, "isAdmin": False, "user": member})
            return

        self.send_error_json("Not found", 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        parts  = parsed.path.strip("/").split("/")   # e.g. ["api","members","m1"]

        # ── API: PUT /api/members/<id>  — update a member ──
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "members":
            member_id = parts[2]
            body      = self.read_body()
            with _lock:
                data   = load_data()
                member = next((m for m in data["members"] if m["id"] == member_id), None)
                if not member:
                    self.send_error_json("Member not found", 404)
                    return
                if "name" in body: member["name"] = body["name"].strip()
                if "role" in body: member["role"] = body["role"].strip()
                save_data(data)
            self.send_json(member)
            return

        self.send_error_json("Not found", 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        parts  = parsed.path.strip("/").split("/")

        # ── API: DELETE /api/members/<id> ──
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "members":
            member_id = parts[2]
            with _lock:
                data    = load_data()
                before  = len(data["members"])
                data["members"] = [m for m in data["members"] if m["id"] != member_id]
                if len(data["members"]) == before:
                    self.send_error_json("Member not found", 404)
                    return
                # also remove their entries
                data["entries"] = [e for e in data["entries"] if e.get("memberId") != member_id]
                save_data(data)
            self.send_json({"deleted": member_id})
            return

        # ── API: DELETE /api/entries/<id> ──
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "entries":
            entry_id = parts[2]
            with _lock:
                data   = load_data()
                before = len(data["entries"])
                data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
                if len(data["entries"]) == before:
                    self.send_error_json("Entry not found", 404)
                    return
                save_data(data)
            self.send_json({"deleted": entry_id})
            return

        self.send_error_json("Not found", 404)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)

    print("=" * 54)
    print("  Polydime Industries — BA Team Tracker")
    print("=" * 54)
    print(f"  Server running on port {PORT}")
    print(f"  Local:    http://localhost:{PORT}")
    print()
    print("  From other devices on same Wi-Fi, use:")
    print(f"  http://<YOUR-LAPTOP-IP>:{PORT}")
    print()
    print("  Data file:", os.path.abspath(DATA_FILE))
    if os.environ.get("ADMIN_PASS") is None:
        print()
        print("  WARNING: ADMIN_PASS/MEMBER_PASS env vars not set — using")
        print("  built-in defaults. Set them before deploying publicly.")
    print()
    print("  Passwords:")
    print(f"    Admin  : {ADMIN_PASS}")
    print(f"    Members: {MEMBER_PASS}")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 54)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()
