from flask import Flask, jsonify, request
import sqlite3, pandas as pd, os
from datetime import datetime, timedelta

app = Flask(__name__)

DB_FILE = "reservation.db"
CSV_FILE = "data/NamesRoomsWithMonths4.csv"  # Samme dataset som guests/rooms

#Localhost URL for testing: http://localhost:5004/
# Endpoints: 
# reservations
# reservations/<int:res_id>
# reservations/summary

# ---------- DATABASE OPSÆTNING ----------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                family_name TEXT,
                country TEXT,
                room_type TEXT,
                season TEXT,
                month TEXT,
                monthnumber INTEGER,
                days_rented INTEGER,
                price REAL,
                total_price REAL,
                check_in TEXT,
                check_out TEXT
            );
        """)
        conn.commit()


def seed_from_csv():
    """Indlæs reservationer fra CSV og generér fiktive datoer."""
    if not os.path.exists(CSV_FILE):
        print(f"⚠️ CSV not found: {CSV_FILE}")
        return

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reservations")
        count = cur.fetchone()[0]

        if count == 0:
            print("📥 Indlæser reservations-data fra CSV...")
            df = pd.read_csv(CSV_FILE, sep=";")
            df.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df.columns]

            # Sørg for at kolonnerne matcher
            rename_map = {
                "first_name": "first_name",
                "family_name": "family_name",
                "country": "country",
                "room_type": "room_type",
                "days_rented": "days_rented",
                "season": "season",
                "month": "month",
                "monthnumber": "monthnumber",
                "price": "price"
            }
            df.rename(columns=rename_map, inplace=True)

            # Rens numeriske kolonner
            df["price"] = df["price"].astype(str).str.replace(",", ".")
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df["days_rented"] = pd.to_numeric(df["days_rented"], errors="coerce")
            df["monthnumber"] = pd.to_numeric(df["monthnumber"], errors="coerce")

            # Beregn totalpris
            df["total_price"] = df["price"] * df["days_rented"]

           # Generér fiktive check-in / check-out datoer (baseret på månednummer)
            def gen_dates(month, days):
                try:
                    start = datetime(2025, int(month), 1) + timedelta(days=int(days) % 20)
                    end = start + timedelta(days=int(days))
                    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
                except Exception:
                    return None, None

            df[["check_in", "check_out"]] = df.apply(
                lambda r: pd.Series(gen_dates(r["monthnumber"], r["days_rented"])), axis=1
            )

            # Fjern ubrugte kolonner som ikke findes i databasen
            for col in ["adjusteddays", "adjusted_days"]:
                if col in df.columns:
                    df.drop(columns=[col], inplace=True)

            df.to_sql("reservations", conn, if_exists="append", index=False)

            print(f"✅ Imported {len(df)} reservations into SQLite database.")
        else:
            print("✅ Reservations already exist, skipping import.")


# ---------- ENDPOINTS ----------

@app.get("/reservations")
def all_reservations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM reservations").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/reservations/<int:res_id>")
def get_reservation(res_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM reservations WHERE id=?", (res_id,)).fetchone()
    return jsonify(dict(row)) if row else ({"error": "Reservation not found"}, 404)


@app.post("/reservations")
def create_reservation():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO reservations 
            (first_name, family_name, country, room_type, season, month, monthnumber, days_rented, price, total_price, check_in, check_out)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["first_name"], data["family_name"], data["country"],
            data["room_type"], data["season"], data["month"], data["monthnumber"],
            data["days_rented"], data["price"], data["total_price"],
            data["check_in"], data["check_out"]
        ))
        conn.commit()
    return {"status": "created"}, 201


@app.get("/reservations/summary")
def reservation_summary():
    """Returner nøgletal for analytics."""
    conn = get_db()
    df = pd.read_sql("SELECT * FROM reservations", conn)

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["days_rented"] = pd.to_numeric(df["days_rented"], errors="coerce")
    df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce")

    summary = {
        "total_reservations": len(df),
        "total_revenue_dkk": round(df["total_price"].sum(), 2),
        "avg_daily_rate": round(df["price"].mean(), 2),
        "avg_stay_days": round(df["days_rented"].mean(), 2),
        "top_room_types": (
            df.groupby("room_type")["total_price"]
              .sum()
              .sort_values(ascending=False)
              .head(5)
              .round(2)
              .to_dict()
        ),
        "revenue_by_season": (
            df.groupby("season")["total_price"]
              .sum()
              .round(2)
              .sort_values(ascending=False)
              .to_dict()
        )
    }
    return jsonify(summary)


# ---------- HEALTH CHECK ----------
from datetime import datetime
import sqlite3, os

@app.get("/health")
def health_check_reservation():
    """Health check for Reservation Service."""
    db_status, record_count = False, 0
    db_file = [f for f in os.listdir('.') if f.endswith('.db')]
    if db_file:
        try:
            conn = sqlite3.connect(db_file[0])
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM sqlite_master")
            record_count = cur.fetchone()[0]
            db_status = True
        except Exception:
            db_status = False
        finally:
            conn.close()

    return jsonify({
        "service": "reservation_service",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "details": {"db_connected": db_status, "db_tables": record_count}
    })


# ---------- MAIN ----------

if __name__ == "__main__":
    init_db()
    seed_from_csv()
    app.run(host="0.0.0.0", port=5004)
