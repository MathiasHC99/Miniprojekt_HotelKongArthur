import streamlit as st
import pandas as pd
import altair as alt
import requests
from utils import API_BASE, fetch_json

# ---------- KONFIG ----------
st.set_page_config(page_title="Bar Dashboard – Hotel Kong Arthur", layout="wide")
API_BAR = f"{API_BASE}/bar"

# ---------- HJÆLPEFUNKTION ----------
@st.cache_data(ttl=60)
def fetch_json(endpoint):
    try:
        r = requests.get(endpoint, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente data fra {endpoint}. Viser mock-data. ({e})")
        return {
            "total_revenue_dkk": 5123000,
            "total_drinks": 30,
            "avg_price": 150,
            "top_drink": "Espresso Martini",
            "category_revenue": {"Cocktail": 2300000, "Beer": 1500000, "Wine": 900000, "Softdrink": 420000},
            "drinks": [
                {"drink_name": "Espresso Martini", "category": "Cocktail", "price_dkk": 165, "units_sold": 780, "total_revenue": 128700},
                {"drink_name": "Gin & Tonic", "category": "Cocktail", "price_dkk": 155, "units_sold": 650, "total_revenue": 100750},
                {"drink_name": "Carlsberg Pilsner", "category": "Beer", "price_dkk": 75, "units_sold": 1200, "total_revenue": 90000},
            ]
        }

# ---------- HENT DATA ----------

summary = fetch_json(f"{API_BAR}/bar/summary")
drinks_data = fetch_json(f"{API_BAR}/bar/drinks")


# ---------- HEADER ----------
st.title("Bar Dashboard")
st.markdown(
    "Få et fuldt overblik over barens salg, omsætning og mest populære drikkevarer. "
    "Dashboardet samler data direkte fra barens system via API Gatewayen."
)
st.divider()

# ---------- KPI’ER ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Samlet omsætning", f"{summary['total_revenue_dkk']:,.0f} DKK")
col2.metric("🍹 Antal drinks", summary['total_drinks'])
col3.metric("🏆 Mest solgte drink", summary['top_drink'])
col4.metric("💵 Gns. pris", f"{summary['avg_price']:,.0f} DKK")

st.divider()

# ---------- OMSÆTNING PR. KATEGORI ----------
st.subheader("Omsætning pr. kategori")

df_cat = pd.DataFrame(list(summary["category_revenue"].items()), columns=["Kategori", "Omsætning (DKK)"])
chart_cat = (
    alt.Chart(df_cat)
    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    .encode(
        x=alt.X("Kategori:N", title="Kategori"),
        y=alt.Y("Omsætning (DKK):Q", title="Omsætning (DKK)"),
        color=alt.Color("Kategori:N", scale=alt.Scale(scheme="tealblues")),
        tooltip=["Kategori", "Omsætning (DKK)"]
    )
    .properties(height=400)
)
st.altair_chart(chart_cat, use_container_width=True)

st.divider()


# ---------- TOP 10 DRINKS ----------
st.subheader("Top 10 mest populære drinks")

# Sikrer korrekt dataframe uanset om API returnerer en liste eller et dict
if isinstance(drinks_data, list):
    df_drinks = pd.DataFrame(drinks_data)
elif isinstance(drinks_data, dict) and "drinks" in drinks_data:
    df_drinks = pd.DataFrame(drinks_data["drinks"])
else:
    df_drinks = pd.DataFrame()


if not df_drinks.empty:
    df_drinks = df_drinks.sort_values("units_sold", ascending=False).head(10)
    chart_drinks = (
        alt.Chart(df_drinks)
        .mark_bar()
        .encode(
            x=alt.X("units_sold:Q", title="Antal solgte"),
            y=alt.Y("drink_name:N", sort="-x", title=None),
            color=alt.Color("category:N", legend=alt.Legend(title="Kategori")),
            tooltip=["drink_name", "category", "units_sold", "total_revenue"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart_drinks, use_container_width=True)
else:
    st.info("Ingen drinkdata tilgængelig.")

st.divider()

# ---------- AUTOMATISK INDSIGT ----------
if not df_drinks.empty:
    top_drink = df_drinks.iloc[0]["drink_name"]
    st.markdown(
        f"**Indsigt:** Drinken *{top_drink}* er den mest populære i baren og bidrager væsentligt til omsætningen. "
        f"Cocktails udgør samlet set omkring **{round((summary['category_revenue'].get('Cocktail', 0) / summary['total_revenue_dkk']) * 100, 1)}%** af barens indtjening."
    )

st.caption("Data via: API Gateway → Bar Service → SQLite database")
