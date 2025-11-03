import streamlit as st
import requests
import pandas as pd
import altair as alt


# from utils import get_data, month_dataframe

# API_ANALYTICS = "http://localhost:8000/api/analytics/analytics"

# overview = get_data(f"{API_ANALYTICS}/overview", "overview_data")
# monthly = get_data(f"{API_ANALYTICS}/monthly_revenue", "monthly_data")

# st.subheader("📈 Årets månedlige omsætning")

# if "monthly_revenue_dkk" in monthly:
#     df_month = month_dataframe(monthly["monthly_revenue_dkk"])
#     st.line_chart(df_month)
# else:
#     st.info("Ingen månedlige data tilgængelige.")






# ---------- KONFIG ----------
st.set_page_config(page_title="Hotel Kong Arthur – Overview", layout="wide")
API_ANALYTICS = "http://localhost:8000/api/analytics/analytics"



# ---------- HJÆLPEFUNKTION ----------

@st.cache_data(ttl=60)
def fetch_json(endpoint):
    try:
        r = requests.get(endpoint, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Kunne ikke hente data fra {endpoint} – viser mock-data. ({e})")
        return {
            "total_revenue_all": 19832000,
            "total_revenue_room": 10938000,
            "total_revenue_bar": 5123000,
            "total_revenue_reservations": 3771000,
            "total_guests": 1001,
            "avg_daily_rate": 1127.3,
            "avg_stay_days": 10.8,
            "top_room_types": {"Suite": 2119671, "Spa Executive": 1722396, "Superior Double": 1339521},
            "revenue_by_season": {"High": 5078921, "Mid": 3710287, "Low": 2528792},
            "top_countries": {"Denmark": 112, "Germany": 95, "Sweden": 88, "Norway": 83, "UK": 77},
        }

# ---------- HENT DATA ---------- muligvis overflødig hvis utils bruges
overview = fetch_json(f"{API_ANALYTICS}/overview")
monthly = fetch_json(f"{API_ANALYTICS}/monthly_revenue")

# ---------- HEADER ----------
st.title("Hotel Kong Arthur – Executive Overview")
st.markdown(
    "Et samlet overblik over hotellets performance på tværs af værelser, gæster og bar-omsætning. "
    "Dashboardet opdateres automatisk via API Gatewayen og giver ledelsen real-time indsigt i nøgletal."
)
st.divider()

# ---------- KPI’ER ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Samlet omsætning", f"{overview['total_revenue_all']:,.0f} DKK")
col2.metric("🛏️ Gns. dagspris (ADR)", f"{overview['avg_daily_rate']:,.0f} DKK")
col3.metric("📆 Gns. ophold", f"{overview['avg_stay_days']:,.1f} dage")
col4.metric("👥 Gæster", f"{overview['total_guests']:,.0f}")

st.divider()

# ---------- MÅNEDLIG OMSÆTNING ----------
st.subheader("Årets månedlige omsætning")
if "monthly_revenue_dkk" in monthly:
    # Lav DataFrame
    df_month = pd.DataFrame(list(monthly["monthly_revenue_dkk"].items()), columns=["Måned", "Omsætning (DKK)"])
    
    # Definer korrekt månedrækkefølge
    month_order = [
        "Januar", "Februar", "Marts", "April", "Maj", "Juni",
        "Juli", "August", "September", "Oktober", "November", "December"
    ]
    
    # Sørg for korrekt rækkefølge selvom nogle måneder mangler
    df_month["Måned"] = pd.Categorical(df_month["Måned"], categories=month_order, ordered=True)
    df_month.sort_values("Måned", inplace=True)
    df_month.set_index("Måned", inplace=True)

    # Tegn linjegraf
    st.line_chart(df_month)

else:
    st.info("Ingen månedlige data tilgængelige.")

# ---------- TOP ROOM TYPES ----------
st.subheader("Mest indbringende værelsestyper")
df_rooms = pd.DataFrame(list(overview["top_room_types"].items()), columns=["Værelsestype", "Omsætning (DKK)"])
st.bar_chart(df_rooms.set_index("Værelsestype"))

# ---------- SÆSONOMSÆTNING ----------
st.subheader("Omsætning pr. sæson")
df_season = pd.DataFrame(list(overview["revenue_by_season"].items()), columns=["Sæson", "Omsætning (DKK)"])
st.bar_chart(df_season.set_index("Sæson"))

# ---------- TOPLANDE ----------
st.subheader("Gæster fordelt på lande")

df_country = pd.DataFrame(list(overview["top_countries"].items()), columns=["Land", "Antal gæster"])

if df_country.empty:
    st.info("Ingen gæstedata tilgængelig.")
else:
    df_country = df_country.sort_values("Antal gæster", ascending=False)

    chart_country = (
        alt.Chart(df_country)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Antal gæster:Q", title="Antal gæster"),
            y=alt.Y("Land:N", sort="-x", title=None),
            color=alt.Color("Antal gæster:Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["Land", "Antal gæster"]
        )
        .properties(height=max(400, len(df_country) * 25))
    )
    st.altair_chart(chart_country, use_container_width=True)

# ---------- NARRATIV KONKLUSION ----------
st.divider()
top_season = max(overview["revenue_by_season"], key=overview["revenue_by_season"].get)
top_room = max(overview["top_room_types"], key=overview["top_room_types"].get)
st.markdown(
    f"**📊 Indsigt:** Højsæsonen **{top_season}** og værelsetypen **{top_room}** "
    f"driver størstedelen af indtjeningen. Kombineret generer de over "
    f"{round(overview['total_revenue_all']/1_000_000,1)} mio. DKK årligt."
)

st.caption("Data via: API Gateway → Analytics Service → Room/Bar/Guest/Reservation microservices")
