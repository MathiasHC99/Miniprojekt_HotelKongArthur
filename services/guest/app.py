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


@app.get("/guests/summary")
def guest_summary():
    """Returner antal gæster pr. land (til Analytics)."""
    conn = get_db()
    df = pd.read_sql("SELECT country FROM guests", conn)

    summary = (
        df["country"]
        .value_counts()
        .head(10)
        .to_dict()
    )

    total_guests = len(df)
    return jsonify({
        "total_guests": total_guests,
        "top_countries": summary
    })


# ---------- MAIN ----------

if __name__ == "__main__":
    init_db()
    seed_from_csv()
    app.run(host="0.0.0.0", port=5003)
