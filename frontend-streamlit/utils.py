import os
import requests
import streamlit as st
import pandas as pd
import datetime, random

# ---------- BASE URL (lokal vs. docker) ----------

# standard: lokal udvikling
API_BASE = os.getenv("API_URL", "http://localhost:8000/api")

# hvis vi kører i en container, brug gateway-navnet
if os.path.exists("/.dockerenv"):
    API_BASE = os.getenv("API_URL", "http://gateway:8000/api")


# ---------- API FETCHING & CACHING ----------

@st.cache_data(ttl=3600)
def fetch_json(endpoint: str):
    """
    Henter JSON-data fra et fuldt endpoint (fx f"{API_BASE}/analytics/analytics/overview")
    og cacher det i 1 time.
    """
    try:
        r = requests.get(endpoint, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"⚠️ Kunne ikke hente data fra {endpoint}. ({e})")
        return {}

def get_data(endpoint: str, key: str):
    """Gemmer hentede data i session_state for hurtigere sideskift."""
    if key not in st.session_state:
        st.session_state[key] = fetch_json(endpoint)
    return st.session_state[key]


# ---------- FORHENT ALLE SERVICES ----------

def preload_all_data():
    if "preloaded" in st.session_state:
      return st.session_state["preloaded"]

    with st.spinner("🔄 Indlæser data fra alle services..."):
        data = {
            "overview": fetch_json(f"{API_BASE}/analytics/analytics/overview"),
            "monthly": fetch_json(f"{API_BASE}/analytics/analytics/monthly_revenue"),
            "rooms": fetch_json(f"{API_BASE}/room/rooms/summary"),
            "bar": fetch_json(f"{API_BASE}/bar/bar/summary"),
            "guests": fetch_json(f"{API_BASE}/guest/guests/summary"),
            "reservations": fetch_json(f"{API_BASE}/reservation/reservations/summary"),
        }

    st.session_state["preloaded"] = data
    return data


# ---------- MÅNEDSSORTERING ----------

MONTH_ORDER = [
    "Januar", "Februar", "Marts", "April", "Maj", "Juni",
    "Juli", "August", "September", "Oktober", "November", "December"
]

def month_dataframe(month_dict):
    """Konverterer dict som {'Januar': 1234, ...} til DataFrame i korrekt rækkefølge."""
    if not month_dict:
        return pd.DataFrame(columns=["Måned", "Omsætning (DKK)"])

    df = pd.DataFrame(list(month_dict.items()), columns=["Måned", "Omsætning (DKK)"])
    df["Måned"] = pd.Categorical(df["Måned"], categories=MONTH_ORDER, ordered=True)
    df.sort_values("Måned", inplace=True)
    df.set_index("Måned", inplace=True)
    return df
