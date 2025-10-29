from flask import Flask, request, jsonify
from datetime import date
import psycopg2, os

app = Flask(__name__)

def db():
    return psycopg2.connect(
        host=os.getenv("PGHOST","db"),
        dbname=os.getenv("PGDATABASE","arthur"),
        user=os.getenv("PGUSER","arthur"),
        password=os.getenv("PGPASSWORD","arthur"),
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/reservations")
def list_reservations():
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id, guest_id, room_id, check_in, check_out, price_dkk
                       FROM reservation.reservations
                       ORDER BY check_in DESC LIMIT 200""")
        rows = [dict(id=r[0], guest_id=r[1], room_id=r[2],
                     check_in=str(r[3]), check_out=str(r[4]), price_dkk=float(r[5])) for r in cur.fetchall()]
    return jsonify(rows)

@app.post("/reservations")
def create_reservation():
    data = request.json
    with db() as conn, conn.cursor() as cur:
        cur.execute("""INSERT INTO reservation.reservations
                       (guest_id, room_id, check_in, check_out, price_dkk)
                       VALUES (%s,%s,%s,%s,%s) RETURNING id""",
                    (data["guest_id"], data["room_id"], data["check_in"], data["check_out"], data["price_dkk"]))
        new_id = cur.fetchone()[0]
        conn.commit()
    return {"id": new_id}, 201

@app.get("/reservations/<int:res_id>")
def get_reservation(res_id):
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id, guest_id, room_id, check_in, check_out, price_dkk
                       FROM reservation.reservations WHERE id=%s""", (res_id,))
        r = cur.fetchone()
        if not r: return {"error":"not found"}, 404
        return dict(id=r[0], guest_id=r[1], room_id=r[2],
                    check_in=str(r[3]), check_out=str(r[4]), price_dkk=float(r[5]))
