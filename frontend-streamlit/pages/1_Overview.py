import streamlit as st
import pandas as pd

st.set_page_config(page_title="Overview – Hotel Kong Arthur", layout="wide")
st.title("Overview (Mockdata)")

# --- MOCKDATA ---
data = [
    {"room_type": "Standard", "country": "Denmark", "price": 1200},
    {"room_type": "Suite", "country": "Germany", "price": 2800},
    {"room_type": "Superior", "country": "Norway", "price": 2000},
    {"room_type": "Standard", "country": "Denmark", "price": 1100},
    {"room_type": "Junior Suite", "country": "Sweden", "price": 2400},
]
df = pd.DataFrame(data)

# --- Beregninger ---
total_revenue = df["price"].sum()
rt = df.groupby("room_type")["price"].sum().sort_values(ascending=False)
co = df.groupby("country")["price"].sum().sort_values(ascending=False)

c1, c2, c3 = st.columns(3)
c1.metric("Årsindtjening (DKK)", f"{total_revenue:,.0f}")
c2.metric("Top room type", rt.index[0])
c3.metric("Top country", co.index[0])

colA, colB = st.columns(2)
with colA:
    st.subheader("Top værelsestyper (indtjening)")
    st.bar_chart(rt)

with colB:
    st.subheader("Top lande (indtjening)")
    st.bar_chart(co)
