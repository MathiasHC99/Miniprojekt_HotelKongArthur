import streamlit as st
import requests
import pandas as pd


# ---------- KONFIGURATION ----------
st.set_page_config(
    page_title="Hotel Kong Arthur – Analytics Dashboard",
    layout="wide"
)

API_ANALYTICS = "http://localhost:8000/api/analytics" # Analytics service

# ---------- HJÆLPEFUNKTIONER ----------

@st.cache_data(ttl=60)
def fetch_json(endpoint):
    """Hent JSON fra et API endpoint – med fallback hvis offline."""
    # endpoint timeout ændret fra 3 til 10 sekunder.
    try:
        r = requests.get(endpoint, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente data fra {endpoint}. Viser mock-data. ({e})")
        # Mockdata som fallback (så dashboard stadig virker)
        return {
            "total_revenue_all": 19832000,
            "total_revenue_room": 10938000,
            "total_revenue_bar": 5123000,
            "total_revenue_reservations": 3771000,
            "total_guests": 1001,
            "avg_daily_rate": 1127.3,
            "avg_stay_days": 10.8,
            "top_room_types": {
                "Suite": 2119671,
                "Spa Executive": 1722396,
                "Superior Double": 1339521
            },
            "revenue_by_season": {
                "High": 5078921,
                "Mid": 3710287,
                "Low": 2528792
            },
            "top_countries": {
                "Denmark": 112,
                "Germany": 95,
                "Sweden": 88,
                "Norway": 83,
                "United Kingdom": 77
            }
        }


# ---------- HENT DATA ----------

overview = fetch_json(f"{API_ANALYTICS}/analytics/overview")
monthly = fetch_json(f"{API_ANALYTICS}/analytics/monthly_revenue")


# ---------- HEADER ----------

st.title("Hotel Kong Arthur – Analytics Dashboard")
st.caption("Samlet overblik over omsætning, gæster og nøgleindikatorer fra alle services.")

st.divider()


# ---------- KPI-SEKTION ----------

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total omsætning (DKK)", f"{overview['total_revenue_all']:,.0f}")
col2.metric("🛏️ Gns. dagspris (ADR)", f"{overview['avg_daily_rate']:,.0f} DKK")
col3.metric("📆 Gns. opholdslængde", f"{overview['avg_stay_days']:,.1f} dage")
col4.metric("👥 Antal gæster", f"{overview['total_guests']:,.0f}")

st.divider()


# ---------- GRAF: Årets månedlige omsætning ----------
st.subheader("Årets månedlige omsætning")

if "monthly_revenue_dkk" in monthly:
    df_monthly = pd.DataFrame(list(monthly["monthly_revenue_dkk"].items()), columns=["Måned", "Omsætning (DKK)"])
    df_monthly.set_index("Måned", inplace=True)
    st.line_chart(df_monthly)
else:
    st.info("Ingen månedlige data tilgængelige.")


# ---------- TOP ROOM TYPES ----------
st.subheader("Mest indbringende værelsestyper")

df_rooms = pd.DataFrame(list(overview["top_room_types"].items()), columns=["Værelsestype", "Omsætning (DKK)"])
st.bar_chart(df_rooms.set_index("Værelsestype"))

# ---------- OMSÆTNING PR. SÆSON ----------
st.subheader("Omsætning pr. sæson")

df_season = pd.DataFrame(list(overview["revenue_by_season"].items()), columns=["Sæson", "Omsætning (DKK)"])
st.bar_chart(df_season.set_index("Sæson"))


# ---------- TOP GÆSTELANDE ----------
st.subheader("Toplande for gæster")

df_countries = pd.DataFrame(list(overview["top_countries"].items()), columns=["Land", "Antal gæster"])
st.bar_chart(df_countries.set_index("Land"))


st.divider()
st.caption("Data leveret fra: Room, Bar, Guest, Reservation og Analytics microservices.")
