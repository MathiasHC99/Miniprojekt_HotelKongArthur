import streamlit as st
import pandas as pd
import requests
import altair as alt
alt.data_transformers.disable_max_rows()
from utils import API_BASE

# ---------- KONFIG ----------
st.set_page_config(page_title="Guest & Country – Hotel Kong Arthur", layout="wide")
API_GUEST = f"{API_BASE}/guest"
API_RES = f"{API_BASE}/reservation"

# ---------- HJÆLPEFUNKTION ----------
@st.cache_data(ttl=60)
def fetch_json(endpoint):
    try:
        r = requests.get(endpoint, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente data fra {endpoint}. Viser mock-data. ({e})")
        return {
            "summary": {
                "total_guests": 1001,
                "avg_stay_days": 10.8,
                "top_country": "Germany",
                "unique_countries": 22
            },
            "by_country": {
                "Denmark": 980000,
                "Germany": 765000,
                "Sweden": 620000,
                "Norway": 580000,
                "United Kingdom": 550000,
                "France": 410000,
                "Italy": 380000
            },
            "by_season": {
                "High": {"Germany": 305000, "Denmark": 290000, "Sweden": 200000},
                "Mid": {"Germany": 250000, "Sweden": 240000, "Norway": 220000},
                "Low": {"Denmark": 190000, "France": 180000, "Italy": 160000}
            },
            "by_country_roomtype": {
                "Germany": {"Suite": 120000, "Superior Double": 90000, "Junior Suite": 80000},
                "Denmark": {"Suite": 110000, "Spa Executive": 95000, "Superior Double": 85000},
                "Sweden": {"Junior Suite": 70000, "Superior Double": 65000, "Standard Double": 62000},
            }
        }

# ---------- HENT DATA ----------
# Kun ét kald – alle data ligger her
guest_data = fetch_json(f"{API_GUEST}/guests/summary")

summary = guest_data.get("summary", {})
country_data = guest_data.get("by_country", {})
season_data = guest_data.get("by_season", {})
country_room = guest_data.get("by_country_roomtype", {})
reservations = fetch_json(f"{API_RES}/reservations/summary")

# ---------- HEADER ----------
st.title("Guest & Country Insights")
st.markdown(
    "Et overblik over hotellets gæster fordelt på nationalitet, sæson og præferencer. "
    "Formålet er at identificere de mest værdifulde markeder og forstå deres bookingmønstre."
)
st.divider()

# ---------- KPI’ER ----------

# Gns. ophold
avg_stay = f"{reservations.get('avg_stay_days', 0):.1f} dage"

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Gæster i alt", f"{summary.get('total_guests', 0):,}")
col2.metric("🌎 Antal lande", f"{summary.get('unique_countries', 0)}")
col3.metric("🏆 Mest værdifulde marked", summary.get("top_country", "N/A"))
# col4.metric("📆 Gns. ophold", f"{summary.get('avg_stay_days', 0):.1f} dage")
col4.metric("📆 Gns. ophold", avg_stay)
st.divider()

# ---------- FILTER ----------
with st.expander("Filtrér efter sæson", expanded=True):
    selected_season = st.selectbox(
        "Vælg sæson",
        ["Alle", "High", "Mid", "Low"],
        index=0,
        help="Filtrer visninger baseret på sæson"
    )

# ---------- TOPLANDE ----------
st.subheader("Omsætning pr. land")

df_country = pd.DataFrame(list(country_data.items()), columns=["Land", "Omsætning (DKK)"])
df_country = df_country.sort_values("Omsætning (DKK)", ascending=False)
if not df_country.empty:
    chart_country = (
        alt.Chart(df_country)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Omsætning (DKK):Q", title="Omsætning (DKK)"),
            y=alt.Y(
                "Land:N",
                sort=alt.EncodingSortField(field="Omsætning (DKK)", order="descending"),
                title=None
            ),
            color=alt.Color("Omsætning (DKK):Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["Land", "Omsætning (DKK)"]
        )
        .properties(height=max(400, len(df_country) * 20))
    )
    st.altair_chart(chart_country, use_container_width=True)
else:
    st.info("Ingen landedata tilgængelige.")
st.divider()

# ---------- SÆSONAFHÆNGIGT VIEW ----------
st.subheader("Omsætning pr. sæson og land")

if season_data:
    df_season = pd.DataFrame([
        (season, country, revenue)
        for season, countries in season_data.items()
        for country, revenue in countries.items()
    ], columns=["Sæson", "Land", "Omsætning (DKK)"])

    if selected_season != "Alle":
        df_season = df_season[df_season["Sæson"] == selected_season]

    chart_season = (
        alt.Chart(df_season)
        .mark_bar()
        .encode(
            x=alt.X("Sæson:N", title="Sæson", sort=["Low", "Mid", "High"]),
            y=alt.Y("Omsætning (DKK):Q"),
            color=alt.Color("Land:N", legend=alt.Legend(title="Land")),
            tooltip=["Land", "Sæson", "Omsætning (DKK)"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart_season, use_container_width=True)
else:
    st.info("Ingen sæsondata tilgængelig.")
st.divider()

# ---------- HEATMAP: LAND VS VÆRELSESTYPE ----------
st.subheader("Land vs. værelsestype (bookings / præference)")

df_heat = pd.DataFrame([
    (country, room, revenue)
    for country, rooms in country_room.items()
    for room, revenue in rooms.items()
], columns=["Land", "Værelsestype", "Omsætning (DKK)"])

if not df_heat.empty:
    chart_heat = (
        alt.Chart(df_heat)
        .mark_rect()
        .encode(
            x=alt.X("Værelsestype:N", title="Værelsestype"),
            y=alt.Y("Land:N", sort=alt.EncodingSortField(field="Land", order="ascending")),
            color=alt.Color("Omsætning (DKK):Q", scale=alt.Scale(scheme="blues")),
            tooltip=["Land", "Værelsestype", "Omsætning (DKK)"]
        )
        .properties(height=max(400, len(df_heat['Land'].unique()) * 20))
    )
    st.altair_chart(chart_heat, use_container_width=True)
else:
    st.info("Ingen data tilgængelig for heatmap.")
st.divider()

# ---------- INDSIGT ----------
if not df_country.empty:
    top_country = df_country.iloc[0]["Land"]
    top_value = df_country.iloc[0]["Omsætning (DKK)"]
    st.markdown(
        f"**Indsigt:** {top_country} er det mest værdifulde marked med en samlet omsætning på "
        f"**{top_value:,.0f} DKK**. Gæster herfra booker typisk under **Mid season** og foretrækker "
        f"premium værelser som *Suite* og *Spa Executive*."
    )
else:
    st.markdown("**📊 Indsigt:** Der er ikke tilstrækkelig data til at generere gæsteindsigt.")
