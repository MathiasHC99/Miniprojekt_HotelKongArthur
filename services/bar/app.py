from flask import Flask, jsonify, request
import sqlite3, pandas as pd, os

app = Flask(__name__)

DB_FILE = "bar.db"
CSV_FILE = "../../drinks_menu_with_sales.csv"  # Tilpas sti efter behov


# Endpoints til test: localhost:5002/
# bar/drinks
# bar/summary
# bar/category/<string:category>
# bar/top/<int:n>
# bar/search     (GET /bar/search?q=espresso) url-encoded query parameter 'q'




# ---------- DATABASE OPSÆTNING ----------

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Opret tabelstruktur"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drink_name TEXT,
                category TEXT,
                price_dkk REAL,
                units_sold INTEGER,
                total_revenue REAL
            );
        """)
        conn.commit()


def seed_from_csv():
    """Importer CSV og seed data i SQLite"""
    # Drop gammel tabel for at undgå mismatch
    with get_db() as conn:
        conn.execute("DROP TABLE IF EXISTS drinks;")
        conn.commit()

    # Reopret tabel
    init_db()

    if not os.path.exists(CSV_FILE):
        print(f"⚠️ CSV file not found: {CSV_FILE}")
        return

    # Læs CSV
    print("📥 Indlæser data fra CSV...")
    df = pd.read_csv(CSV_FILE, sep=";")
    print("Kolonner fundet i CSV:", df.columns.tolist())

    # Rens kolonnenavne (fjerner specialtegn og gør lowercase)
    df.columns = [
        c.strip()
         .replace(" ", "_")
         .replace("-", "_")
         .replace("(", "")
         .replace(")", "")
         .lower()
        for c in df.columns
    ]
    print("Efter rensning:", df.columns.tolist())

    # Tjek for mulige pris-kolonner
    price_cols = [c for c in df.columns if "price" in c and "dkk" in c]
    if not price_cols:
        raise ValueError("Ingen pris-kolonne fundet i CSV!")
    price_col = price_cols[0]

    # Ensret kolonnenavne til at matche SQLite
    df.rename(columns={price_col: "price_dkk"}, inplace=True)

    # Beregn total omsætning
    # Konverter evt. komma-decimaler til punktum
    df["price_dkk"] = df["price_dkk"].astype(str).str.replace(",", ".")
    df["units_sold"] = df["units_sold"].astype(str).str.replace(",", ".")  # sjældent nødvendigt, men for en sikkerheds skyld

    # Konverter til tal
    df["price_dkk"] = pd.to_numeric(df["price_dkk"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")

    # Beregn total omsætning som tal
    df["total_revenue"] = df["price_dkk"] * df["units_sold"]

    # Sørg for at total_revenue også er numerisk
    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce")


    print("Kolonner der indsættes:", df.columns.tolist())

    with get_db() as conn:
        df.to_sql("drinks", conn, if_exists="append", index=False)
        existing = [col[1] for col in conn.execute("PRAGMA table_info(drinks)").fetchall()]
        print("SQLite ser nu kolonner:", existing)
        print(f"✅ Imported {len(df)} drinks into SQLite database.")


# ---------- ENDPOINTS ----------

@app.get("/bar/drinks")
def all_drinks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM drinks").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/bar/summary")
def bar_summary():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM drinks", conn)

    # Sørger for at numeriske kolonner faktisk er floats
    for col in ["price_dkk", "units_sold", "total_revenue"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    summary = {
        "total_revenue_dkk": round(df["total_revenue"].sum(), 2),
        "avg_price_dkk": round(df["price_dkk"].mean(), 2),
        "top_drinks": (
            df.sort_values("total_revenue", ascending=False)
              [["drink_name", "category", "total_revenue"]]
              .head(5)
              .to_dict(orient="records")
        ),
        "revenue_by_category": (
            df.groupby("category")["total_revenue"]
              .sum()
              .round(2)
              .to_dict()
        )
    }

    # Procentfordeling mellem kategorier
    total = summary["total_revenue_dkk"]
    summary["category_share"] = {
        cat: f"{(val / total * 100):.1f}%" for cat, val in summary["revenue_by_category"].items()
    }

    return jsonify(summary)


@app.get("/bar/category/<string:category>")
def by_category(category):
    conn = get_db()
    df = pd.read_sql("SELECT * FROM drinks", conn)
    subset = df[df["category"].str.lower() == category.lower()]
    return jsonify(subset.to_dict(orient="records"))


@app.get("/bar/top/<int:n>")
def top_n_drinks(n):
    conn = get_db()
    df = pd.read_sql("SELECT * FROM drinks", conn)
    df = df.sort_values("total_revenue", ascending=False).head(n)
    return jsonify(df.to_dict(orient="records"))


@app.get("/bar/search")
def search_drink():
    query = request.args.get("q", "").lower()
    conn = get_db()
    df = pd.read_sql("SELECT * FROM drinks", conn)
    subset = df[df["drink_name"].str.lower().str.contains(query)]
    return jsonify(subset.to_dict(orient="records"))


# ---------- MAIN ----------

if __name__ == "__main__":
    init_db()
    seed_from_csv()
    app.run(host="0.0.0.0", port=5002)

