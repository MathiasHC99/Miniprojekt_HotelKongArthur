import pandas as pd, os

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "NamesRoomsWithMonths4.csv")
df = pd.read_csv(CSV_PATH, sep=";")

df["Country"] = df["Country"].astype(str).str.strip().str.title()
df = df[df["Country"].notna() & (df["Country"].str.strip() != "") & (df["Country"].str.lower() != "nan")]
df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df = df.dropna(subset=["Price"])

# Brug direkte pris som revenue for at matche Tableau
df["Revenue"] = df["Price"]

by_country = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False).round(2)

print(by_country.head(10))
print("\nAntal unikke lande:", df["Country"].nunique())
print("Total:", round(df["Revenue"].sum(), 2))
