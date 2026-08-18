import pandas as pd
import numpy as np
import sqlite3
import os
import re
from datetime import datetime

RAW_PATH = os.path.join("dataset", "market_analysis_cars_nov2025.csv")
DB_PATH = os.path.join("data_warehouse.db")

KNOWN_BRANDS = [
    "Mercedes-Benz", "Alfa Romeo", "Land Rover", "Aston Martin",
    "Rolls-Royce", "Great Wall",
    "Toyota", "Honda", "Ford", "BMW", "Audi", "Volkswagen", "Mercedes",
    "Peugeot", "Renault", "Opel", "Fiat", "Nissan", "Hyundai", "Kia",
    "Citroën", "Citroen", "Mazda", "Suzuki", "Volvo", "Seat", "Skoda",
    "Dacia", "Mini", "Jeep", "Mitsubishi", "Subaru", "Lexus",
    "Porsche", "Jaguar", "Chrysler", "Dodge", "Chevrolet", "Tesla",
    "Cupra", "DS", "Saab", "Smart", "SsangYong", "Iveco",
    "Piaggio", "MAN", "Truck", "Autocarro", "Lada",
]


def extract_brand(title: str) -> str:
    if not isinstance(title, str):
        return "Desconhecida"
    t = title.strip()
    for brand in KNOWN_BRANDS:
        if t.lower().startswith(brand.lower()):
            return brand
    parts = t.split()
    if parts:
        return parts[0]
    return "Desconhecida"


def extract_model(title: str, brand: str) -> str:
    if not isinstance(title, str):
        return "Desconhecido"
    t = title.strip()
    b_len = len(brand)
    rest = t[b_len:].strip()
    rest = re.sub(r"^\s*[-–]\s*", "", rest)
    rest = re.sub(r"^\d[\d.]*\s*", "", rest)
    rest = re.sub(r"^(dCi|TCe|TSI|TFSI|BlueHDi|PureTech|i-VTEC|VVT-i|HSD|T-GDi|MPI|CRDI|CDI|TDI|SDI|JTS|TS)\s*", "", rest, flags=re.IGNORECASE)
    rest = rest.strip()
    tokens = rest.split()
    if not tokens:
        return "Desconhecido"
    model_tokens = []
    stop = {"pack", "exclusive", "style", "comfort", "business", "advance",
            "active", "lounge", "s-line", "amg", "line", "edition", "grande",
            "sport", "tech", "family", "urban", "premium", "standard",
            "base", "express", "intense", "initiale", "zen", "intens",
            "n-line", "fr", "gt", "gti", "rs", "r-line", "suv", "coupé",
            "cabriolet", "break", "van", "sedan"}
    for tok in tokens:
        if tok.lower().rstrip(",.") in stop:
            break
        model_tokens.append(tok)
        if len(model_tokens) >= 3:
            break
    return " ".join(model_tokens) if model_tokens else "Desconhecido"


def classify_fuel(fuel: str) -> str:
    if not isinstance(fuel, str):
        return "Outro"
    f = fuel.strip().lower()
    if "diesel" in f:
        return "Diesel"
    if "electric" in f or "eletric" in f:
        return "Elétrico"
    if "plug" in f:
        return "Híbrido Plug-In"
    if "hybrid" in f or "híbrid" in f:
        return "Híbrido"
    if "gasoline" in f or "gasolina" in f or "petrol" in f:
        return "Gasolina"
    if "lpg" in f or "gpl" in f:
        return "GPL"
    return "Outro"


def classify_transmission(trans: str) -> str:
    if not isinstance(trans, str):
        return "Outro"
    t = trans.strip().lower()
    if "auto" in t or "automat" in t or "dsg" in t or "tiptronic" in t:
        return "Automática"
    if "manual" in t:
        return "Manual"
    return "Outro"


