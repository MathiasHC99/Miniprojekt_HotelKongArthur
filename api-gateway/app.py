from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# ---------- KONFIGURATION ----------
SERVICES = {
    "room": "http://localhost:5001",
    "bar": "http://localhost:5002",
    "guest": "http://localhost:5003",
    "reservation": "http://localhost:5004",
    "analytics": "http://localhost:5005"
}

TIMEOUT = 15  # sekunder


# ---------- HJÆLPEFUNKTIONER ----------

def forward_request(service_key, path):
    """Videresend request til korrekt service baseret på service_key."""
    base_url = SERVICES.get(service_key)
    if not base_url:
        return jsonify({"error": f"Service '{service_key}' not found"}), 404

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
        return jsonify({"error": f"Gateway timeout or connection error to {target_url}", "details": str(e)}), 504


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


# ---------- MAIN ----------

if __name__ == "__main__":
    print("API Gateway ruller derudaf på port 8000 ...")
    app.run(host="0.0.0.0", port=8000, threaded=True)
