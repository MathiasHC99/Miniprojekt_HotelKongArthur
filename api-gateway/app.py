from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

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
