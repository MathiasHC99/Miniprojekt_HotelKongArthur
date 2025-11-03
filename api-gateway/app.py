from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# ---------- KONFIGURATION ----------
SERVICES = {
    "room": "http://room_service:5001",
    "bar": "http://bar_service:5002",
    "guest": "http://guest_service:5003",
    "reservation": "http://reservation_service:5004",
    "analytics": "http://analytics_service:5005"
}

ANALYTICS_SERVICE = "http://analytics_service:5005"
TIMEOUT = 15  # sekunder


# ---------- HJÆLPEFUNKTIONER ----------

def forward_request(service_key, path):
    """Videresend request til korrekt service baseret på service_key."""
    base_url = SERVICES.get(service_key)
    if not base_url:
        return jsonify({"error": f"Service '{service_key}' not found"}), 404

    # 🔧 Juster path baseret på service
    if service_key == "analytics":
        # Hvis path IKKE allerede starter med 'analytics/', tilføj det
        if not path.startswith("analytics/"):
            path = f"analytics/{path}"
    elif service_key == "bar":
        if not path.startswith("bar/"):
            path = f"bar/{path}"
    elif service_key == "guest":
        if not path.startswith("guests/"):
            path = f"guests/{path}"
    elif service_key == "reservation":
        if not path.startswith("reservations/"):
            path = f"reservations/{path}"
    elif service_key == "room":
        if not path.startswith("rooms/"):
            path = f"rooms/{path}"

    target_url = f"{base_url}/{path}"
    method = request.method.lower()

    try:
        if method == "get":
            resp = requests.get(target_url, params=request.args, timeout=TIMEOUT)
        elif method == "post":
            resp = requests.post(target_url, json=request.get_json(), timeout=TIMEOUT)
        elif method == "delete":
            resp = requests.delete(target_url, timeout=TIMEOUT)
        else:
            return jsonify({"error": "Unsupported HTTP method"}), 405

        return jsonify(resp.json()), resp.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Gateway timeout or connection error to {target_url}",
            "details": str(e)
        }), 504

# ---------- ROUTES ----------

@app.route("/")
def index():
    return jsonify({
        "message": "API Gateway for Hotel Kong Arthur",
        "services": list(SERVICES.keys()),
        "example": "/api/room/rooms/revenue/total"
    })


@app.route("/api/<service>/<path:path>", methods=["GET", "POST", "DELETE"])
def proxy(service, path):
    """Generisk proxy der sender kald videre til microservice."""
    return forward_request(service, path)




@app.route("/api/analytics/overview", methods=["GET"])
def get_analytics_overview():
    try:
        resp = requests.get(f"{ANALYTICS_SERVICE}/analytics/overview", timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 502







# ---------- HEALTH CHECK ----------
from datetime import datetime
import requests

@app.get("/api/health")
def gateway_health():
    """Health check for API Gateway + downstream services."""
    statuses = {}
    for name, url in SERVICES.items():
        try:
            # Analytics har sit eget health-path
            health_path = "/analytics/health" if name == "analytics" else "/health"
            r = requests.get(f"{url}{health_path}", timeout=5)
            statuses[name] = "ok" if r.status_code == 200 else f"error ({r.status_code})"
        except Exception as e:
            statuses[name] = f"unreachable ({e})"

    return jsonify({
        "service": "api_gateway",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": statuses
    })



# ---------- MAIN ----------

if __name__ == "__main__":
    print("API Gateway ruller derudaf på port 8000 ...")
    app.run(host="0.0.0.0", port=8000, threaded=True)
