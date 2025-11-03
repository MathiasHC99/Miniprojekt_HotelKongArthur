from flask import Flask, jsonify, request
import sqlite3, pandas as pd, os

app = Flask(__name__)

DB_FILE = "guest.db"
CSV_FILE = "../../NamesRoomsWithMonths4.csv"  # samme datafil som room

#Localhost URL for testing: http://localhost:5003/
# Endpoints: 
# guests
# guests/<int:guest_id>
# guests/summary


# ---------- DATABASE OPSÆTNING ----------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                family_name TEXT,
                country TEXT
            );
        """)
        conn.commit()


def seed_from_csv():
    """Indlæs gæst-data fra CSV (kun navn og land)."""
    if not os.path.exists(CSV_FILE):
        print(f"⚠️ CSV not found: {CSV_FILE}")
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM guests")
        count = cur.fetchone()[0]

        if count == 0:
            print("📥 Indlæser gæst-data fra CSV...")
            df = pd.read_csv(CSV_FILE, sep=";")
            df.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df.columns]

            # Sørg for at kolonnenavne matcher CSV'en
            rename_map = {
                "first_name": "first_name",
                "family_name": "family_name",
                "country": "country"
            }
            df.rename(columns=rename_map, inplace=True)

            # Fjern dubletter (samme navn/land flere gange)
            df_unique = df[["first_name", "family_name", "country"]].drop_duplicates()

            df_unique.to_sql("guests", conn, if_exists="append", index=False)
            print(f"✅ Imported {len(df_unique)} guests into SQLite database.")
        else:
            print("✅ Guests already loaded.")


# ---------- ENDPOINTS ----------

@app.get("/guests")
def all_guests():
    conn = get_db()
    rows = conn.execute("SELECT * FROM guests").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/guests/<int:guest_id>")
def get_guest(guest_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM guests WHERE id=?", (guest_id,)).fetchone()
    return jsonify(dict(row)) if row else ({"error": "Guest not found"}, 404)


@app.post("/guests")
def create_guest():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO guests (first_name, family_name, country)
            VALUES (?, ?, ?)
        """, (data["first_name"], data["family_name"], data["country"]))
        conn.commit()
    return {"status": "created"}, 201


@app.delete("/guests/<int:guest_id>")
def delete_guest(guest_id):
    with get_db() as conn:
        conn.execute("DELETE FROM guests WHERE id=?", (guest_id,))
        conn.commit()
    return {"status": "deleted"}, 200


# ---------- ANALYTICS BASERET PÅ ROOM_RENTALS ----------

ROOM_DB = "../room/room.db"

def get_room_df():
    """Hent room_rentals som DataFrame."""
    if not os.path.exists(ROOM_DB):
        print("⚠️ Room database not found.")
        return pd.DataFrame()
    conn = sqlite3.connect(ROOM_DB)
    df = pd.read_sql("SELECT * FROM room_rentals", conn)
    conn.close()
    return df


@app.get("/guests/summary")
def guest_summary():
    """
    Returnerer:
      - total_guests (antal i guests.db)
      - top_countries (fra guests.db)
      - by_country / by_season / by_country_roomtype (fra room_rentals)
    """
    # --- Data fra guests.db (navne & antal) ---
    conn = get_db()
    df_guests = pd.read_sql("SELECT country FROM guests", conn)
    conn.close()

    total_guests = len(df_guests)
    top_countries = df_guests["country"].value_counts().to_dict()

    # --- Data fra room_rentals (revenueanalyse) ---
    df_room = get_room_df()
    if df_room.empty:
        return jsonify({
            "summary": {
                "total_guests": total_guests,
                "unique_countries": len(df_guests["country"].unique()),
                "avg_stay_days": 0,
                "top_country": None
            },
            "by_country": {},
            "by_season": {},
            "by_country_roomtype": {}
        })

    df_room["revenue"] = df_room["price"] * df_room["days_rented"]

    # Gns. opholdstid
    avg_stay = round(df_room["days_rented"].mean(), 1)

    # Omsætning pr. land
    by_country = (
        df_room.groupby("country")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    # Omsætning pr. sæson og land
    by_season = (
        df_room.groupby(["season", "country"])["revenue"]
        .sum()
        .reset_index()
    )
    result_season = {}
    for _, row in by_season.iterrows():
        s = str(row["season"]).strip()
        c = str(row["country"]).strip()
        r = float(row["revenue"])
        result_season.setdefault(s, {})[c] = r

    # Land × værelsestype
    by_country_room = (
        df_room.groupby(["country", "room_type"])["revenue"]
        .sum()
        .reset_index()
    )
    result_heat = {}
    for _, row in by_country_room.iterrows():
        c = str(row["country"]).strip()
        rt = str(row["room_type"]).strip()
        r = float(row["revenue"])
        result_heat.setdefault(c, {})[rt] = r

    top_country = max(by_country, key=by_country.get)

    return jsonify({
        "summary": {
            "total_guests": int(total_guests),
            "unique_countries": int(df_room["country"].nunique()),
            "avg_stay_days": avg_stay,
            "top_country": top_country
        },
        "by_country": by_country,
        "by_season": result_season,
        "by_country_roomtype": result_heat
    })







# ---------- MAIN ----------

if __name__ == "__main__":
    init_db()
    seed_from_csv()
    app.run(host="0.0.0.0", port=5003)
