import streamlit as st
import pandas as pd
import requests
import altair as alt
from utils import API_BASE, fetch_json

# ---------- KONFIGURATION ----------
st.set_page_config(page_title="🛏️ Room Insights – Hotel Kong Arthur", layout="wide")
API_ROOM = f"{API_BASE}/room"
API_RES = f"{API_BASE}/reservation"

# ---------- HJÆLPEFUNKTION ----------
@st.cache_data(ttl=3600)
def fetch_json(endpoint):
    """Henter JSON-data og cacher i 1 time."""
    try:
        r = requests.get(endpoint, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente data fra {endpoint}. ({e})")
        return {}

# ---------- HENT DATA ----------
room_by_season = fetch_json(f"{API_ROOM}/rooms/revenue/by_roomtype_and_season")
season_revenue = fetch_json(f"{API_ROOM}/rooms/revenue/by_season")
total_revenue = fetch_json(f"{API_ROOM}/rooms/revenue/total")
reservations = fetch_json(f"{API_RES}/reservations/summary")

# ---------- HEADER ----------
st.title("🛏️ Room Insights – Hotel Kong Arthur")
st.markdown(
    "Denne side viser, hvordan hotellets værelser performer gennem året. "
    
)
st.divider()

# ---------- KPI’ER ----------

# Beregn samlet room revenue baseret på de data, der findes
if total_revenue and "total_revenue_dkk" in total_revenue:
    total_value = total_revenue["total_revenue_dkk"]
elif "room_by_season" in locals() and room_by_season:
    total_value = sum(
        revenue
        for season_data in room_by_season.values()
        for revenue in season_data.values()
    )
else:
    total_value = 0

# Find mest populære værelse (baseret på summeret omsætning)
if "room_by_season" in locals() and room_by_season:
    combined = {}
    for season_dict in room_by_season.values():
        for room, value in season_dict.items():
            combined[room] = combined.get(room, 0) + value
    top_room = max(combined, key=combined.get)
else:
    top_room = "N/A"

# Find mest profitable sæson
top_season = max(season_revenue, key=season_revenue.get) if season_revenue else "N/A"

# Gns. ophold
avg_stay = f"{reservations.get('avg_stay_days', 0):.1f} dage"

# KPI-visning
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Samlet room revenue", f"{total_value:,.0f} DKK")
col2.metric("🏆 Mest populære værelse", top_room)
col3.metric("🌤️ Mest profitable sæson", top_season)
col4.metric("📆 Gns. ophold", avg_stay)

st.divider()


# ---------- INTERAKTIV FILTRERING ----------
st.subheader("Filtrér efter sæson")
selected_season = st.radio(
    "Vælg sæson:",
    ["Alle", "High", "Mid", "Low"],
    horizontal=True,
    help="Filtrér for at se hvilke værelsestyper der performer bedst i en bestemt sæson."
)
st.divider()

# ---------- DATAFORBEREDELSE ----------
# Vi henter nu reelle data pr. værelsestype og sæson fra /by_roomtype_and_season
# og viser enten samlet overblik (pivot) eller filtreret sæsonvisning.

if "room_by_season" not in locals():
    room_by_season = fetch_json(f"{API_ROOM}/rooms/revenue/by_roomtype_and_season")

if not room_by_season:
    st.error("Ingen data modtaget fra /rooms/revenue/by_roomtype_and_season.")
    st.stop()

# Hvis brugeren vælger "Alle" -> vis pivot-tabel med alle sæsoner
if selected_season == "Alle":
    df_room = pd.DataFrame([
        (season, room, revenue)
        for season, rooms in room_by_season.items()
        for room, revenue in rooms.items()
    ], columns=["Sæson", "Værelsestype", "Omsætning (DKK)"])

    if df_room.empty:
        st.warning("Ingen data fundet for værelsestyper og sæsoner.")
        st.stop()

    # Lav pivot-tabel, så rækker = værelser og kolonner = sæsoner
    df_pivot = df_room.pivot_table(
        index="Værelsestype",
        columns="Sæson",
        values="Omsætning (DKK)",
        fill_value=0
    ).sort_index(axis=1, ascending=True)

    st.subheader("🏨 Omsætning pr. værelsestype (alle sæsoner)")
    st.dataframe(
    df_pivot.style
        .format(lambda x: f"{x:,.0f}".replace(",", ".") + " DKK")
        .highlight_max(axis=1, color="#D1FAE5"),
    use_container_width=True
)



    # Brug et stacked bar chart for overblik over alle sæsoner
    df_pivot_reset = df_pivot.reset_index().melt(id_vars="Værelsestype", var_name="Sæson", value_name="Omsætning (DKK)")
    chart_all = (
        alt.Chart(df_pivot_reset)
        .mark_bar()
        .encode(
            x=alt.X("Værelsestype:N", sort="-y", title="Værelsestype"),
            y=alt.Y("Omsætning (DKK):Q", stack="normalize", title="Andel af samlet omsætning"),
            color=alt.Color("Sæson:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=["Værelsestype", "Sæson", "Omsætning (DKK)"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart_all, use_container_width=True)

else:
    #  Hvis brugeren vælger en bestemt sæson
    if selected_season in room_by_season:
        df_room = pd.DataFrame(
            list(room_by_season[selected_season].items()),
            columns=["Værelsestype", "Omsætning (DKK)"]
        ).sort_values("Omsætning (DKK)", ascending=False)

        st.subheader(f"Omsætning pr. værelsestype – {selected_season} season")
        c1, c2 = st.columns([2, 1])
        with c1:
            chart = (
            alt.Chart(df_room)
            .mark_bar(color="#3B82F6")
            .encode(
                x=alt.X("Værelsestype:N", sort="-y"),
                y=alt.Y("Omsætning (DKK):Q", title="Omsætning (DKK)"),
                tooltip=["Værelsestype", "Omsætning (DKK)"]
            )
            .properties(height=400)
        )
        st.altair_chart(chart, use_container_width=True)

        with c2:
            st.dataframe(
                df_room.style.highlight_max(subset=["Omsætning (DKK)"], color="#D1FAE5"),
                use_container_width=True
            )
    else:
        st.warning(f"Ingen data fundet for sæson: {selected_season}")
        st.stop()



# ---------- ANTAL UDLEJEDE VÆRELSER PR. MÅNED ----------
st.divider()
st.subheader("Antal udlejede værelser pr. måned")

bookings_by_month = fetch_json(f"{API_ROOM}/rooms/bookings/by_month_and_type")

if bookings_by_month:
    # Konverter nested dict -> dataframe
    df_bookings = pd.DataFrame([
        (room, month, count)
        for room, months in bookings_by_month.items()
        for month, count in months.items()
    ], columns=["Værelsestype", "Måned", "Antal bookinger"])

    # Sørg for, at Måned er numerisk (kan være tekst i SQLite)
    df_bookings["Måned"] = pd.to_numeric(df_bookings["Måned"], errors="coerce")

    # Fjern rækker uden gyldig måned
    df_bookings = df_bookings.dropna(subset=["Måned"])

    # Konverter til månednavne
    month_names = [
        "Januar", "Februar", "Marts", "April", "Maj", "Juni",
        "Juli", "August", "September", "Oktober", "November", "December"
    ]
    df_bookings["Måned"] = df_bookings["Måned"].apply(lambda x: month_names[int(x) - 1])

    # Byg line chart
    chart_bookings = (
        alt.Chart(df_bookings)
        .mark_line(point=True)
        .encode(
            x=alt.X("Måned:N", sort=month_names, title="Måned"),
            y=alt.Y("Antal bookinger:Q", title="Antal bookinger"),
            color=alt.Color("Værelsestype:N", legend=alt.Legend(title="Værelsestype")),
            tooltip=["Måned", "Værelsestype", "Antal bookinger"]
        )
        .properties(height=400, title="Udlejninger pr. måned fordelt på værelsestype")
    )

    st.altair_chart(chart_bookings, use_container_width=True)


else:
    st.info("Ingen data tilgængelig for månedlige bookinger.")


# ---------- AUTOMATISK INDSIGT ----------
if not df_room.empty and season_revenue:
    top_room = df_room.iloc[0]["Værelsestype"]

    # brug den kolonne, som faktisk findes
    if "Omsætning (DKK)" in df_room.columns:
        top_value = df_room.iloc[0]["Omsætning (DKK)"]
    elif "Sæson Omsætning (DKK)" in df_room.columns:
        top_value = df_room.iloc[0]["Sæson Omsætning (DKK)"]
    else:
        top_value = 0

    top_season = max(season_revenue, key=season_revenue.get)

    if selected_season == "Alle":
        st.markdown(
            f"**Indsigt:** Værelsetypen **{top_room}** genererer den højeste omsætning over året "
            f"med cirka **{top_value:,.0f} DKK**. Den mest profitable periode for hotellet er ironisk nok **{top_season}-season**, "
            f"hvor både priser og belægning er højest."
        )