def build_warehouse():
    print("Lendo dataset bruto...")
    df = pd.read_csv(RAW_PATH)
    print(f"  Registos carregados: {len(df)}")

    print("A extrair marcas e modelos...")
    df["brand"] = df["title"].apply(extract_brand)
    df["model"] = df.apply(lambda r: extract_model(r["title"], r["brand"]), axis=1)

    print("A classificar combustível e transmissão...")
    df["fuel_type"] = df["fuel"].apply(classify_fuel)
    df["trans_type"] = df["transmission"].apply(classify_transmission)

    current_year = datetime.now().year
    df["vehicle_age"] = current_year - df["year"]

    # --- Dimensões ---
    print("A criar dimensões...")

    dim_brand = df[["brand"]].drop_duplicates().reset_index(drop=True)
    dim_brand["brand_id"] = dim_brand.index + 1
    dim_brand = dim_brand[["brand_id", "brand"]]

    dim_model = df[["brand", "model"]].drop_duplicates().reset_index(drop=True)
    dim_model["model_id"] = dim_model.index + 1
    brand_map = dict(zip(dim_brand["brand"], dim_brand["brand_id"]))
    dim_model["brand_id"] = dim_model["brand"].map(brand_map)

    dim_fuel = df[["fuel_type"]].drop_duplicates().reset_index(drop=True)
    dim_fuel["fuel_id"] = dim_fuel.index + 1
    dim_fuel = dim_fuel[["fuel_id", "fuel_type"]]

    dim_trans = df[["trans_type"]].drop_duplicates().reset_index(drop=True)
    dim_trans["trans_id"] = dim_trans.index + 1
    dim_trans = dim_trans[["trans_id", "trans_type"]]

    dim_location = df[["location"]].drop_duplicates().reset_index(drop=True)
    dim_location["location_id"] = dim_location.index + 1
    dim_location = dim_location[["location_id", "location"]]

    # --- Tabela de fatos ---
    print("A criar tabela de factos...")
    model_map = dict(zip(
        dim_model["brand"].astype(str) + "|" + dim_model["model"],
        dim_model["model_id"]
    ))
    dim_model = dim_model[["model_id", "brand_id", "model"]]
    fuel_map = dict(zip(dim_fuel["fuel_type"], dim_fuel["fuel_id"]))
    trans_map = dict(zip(dim_trans["trans_type"], dim_trans["trans_id"]))
    loc_map = dict(zip(dim_location["location"], dim_location["location_id"]))

    fact = pd.DataFrame()
    fact["listing_id"] = df["index"]
    fact["model_id"] = df.apply(
        lambda r: model_map.get(f"{r['brand']}|{r['model']}", None), axis=1
    )
    fact["fuel_id"] = df["fuel_type"].map(fuel_map)
    fact["trans_id"] = df["trans_type"].map(trans_map)
    fact["location_id"] = df["location"].map(loc_map)
    fact["year"] = df["year"]
    fact["price"] = df["price"]
    fact["mileage"] = df["mileage"]
    fact["displacement"] = df["displacement"]
    fact["horsepower"] = df["horsepower"]
    fact["vehicle_age"] = df["vehicle_age"]

    # --- Gravar em SQLite ---
    print(f"A gravar data warehouse em {DB_PATH}...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    dim_brand.to_sql("dim_brand", conn, index=False)
    dim_model.to_sql("dim_model", conn, index=False)
    dim_fuel.to_sql("dim_fuel", conn, index=False)
    dim_trans.to_sql("dim_transmission", conn, index=False)
    dim_location.to_sql("dim_location", conn, index=False)
    fact.to_sql("fact_listings", conn, index=False)

    # Criar índices
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_model ON fact_listings(model_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_fuel ON fact_listings(fuel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_trans ON fact_listings(trans_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_year ON fact_listings(year)")
    conn.commit()
    conn.close()

    print("Data warehouse criado com sucesso!")
    print(f"  Marcas: {len(dim_brand)}")
    print(f"  Modelos: {len(dim_model)}")
    print(f"  Tipos de combustível: {len(dim_fuel)}")
    print(f"  Tipos de transmissão: {len(dim_trans)}")
    print(f"  Localizações: {len(dim_location)}")
    print(f"  Factos: {len(fact)}")


if __name__ == "__main__":
    build_warehouse()
