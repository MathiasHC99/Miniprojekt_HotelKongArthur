# api-gateway/app.py
from flask import Flask, jsonify, request
import os, requests, pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Streamlit (8501) -> Gateway (5055)

# ------------------- Konfiguration -------------------
SERVICES = {
    "reservation": os.getenv("RESERVATION_URL", "http://reservation:5000"),
    "room":        os.getenv("ROOM_URL",        "http://room:5000"),
    "guest":       os.getenv("GUEST_URL",       "http://guest:5000"),
    "review":      os.getenv("REVIEW_URL",      "http://review:5000"),
    "bar":         os.getenv("BAR_URL",         "http://bar:5000"),
    "analytics":   os.getenv("ANALYTICS_URL",   "http://analytics:5000"),
}

# CSV-filer ligger i projektroden (én mappe op fra api-gateway/)
ROOMS_CSV = os.getenv("ROOMS_CSV", "../NamesRoomsWithMonths4.csv")
BAR_CSV   = os.getenv("BAR_CSV",   "../drinks_menu_with_sales.csv")

def read_csv_clean(path, sep=";"):
    """Læs CSV, normaliser kolonnenavne, lav sikre numerics."""
    df = pd.read_csv(path, sep=sep)

    # normaliser kolonnenavne
    df.columns = (
        df.columns.str.strip()
                  .str.replace(" ", "_")
                  .str.replace("-", "_")
                  .str.replace("(", "", regex=False)
                  .str.replace(")", "", regex=False)
                  .str.lower()
    )

    # konverter numeriske felter med evt. komma-decimaler
    for col in df.columns:
        if any(k in col for k in [
            "price", "revenue", "units", "days", "monthnumber", "month_number",
            "adjusteddays", "adjusted_days"
        ]):
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# ------------------- Hjælper -------------------
def proxy(service_key, path):
    try:
        r = requests.get(f"{SERVICES[service_key]}{path}", timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e), "service": service_key, "path": path}), 502

# ------------------- Basis / Health -------------------
@app.get("/")
def root():
    return {"ok": True, "service": "api-gateway", "hint": "try /health or /data/rooms"}

@app.get("/health")
def health():
    return {"status": "ok", "csv": {"rooms": ROOMS_CSV, "bar": BAR_CSV}}

# ------------------- CSV -> JSON -------------------
@app.get("/data/rooms")
def data_rooms():
    try:
        df = read_csv_clean(ROOMS_CSV, sep=";")
    except Exception as e:
        return jsonify({"error": f"Could not read {ROOMS_CSV}: {e}"}), 500

    # ensret evt. feltnavne
    rename_map = {
        "monthnumber": "month_number",
        "adjusteddays": "adjusted_days",
        "days": "days_rented"
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k: v}, inplace=True)

    return jsonify(df.to_dict(orient="records"))

@app.get("/data/bar")
def data_bar():
    try:
        df = read_csv_clean(BAR_CSV, sep=";")
    except Exception as e:
        return jsonify({"error": f"Could not read {BAR_CSV}: {e}"}), 500

    # standardiser kolonnenavne
    # prøv at finde pris-kolonne og navngiv til price_dkk
    if "price_dkk" not in df.columns:
        cand = [c for c in df.columns if "price" in c]
        if cand:
            df.rename(columns={cand[0]: "price_dkk"}, inplace=True)

    # typisk kolonnenavne:
    # drink_name / name, category, units_sold, price_dkk -> total_revenue
    if "drink_name" not in df.columns:
        if "name" in df.columns:
            df.rename(columns={"name": "drink_name"}, inplace=True)

    if "total_revenue" not in df.columns and \
       "units_sold" in df.columns and "price_dkk" in df.columns:
        df["total_revenue"] = df["units_sold"] * df["price_dkk"]

    return jsonify(df.to_dict(orient="records"))

# ------------------- KPI / passthroughs (valgfrit) -------------------
@app.get("/kpis/top")
def kpis_top():
    return proxy("analytics", "/kpis/top")

@app.get("/kpis/rooms")
def kpis_rooms():
    return proxy("analytics", "/kpis/rooms")

@app.get("/rooms/revenue/by_roomtype")
def rooms_rev_roomtype():
    return proxy("room", "/rooms/revenue/by_roomtype")

@app.get("/rooms/revenue/by_season")
def rooms_rev_season():
    return proxy("room", "/rooms/revenue/by_season")

@app.get("/bar/summary")
def bar_summary_proxy():
    return proxy("bar", "/summary")

# ------------------- START SERVER -------------------
if __name__ == "__main__":
    # Brug en klar, fri port
    port = int(os.getenv("PORT", 5055))
    print(f">> API-GATEWAY STARTER på http://127.0.0.1:{port}")
    print(f">> ROOMS_CSV = {ROOMS_CSV}")
    print(f">> BAR_CSV   = {BAR_CSV}")
    app.run(host="0.0.0.0", port=port, debug=True)
