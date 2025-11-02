import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Guests & Country – Hotel Kong Arthur", layout="wide")
st.title("Guests & Country (Mockdata)")

# --- MOCKDATA ---
data = [
    {"country": "Denmark", "room_type": "Standard", "price": 1100},
    {"country": "Sweden", "room_type": "Superior", "price": 2100},
    {"country": "Norway", "room_type": "Suite", "price": 3200},
    {"country": "Germany", "room_type": "Junior Suite", "price": 2500},
    {"country": "Denmark", "room_type": "Superior", "price": 1800},
]
df = pd.DataFrame(data)

# --- Indtjening pr. land ---
by_country = df.groupby("country")["price"].sum().sort_values(ascending=False)
st.subheader("Indtjening pr. land")
st.bar_chart(by_country)

# --- Heatmap Land × Værelsestype ---
pivot = df.pivot_table(index="country", columns="room_type", values="price", aggfunc="sum").fillna(0)
melted = pivot.reset_index().melt("country", var_name="room_type", value_name="revenue_dkk")

heat = (
    alt.Chart(melted)
    .mark_rect()
    .encode(
        x="room_type:O",
        y="country:O",
        color=alt.Color("revenue_dkk:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["country", "room_type", "revenue_dkk"],
    )
    .properties(height=400)
)
st.subheader("Heatmap – Land × Værelsestype")
st.altair_chart(heat, use_container_width=True)
