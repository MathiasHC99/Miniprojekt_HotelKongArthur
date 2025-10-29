import os, requests, streamlit as st, datetime, random

# Standard API-adresse – peger mod localhost mens I udvikler
API = os.getenv("API_URL", "http://localhost:8000")

def fetch_json(path: str):
    """Forsøger at hente JSON fra API. Hvis ingen forbindelse, returneres mock-data."""
    url = f"{API}{path}"
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Kunne ikke hente {path} fra {url}. Viser mock-data i stedet. ({e})")
        return mock_data(path)

def mock_data(path: str):
    """Mock-data til udvikling uden backend."""
    if path == "/kpis/top":
        return {
            "year_revenue_dkk": 1832450,
            "top_room_types": [
                {"room_type": "Deluxe Suite", "revenue": 642000},
                {"room_type": "Standard Double", "revenue": 382000},
                {"room_type": "Economy Single", "revenue": 241000},
                {"room_type": "Family Room", "revenue": 181000},
                {"room_type": "Penthouse", "revenue": 139000},
            ],
            "top_countries": [
                {"country": "Denmark", "revenue": 712000},
                {"country": "Germany", "revenue": 433000},
                {"country": "UK", "revenue": 254000},
                {"country": "Sweden", "revenue": 192000},
                {"country": "Norway", "revenue": 144000},
            ],
        }
    elif path == "/kpis/rooms":
        base = datetime.date(2025, 10, 1)
        return [
            {
                "date": str(base + datetime.timedelta(days=i)),
                "occupancy": round(random.uniform(0.6, 1.0), 2),
                "ADR": round(random.uniform(800, 1500), 2),
                "RevPAR": round(random.uniform(500, 900), 2),
            }
            for i in range(10)
        ]
    elif path == "/bar/summary":
        return {
            "total_revenue_dkk": 324500,
            "by_product": [
                {"product": "Espresso", "revenue": 85000},
                {"product": "Cappuccino", "revenue": 62000},
                {"product": "Latte", "revenue": 59000},
                {"product": "Mojito", "revenue": 48000},
                {"product": "Old Fashioned", "revenue": 40500},
            ],
        }
    return []
