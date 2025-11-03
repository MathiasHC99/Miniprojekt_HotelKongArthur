from flask import Flask, jsonify, request
import sqlite3, os, pandas as pd

app = Flask(__name__)

DB_FILE = "room.db"
CSV_FILE = "../../NamesRoomsWithMonths4.csv"  # tilpas hvis sti er anderledes



#Localhost URL for testing: http://localhost:5001/rooms/summary
# Endpoints: 
# rooms/
# rooms/<int:room_id>
# rooms/summary
# rooms/revenue/by_season
# rooms/revenue/by_roomtype
# rooms/bookings/by_month_and_type
# rooms/revenue/by_roomtype_and_season
# rooms/revenue/by_country
# rooms/revenue/total



# ---------- Database forbindelser ----------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS room_rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                family_name TEXT,
                country TEXT,
                room_type TEXT,
                days_rented INTEGER,
                season TEXT,
                month TEXT,
                monthnumber INTEGER,
                price REAL,
                adjusteddays REAL
            );
        """)
        conn.commit()


# ---------- Indlæs CSV ved første start ----------
def seed_from_csv():
    if not os.path.exists(CSV_FILE):
        print(f"⚠️ CSV file not found: {CSV_FILE}")
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM room_rentals")
        count = cur.fetchone()[0]

        if count == 0:
            print("Indlæser CSV...")
            df = pd.read_csv(CSV_FILE, sep=";")  # <-- vigtigt!
            print("Kolonner fundet:", df.columns.tolist())

            # Gør kolonnenavne ens
            df.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df.columns]
            print("Efter rensning:", df.columns.tolist())

            # Indsæt i SQLite
            df.to_sql("room_rentals", conn, if_exists="append", index=False)
            print(f"Imported {len(df)} rows into room_rentals table.")
        else:
            print("Database already seeded.")

# ---------- API Endpoints ----------
@app.get("/rooms")
def get_all_rooms():
    conn = get_db()
    rows = conn.execute("SELECT * FROM room_rentals LIMIT 100").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/rooms/<int:room_id>")
def get_room(room_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM room_rentals WHERE id=?", (room_id,)).fetchone()
    if not row:
        return {"error": "Room not found"}, 404
    return jsonify(dict(row))

@app.get("/rooms/summary")
def get_summary():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM room_rentals", conn)

    summary = {
        "total_bookings": len(df),
        "average_price": round(df["price"].mean(), 2),
        "avg_days_rented": round(df["days_rented"].mean(), 2),
        "top_room_types": (
            df.groupby("room_type")["price"]
              .sum()
              .sort_values(ascending=False)
              .head(5)
              .to_dict()
        ),
        "top_countries": (
            df.groupby("country")["price"]
              .sum()
              .sort_values(ascending=False)
              .head(5)
              .to_dict()
        ),
    }
    return jsonify(summary)

@app.get("/rooms/revenue/by_roomtype")
def revenue_by_roomtype():
    conn = get_db()
    df = pd.read_sql("SELECT room_type, price FROM room_rentals", conn)
    grouped = (
        df.groupby("room_type")["price"]
          .sum()
          .sort_values(ascending=False)
          .round(2)
          .to_dict()
    )
    return jsonify(grouped)


@app.get("/rooms/bookings/by_month_and_type")
def bookings_by_month_and_type():
    """Returnerer antal udlejede værelser pr. måned og værelsetype."""
    conn = get_db()
    df = pd.read_sql("""
        SELECT 
            room_type,
            monthnumber AS month,
            COUNT(*) AS total_bookings
        FROM room_rentals
        WHERE room_type IS NOT NULL AND monthnumber IS NOT NULL
        GROUP BY room_type, month
        ORDER BY month ASC
    """, conn)
    conn.close()

    # Konverter til struktur: {room_type: {month: count}}
    result = {}
    for _, row in df.iterrows():
        rt = row["room_type"]
        month = int(row["month"])
        count = int(row["total_bookings"])
        result.setdefault(rt, {})[month] = count

    return result



@app.get("/rooms/revenue/by_roomtype_and_season")
def revenue_by_roomtype_and_season():
    """Returnerer omsætning pr. værelsestype fordelt på sæsoner."""
    conn = get_db()
    df = pd.read_sql("""
        SELECT 
            room_type, 
            season, 
            SUM(price * days_rented) AS revenue
        FROM room_rentals
        WHERE room_type IS NOT NULL AND season IS NOT NULL
        GROUP BY room_type, season
    """, conn)
    conn.close()

    result = {}
    for _, row in df.iterrows():
        season = str(row["season"]).strip()
        room = str(row["room_type"]).strip()
        revenue = float(row["revenue"]) if row["revenue"] is not None else 0.0

        # Spring over rækker med tomme værdier
        if not season or not room:
            continue

        # Opret dictionarystruktur
        result.setdefault(season, {})[room] = revenue

    return result


@app.get("/rooms/revenue/by_season")
def revenue_by_season():
    conn = get_db()
    df = pd.read_sql("SELECT season, price FROM room_rentals", conn)
    grouped = (
        df.groupby("season")["price"]
          .sum()
          .sort_values(ascending=False)
          .round(2)
          .to_dict()
    )
    return jsonify(grouped)

@app.get("/rooms/revenue/by_country")
def revenue_by_country():
    conn = get_db()
    df = pd.read_sql("SELECT country, price FROM room_rentals", conn)
    grouped = (
        df.groupby("country")["price"]
          .sum()
          .sort_values(ascending=False)
          .round(2)
          .to_dict()
    )
    return jsonify(grouped)

@app.get("/rooms/revenue/total")
def total_revenue():
    conn = get_db()
    df = pd.read_sql("SELECT price FROM room_rentals", conn)
    total = float(df["price"].sum())
    return jsonify({"total_revenue_dkk": round(total, 2)})

@app.post("/rooms")
def create_room():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO room_rentals (first_name, family_name, country, room_type, days_rented,
                                      season, month, month_number, price, adjusted_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["first_name"], data["family_name"], data["country"],
            data["room_type"], data["days_rented"], data["season"],
            data["month"], data["month_number"], data["price"], data["adjusted_days"]
        ))
        conn.commit()
    return {"status": "created"}, 201

if __name__ == "__main__":
    init_db()
    seed_from_csv()
    app.run(host="0.0.0.0", port=5001)


