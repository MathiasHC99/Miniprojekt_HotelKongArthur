import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bar Dashboard – Hotel Kong Arthur", layout="wide")
st.title("Bar Dashboard (Mockdata)")

# --- MOCKDATA ---
data = [
    {"drink_name": "Espresso", "category": "Coffee", "price_dkk": 35, "units_sold": 240},
    {"drink_name": "Cappuccino", "category": "Coffee", "price_dkk": 45, "units_sold": 190},
    {"drink_name": "Mojito", "category": "Cocktail", "price_dkk": 95, "units_sold": 110},
    {"drink_name": "Old Fashioned", "category": "Cocktail", "price_dkk": 110, "units_sold": 80},
    {"drink_name": "Latte", "category": "Coffee", "price_dkk": 40, "units_sold": 210},
]
bar = pd.DataFrame(data)
bar["total_revenue"] = bar["price_dkk"] * bar["units_sold"]

total_revenue = float(bar["total_revenue"].sum())
avg_price = float(bar["price_dkk"].mean())

k1, k2 = st.columns(2)
k1.metric("Total omsætning (DKK)", f"{total_revenue:,.0f}")
k2.metric("Gns. pris pr. drink (DKK)", f"{avg_price:,.2f}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 5 drinks (omsætning)")
    top = bar.sort_values("total_revenue", ascending=False).head(5)
    st.bar_chart(top.set_index("drink_name")["total_revenue"])

with col2:
    st.subheader("Omsætning pr. kategori")
    by_cat = bar.groupby("category")["total_revenue"].sum()
    st.bar_chart(by_cat)
