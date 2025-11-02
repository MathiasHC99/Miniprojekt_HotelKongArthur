import os, requests, streamlit as st

API_BASE = os.getenv("GATEWAY_URL", "http://localhost:5055")

def get_json(path: str):
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Kunne ikke hente data fra {url}\n{e}")
        return None
