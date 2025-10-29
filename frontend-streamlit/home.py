import streamlit as st
import pandas as pd
import requests
import datetime, random

st.set_page_config(page_title="Hotel Kong Arthur – Dashboard", layout="wide")

# --- Prøver API-kald, ellers bruges mock ---
API = "http://localhost:8000"

def fetch_json(path):
    try:
        r = requests.get(f"{API}{path}", timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente {path}. Viser mockdata. ({e})")
        return mock_data(path)

def mock_data(path):
    if path == "/kpis/top":
        return {
            "year_revenue_dkk": 1832450,
            "top_room_types": [
                {"room_type": "Deluxe Suite", "revenue": 642000},
                {"room_type": "Standard Double", "revenue": 382000},
                {"room_type": "Economy Single", "revenue": 241000},
                {"room_type": "Family Room", "revenue": 181000},
                {"room_type": "Penthouse", "revenue": 139000},
            ],
            "top_countries": [
                {"country": "Denmark", "revenue": 712000},
                {"country": "Germany", "revenue": 433000},
                {"country": "UK", "revenue": 254000},
                {"country": "Sweden", "revenue": 192000},
                {"country": "Norway", "revenue": 144000},
            ]
        }
    elif path == "/kpis/rooms":
        base = datetime.date(2025, 10, 1)
        return [
            {"date": str(base + datetime.timedelta(days=i)),
             "occupancy": round(random.uniform(0.6, 1.0), 2),
             "ADR": round(random.uniform(800, 1500), 2),
             "RevPAR": round(random.uniform(500, 900), 2)}
            for i in range(10)
        ]
    return []

# --- UI ---
st.title("Hotel Kong Arthur – Softwarearkitektur Demo")

kpi_data = fetch_json("/kpis/top")

col1, col2, col3 = st.columns(3)
col1.metric("Årsindtjening (DKK)", f"{kpi_data.get('year_revenue_dkk',0):,.0f}")
col2.metric("Top room type", kpi_data.get("top_room_types", [{}])[0].get("room_type", "-"))
col3.metric("Top country", kpi_data.get("top_countries", [{}])[0].get("country", "-"))

st.subheader("Top 5 værelsestyper")
st.table(pd.DataFrame(kpi_data["top_room_types"]))

st.subheader("Top 5 lande")
st.table(pd.DataFrame(kpi_data["top_countries"]))

st.subheader("Belægning, ADR og RevPAR pr. dag")
rooms_data = fetch_json("/kpis/rooms")
df = pd.DataFrame(rooms_data)
if not df.empty:
    st.line_chart(df.set_index("date")[["occupancy","ADR","RevPAR"]])
