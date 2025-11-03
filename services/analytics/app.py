from flask import Flask, jsonify
import requests
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)



# Bruger Docker service-navne, men beholder fallback for lokal
if os.path.exists("/.dockerenv"):
    ROOM_URL = "http://room_service:5001"
    BAR_URL = "http://bar_service:5002"
    GUEST_URL = "http://guest_service:5003"
    RES_URL = "http://reservation_service:5004"
else:
    ROOM_URL = "http://localhost:5001"
    BAR_URL = "http://localhost:5002"
    GUEST_URL = "http://localhost:5003"
    RES_URL = "http://localhost:5004"


# ---------- HJÆLPEFUNKTIONER ----------

def safe_get(url):
    print(f"➡️  Henter data fra: {url}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️ Fejl ved kald til {url}: {e}")
        return {}

# ---------- ENDPOINTS ----------

@app.get("/analytics/overview")
def analytics_overview():
    """Hent totaler og KPI’er på tværs af alle services."""
    room_data = safe_get(f"{ROOM_URL}/rooms/revenue/total")
    bar_data = safe_get(f"{BAR_URL}/bar/summary")
    guest_data = safe_get(f"{GUEST_URL}/guests/summary")
    res_data = safe_get(f"{RES_URL}/reservations/summary")

    total_room = room_data.get("total_revenue_dkk", 0)
    total_bar = bar_data.get("total_revenue_dkk", 0)
    total_res = res_data.get("total_revenue_dkk", 0)

    total_all = total_room + total_bar + total_res

    summary = {
        "total_revenue_all": round(total_all, 2),
        "total_revenue_room": round(total_room, 2),
        "total_revenue_bar": round(total_bar, 2),
        "total_revenue_reservations": round(total_res, 2),
        "total_guests": guest_data.get("summary", {}).get("total_guests", 0),
        "top_countries": guest_data.get("by_country") or guest_data.get("summary", {}).get("top_countries", {}),
        "avg_daily_rate": res_data.get("avg_daily_rate", 0),
        "avg_stay_days": res_data.get("avg_stay_days", 0),
        "top_room_types": res_data.get("top_room_types", {}),
        "revenue_by_season": res_data.get("revenue_by_season", {})
    }
    return jsonify(summary)

# ---------- Årets månedlige omsætning ----------

@app.get("/analytics/monthly_revenue")
def monthly_revenue():
    """Hent samlet månedlig omsætning (fra reservationer og evt. bar)."""
    res_data = safe_get(f"{RES_URL}/reservations")
    if not res_data:
        return jsonify({"error": "Ingen reservationsdata"}), 404

    df = pd.DataFrame(res_data)
    if "monthnumber" not in df.columns or "total_price" not in df.columns:
        return jsonify({"error": "Mangler nødvendige kolonner"}), 400

    df["monthnumber"] = pd.to_numeric(df["monthnumber"], errors="coerce")
    df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce")

    monthly = (
        df.groupby("monthnumber")["total_price"]
          .sum()
          .round(2)
          .reindex(range(1, 13), fill_value=0)
          .to_dict()
    )

    # Konverter månednumre til navne
    month_names = {
        1: "Januar", 2: "Februar", 3: "Marts", 4: "April",
        5: "Maj", 6: "Juni", 7: "Juli", 8: "August",
        9: "September", 10: "Oktober", 11: "November", 12: "December"
    }

    monthly_named = {month_names[k]: v for k, v in monthly.items()}

    return jsonify({
        "monthly_revenue_dkk": monthly_named,
        "total_revenue_dkk": round(df["total_price"].sum(), 2)
    })












from datetime import datetime
import sqlite3, os


# ---------- HEALTH CHECK ----------

from datetime import datetime
import requests

@app.get("/analytics/health")
def analytics_health():
    """Health check for Analytics + afhængigheder."""
    services = {
        "room": ROOM_URL,
        "bar": BAR_URL,
        "guest": GUEST_URL,
        "reservation": RES_URL
    }

    results = {}
    for name, url in services.items():
        try:
            r = requests.get(f"{url}/health", timeout=5)
            results[name] = "ok" if r.status_code == 200 else f"error ({r.status_code})"
        except Exception as e:
            results[name] = f"unreachable ({e})"

    return jsonify({
        "service": "analytics_service",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": results
    })


# ---------- MAIN ----------

if __name__ == "__main__":
    print("✅ Analytics service kører...")
    app.run(host="0.0.0.0", port=5005, debug=False)
