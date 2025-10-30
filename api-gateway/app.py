from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)
from flask_cors import CORS
CORS(app)


SERVICES = {
  "reservation": os.getenv("RESERVATION_URL","http://reservation:5000"),
  "room": os.getenv("ROOM_URL","http://room:5000"),
  "guest": os.getenv("GUEST_URL","http://guest:5000"),
  "review": os.getenv("REVIEW_URL","http://review:5000"),
  "bar": os.getenv("BAR_URL","http://bar:5000"),
  "analytics": os.getenv("ANALYTICS_URL","http://analytics:5000"),
}

# Offentlige endpoints til frontend
@app.get("/kpis/rooms")
def rooms_kpis():
    return requests.get(f"{SERVICES['analytics']}/kpis/rooms").json()

@app.get("/kpis/top")
def top_kpis():
    return requests.get(f"{SERVICES['analytics']}/kpis/top").json()

@app.get("/bar/summary")
def bar_summary():
    return requests.get(f"{SERVICES['bar']}/summary").json()

# _internal aggregator til analytics
@app.get("/_internal/reservations")
def _int_reservations():
    return requests.get(f"{SERVICES['reservation']}/reservations").json()

@app.get("/_internal/rooms")
def _int_rooms():
    return requests.get(f"{SERVICES['room']}/rooms").json()

@app.get("/_internal/denormalized_sales")
def _int_sales():
    # join-lignende aggregering via gateway (reservation + room + guest)
    res = requests.get(f"{SERVICES['reservation']}/reservations").json()
    rooms = {r["id"]: r for r in requests.get(f"{SERVICES['room']}/rooms").json()}
    guests = {g["id"]: g for g in requests.get(f"{SERVICES['guest']}/guests").json()}
    out=[]
    for r in res:
        room = rooms.get(r["room_id"],{})
        guest = guests.get(r["guest_id"],{})
        out.append({
          "price_dkk": r["price_dkk"],
          "room_type": room.get("type","Unknown"),
          "country": guest.get("country","Unknown")
        })
    return jsonify(out)


# CRUD ENDPOINTS (til frontend)

def _forward(method, service, path, **kwargs):
    url = f"{SERVICES[service]}{path}"
    resp = requests.request(method, url, timeout=5, **kwargs)
    return (resp.json() if resp.content else {}), resp.status_code


# --- Reservation CRUD ---
@app.get("/reservations")
def gw_list_res():
    d, s = _forward("GET", "reservation", "/reservations")
    return jsonify(d), s

@app.post("/reservations")
def gw_create_res():
    d, s = _forward("POST", "reservation", "/reservations", json=request.json)
    return jsonify(d), s

@app.get("/reservations/<int:id>")
def gw_get_res(id):
    d, s = _forward("GET", "reservation", f"/reservations/{id}")
    return jsonify(d), s

@app.put("/reservations/<int:id>")
def gw_update_res(id):
    d, s = _forward("PUT", "reservation", f"/reservations/{id}", json=request.json)
    return jsonify(d), s

@app.delete("/reservations/<int:id>")
def gw_delete_res(id):
    d, s = _forward("DELETE", "reservation", f"/reservations/{id}")
    return jsonify(d), s


# --- Room CRUD ---
@app.get("/rooms")
def gw_list_rooms():
    d, s = _forward("GET", "room", "/rooms")
    return jsonify(d), s

@app.post("/rooms")
def gw_create_room():
    d, s = _forward("POST", "room", "/rooms", json=request.json)
    return jsonify(d), s

@app.put("/rooms/<int:id>")
def gw_update_room(id):
    d, s = _forward("PUT", "room", f"/rooms/{id}", json=request.json)
    return jsonify(d), s

@app.delete("/rooms/<int:id>")
def gw_delete_room(id):
    d, s = _forward("DELETE", "room", f"/rooms/{id}")
    return jsonify(d), s


# --- Guest CRUD ---
@app.get("/guests")
def gw_list_guests():
    d, s = _forward("GET", "guest", "/guests")
    return jsonify(d), s

@app.post("/guests")
def gw_create_guest():
    d, s = _forward("POST", "guest", "/guests", json=request.json)
    return jsonify(d), s

@app.put("/guests/<int:id>")
def gw_update_guest(id):
    d, s = _forward("PUT", "guest", f"/guests/{id}", json=request.json)
    return jsonify(d), s

@app.delete("/guests/<int:id>")
def gw_delete_guest(id):
    d, s = _forward("DELETE", "guest", f"/guests/{id}")
    return jsonify(d), s

@app.get("/")
def index():
    return jsonify({
        "service": "api-gateway",
        "endpoints": [
            "/reservations [GET,POST]",
            "/reservations/<id> [GET,PUT,DELETE]",
            "/rooms [GET,POST] (hvis du har room-service)",
            "/guests [GET,POST] (hvis du har guest-service)",
            "/kpis/rooms [GET]",
            "/kpis/top [GET]",
            "/_internal/reservations [GET]",
            "/_internal/rooms [GET]"
        ]
    })

@app.get("/health")
def health():
    return {"gateway": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
