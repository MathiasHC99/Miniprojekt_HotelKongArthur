from flask import Flask, request, jsonify
import sqlite3, os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "reservations.db")

# --- Helper til DB ---
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- INIT DB ---
def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            price_dkk REAL NOT NULL
        )
        """)
        conn.commit()
init_db()

# --- ROUTES ---
@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/reservations")
def list_res():
    with db() as conn:
        res = conn.execute("SELECT * FROM reservations").fetchall()
        return jsonify([dict(r) for r in res])

@app.post("/reservations")
def create_res():
    data = request.json
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO reservations (guest_id, room_id, check_in, check_out, price_dkk)
            VALUES (?, ?, ?, ?, ?)
        """, (data["guest_id"], data["room_id"], data["check_in"], data["check_out"], data["price_dkk"]))
        conn.commit()
        return {"id": cur.lastrowid}, 201

@app.get("/reservations/<int:id>")
def get_res(id):
    with db() as conn:
        r = conn.execute("SELECT * FROM reservations WHERE id = ?", (id,)).fetchone()
        if not r: return {"error":"not found"}, 404
        return dict(r)

@app.put("/reservations/<int:id>")
def update_res(id):
    data = request.json
    with db() as conn:
        cur = conn.execute("""
            UPDATE reservations
            SET guest_id=?, room_id=?, check_in=?, check_out=?, price_dkk=?
            WHERE id=?
        """, (data["guest_id"], data["room_id"], data["check_in"], data["check_out"], data["price_dkk"], id))
        conn.commit()
        if cur.rowcount == 0: return {"error":"not found"}, 404
    return {"id": id}

@app.delete("/reservations/<int:id>")
def delete_res(id):
    with db() as conn:
        cur = conn.execute("DELETE FROM reservations WHERE id=?", (id,))
        conn.commit()
        if cur.rowcount == 0: return {"error":"not found"}, 404
    return {"deleted": id}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
