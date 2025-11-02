import streamlit as st
import pandas as pd

st.set_page_config(page_title="Room Insights – Hotel Kong Arthur", layout="wide")
st.title("Room Insights (Mockdata)")

# --- MOCKDATA ---
data = [
    {"room_type": "Standard", "season": "Winter", "days_rented": 3, "price": 1000},
    {"room_type": "Superior", "season": "Summer", "days_rented": 5, "price": 2100},
    {"room_type": "Suite", "season": "Summer", "days_rented": 2, "price": 3200},
    {"room_type": "Junior Suite", "season": "Spring", "days_rented": 4, "price": 2500},
    {"room_type": "Standard", "season": "Autumn", "days_rented": 3, "price": 1100},
]
df = pd.DataFrame(data)

k1, k2, k3 = st.columns(3)
k1.metric("Total bookings", f"{len(df):,}")
k2.metric("Gns. pris (DKK)", f"{df['price'].mean():,.2f}")
k3.metric("Gns. dage lejet", f"{df['days_rented'].mean():,.2f}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Indtjening pr. værelsestype")
    st.bar_chart(df.groupby("room_type")["price"].sum())

with col2:
    st.subheader("Indtjening pr. sæson")
    st.bar_chart(df.groupby("season")["price"].sum())

st.metric("Total indtjening (DKK)", f"{df['price'].sum():,.0f}")
