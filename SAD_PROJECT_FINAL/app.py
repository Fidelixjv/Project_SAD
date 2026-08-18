import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

st.set_page_config(page_title="SAD - Mercado de Automóveis PT", layout="wide")

DB_PATH = os.path.join(os.path.dirname(__file__), "data_warehouse.db")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT
            f.listing_id,
            f.year,
            f.price,
            f.mileage,
            f.displacement,
            f.horsepower,
            f.vehicle_age,
            b.brand,
            m.model,
            fl.fuel_type,
            t.trans_type,
            l.location
        FROM fact_listings f
        JOIN dim_model m ON f.model_id = m.model_id
        JOIN dim_brand b ON m.brand_id = b.brand_id
        JOIN dim_fuel fl ON f.fuel_id = fl.fuel_id
        JOIN dim_transmission t ON f.trans_id = t.trans_id
        JOIN dim_location l ON f.location_id = l.location_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def main():
    st.title("Sistema de Apoio a Decisao - Mercado de Automoveis em Portugal")
    st.caption("Equipe: Joao Vitor Fidelix da Silva | Eric Reullyson Silva Leite | Rafael dos Santos Sousa")
    st.markdown("---")

    df = load_data()

    # --- Sidebar Filtros ---
    st.sidebar.header("Filtros")

    brands = sorted(df["brand"].unique())
    sel_brands = st.sidebar.multiselect("Marca", brands, default=[])

    fuels = sorted(df["fuel_type"].unique())
    sel_fuels = st.sidebar.multiselect("Combustivel", fuels, default=fuels)

    trans_options = sorted(df["trans_type"].unique())
    sel_trans = st.sidebar.multiselect("Transmissao", trans_options, default=trans_options)

    year_min = int(df["year"].min())
    year_max = int(df["year"].max())
    sel_year = st.sidebar.slider("Ano", year_min, year_max, (year_min, year_max))

    price_max = int(df["price"].max())
    sel_price = st.sidebar.slider("Preco (EUR)", 0, price_max, (0, price_max))

    mileage_max = int(df["mileage"].max())
    sel_mileage = st.sidebar.slider("Quilometragem (km)", 0, int(mileage_max), (0, int(mileage_max)))

    # Filtragem
    filtered = df.copy()
    if sel_brands:
        filtered = filtered[filtered["brand"].isin(sel_brands)]
    filtered = filtered[filtered["fuel_type"].isin(sel_fuels)]
    filtered = filtered[filtered["trans_type"].isin(sel_trans)]
    filtered = filtered[(filtered["year"] >= sel_year[0]) & (filtered["year"] <= sel_year[1])]
    filtered = filtered[(filtered["price"] >= sel_price[0]) & (filtered["price"] <= sel_price[1])]
    filtered = filtered[(filtered["mileage"] >= sel_mileage[0]) & (filtered["mileage"] <= sel_mileage[1])]

    if filtered.empty:
        st.warning("Nenhum registo corresponde aos filtros selecionados.")
        return

    # --- KPIs ---
    st.subheader("Metricas Gerais")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Anuncios", f"{len(filtered):,}")
    c2.metric("Preco Medio", f"EUR {filtered['price'].mean():,.0f}")
    c3.metric("Preco Mediano", f"EUR {filtered['price'].median():,.0f}")
    c4.metric("Preco Minimo", f"EUR {filtered['price'].min():,.0f}")
    c5.metric("Preco Maximo", f"EUR {filtered['price'].max():,.0f}")
    c6.metric("Idade Media", f"{filtered['vehicle_age'].mean():.1f} anos")

    c7, c8, c9 = st.columns(3)
    c7.metric("Km Media", f"{filtered['mileage'].mean():,.0f} km")
    c8.metric("Km Mediana", f"{filtered['mileage'].median():,.0f} km")
    c9.metric("Marcas Distintas", f"{filtered['brand'].nunique()}")

    st.markdown("---")

    # ==================== Pergunta 1 ====================
    st.header("1. Quais sao as marcas de automoveis mais anunciadas em Portugal?")

    brand_counts = filtered["brand"].value_counts().head(20).reset_index()
    brand_counts.columns = ["Marca", "Quantidade"]

    col_a, col_b = st.columns(2)
    with col_a:
        fig_bar = px.bar(
            brand_counts, x="Marca", y="Quantidade",
            color="Quantidade", color_continuous_scale="Blues",
            title="Top 20 Marcas por Numero de Anuncios"
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        fig_pie = px.pie(
            brand_counts.head(10), names="Marca", values="Quantidade",
            title="Participacao das Top 10 Marcas"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(brand_counts, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==================== Pergunta 2 ====================
    st.header("2. Qual e o preco medio dos carros por marca e modelo?")

    top_brands = filtered["brand"].value_counts().head(15).index.tolist()
    brand_price = (
        filtered[filtered["brand"].isin(top_brands)]
        .groupby("brand")["price"]
        .agg(["mean", "median", "min", "max", "count"])
        .reset_index()
    )
    brand_price.columns = ["Marca", "Preco Medio", "Preco Mediano", "Minimo", "Maximo", "N"]
    brand_price = brand_price.sort_values("Preco Medio", ascending=False)

    fig_bp = px.bar(
        brand_price, x="Marca", y="Preco Medio",
        error_y=brand_price["Maximo"] - brand_price["Preco Medio"],
        color="Preco Medio", color_continuous_scale="RdYlGn_r",
        title="Preco Medio por Marca (Top 15 com mais anuncios)"
    )
    fig_bp.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bp, use_container_width=True)

    st.dataframe(brand_price.style.format({
        "Preco Medio": "EUR {:,.0f}",
        "Preco Mediano": "EUR {:,.0f}",
        "Minimo": "EUR {:,.0f}",
        "Maximo": "EUR {:,.0f}"
    }), use_container_width=True, hide_index=True)

    # Preco medio por modelo dentro de uma marca selecionada
    st.subheader("Preco Medio por Modelo")
    selected_brand = st.selectbox("Selecione uma marca para ver os modelos:", top_brands)
    model_price = (
        filtered[filtered["brand"] == selected_brand]
        .groupby("model")["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    model_price.columns = ["Modelo", "Preco Medio", "Preco Mediano", "N"]
    model_price = model_price.sort_values("N", ascending=False)

    fig_mp = px.bar(
        model_price.head(15), x="Modelo", y="Preco Medio",
        color="N", color_continuous_scale="Teal",
        title=f"Preco Medio por Modelo - {selected_brand}"
    )
    st.plotly_chart(fig_mp, use_container_width=True)

    st.markdown("---")

    # ==================== Pergunta 3 ====================
    st.header("3. Veiculos mais novos possuem precos significativamente maiores?")

    age_price = (
        filtered.groupby("vehicle_age")["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    age_price.columns = ["Idade (anos)", "Preco Medio", "Preco Mediano", "N"]

    col_a, col_b = st.columns(2)
    with col_a:
        fig_age = px.scatter(
            age_price, x="Idade (anos)", y="Preco Medio",
            size="N", color="Preco Medio",
            color_continuous_scale="RdYlGn_r",
            title="Relacao entre Idade do Veiculo e Preco Medio",
            size_max=40
        )
        st.plotly_chart(fig_age, use_container_width=True)

    with col_b:
        fig_box = px.box(
            filtered, x="vehicle_age", y="price",
            title="Distribuicao de Preco por Idade",
            labels={"vehicle_age": "Idade (anos)", "price": "Preco (EUR)"}
        )
        fig_box.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_box, use_container_width=True)

    st.dataframe(age_price.sort_values("Idade (anos)"), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==================== Pergunta 4 ====================
    st.header("4. Quais caracteristicas tem maior influencia no valor do automovel?")

    st.subheader("Analise por Combustivel")
    col_a, col_b = st.columns(2)
    with col_a:
        fuel_stats = (
            filtered.groupby("fuel_type")["price"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        fuel_stats.columns = ["Combustivel", "Preco Medio", "Preco Mediano", "N"]
        fuel_stats = fuel_stats.sort_values("Preco Medio", ascending=False)

        fig_fuel = px.bar(
            fuel_stats, x="Combustivel", y="Preco Medio",
            color="Combustivel", title="Preco Medio por Tipo de Combustivel"
        )
        st.plotly_chart(fig_fuel, use_container_width=True)

    with col_b:
        fig_fuel_box = px.box(
            filtered, x="fuel_type", y="price",
            color="fuel_type",
            title="Distribuicao de Preco por Combustivel",
            labels={"price": "Preco (EUR)"}
        )
        st.plotly_chart(fig_fuel_box, use_container_width=True)

    st.subheader("Analise por Transmissao")
    col_a, col_b = st.columns(2)
    with col_a:
        trans_stats = (
            filtered.groupby("trans_type")["price"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        trans_stats.columns = ["Transmissao", "Preco Medio", "Preco Mediano", "N"]

        fig_trans = px.bar(
            trans_stats, x="Transmissao", y="Preco Medio",
            color="Transmissao", title="Preco Medio por Transmissao"
        )
        st.plotly_chart(fig_trans, use_container_width=True)

    with col_b:
        fig_trans_box = px.box(
            filtered, x="trans_type", y="price",
            color="trans_type",
            title="Distribuicao de Preco por Transmissao",
            labels={"price": "Preco (EUR)"}
        )
        st.plotly_chart(fig_trans_box, use_container_width=True)

    st.subheader("Analise de Correlacao (Caracteristicas Numericas)")
    numeric_cols = ["price", "year", "mileage", "vehicle_age", "displacement", "horsepower"]
    corr_df = filtered[numeric_cols].dropna()
    corr = corr_df.corr()

    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r",
        title="Matriz de Correlacao entre Variaveis",
        labels=dict(color="Correlacao")
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Importancia: Quilometragem vs Preco por Combustivel")
    fig_mil = px.scatter(
        filtered.sample(min(3000, len(filtered)), random_state=42),
        x="mileage", y="price", color="fuel_type",
        opacity=0.5, title="Quilometragem vs Preco",
        labels={"mileage": "Quilometragem (km)", "price": "Preco (EUR)"},
        trendline="ols"
    )
    st.plotly_chart(fig_mil, use_container_width=True)

    st.subheader("Importancia: Potencia (CV) vs Preco")
    fig_hp = px.scatter(
        filtered[filtered["horsepower"].notna()].sample(min(3000, len(filtered)), random_state=42),
        x="horsepower", y="price", color="fuel_type",
        opacity=0.5, title="Potencia vs Preco",
        labels={"horsepower": "Potencia (CV)", "price": "Preco (EUR)"},
        trendline="ols"
    )
    st.plotly_chart(fig_hp, use_container_width=True)

    st.markdown("---")

    # ==================== Pergunta 5 ====================
    st.header("5. Quais modelos apresentam melhor relacao entre preco e ano de fabricacao?")

    model_analysis = (
        filtered.groupby(["brand", "model"])
        .agg(
            preco_medio=("price", "mean"),
            ano_medio=("year", "mean"),
            km_media=("mileage", "mean"),
            n_anuncios=("price", "count")
        )
        .reset_index()
    )

    min_anuncios = st.slider(
        "Minimo de anuncios por modelo para analise:", 1, 50, 5
    )
    model_filtered = model_analysis[model_analysis["n_anuncios"] >= min_anuncios].copy()

    model_filtered["valor_ano_ratio"] = model_filtered["preco_medio"] / model_filtered["ano_medio"]

    st.subheader("Modelos com Melhor Relacao Preco/Ano (Mais Novos e Mais Baratos)")
    best_value = model_filtered.nsmallest(20, "valor_ano_ratio")
    fig_bv = px.scatter(
        model_filtered, x="ano_medio", y="preco_medio",
        size="n_anuncios", color="valor_ano_ratio",
        color_continuous_scale="RdYlGn",
        hover_name="model", hover_data=["brand", "km_media"],
        title="Relacao Preco vs Ano (tamanho = n. anuncios, cor = ratio)",
        labels={"ano_medio": "Ano Medio", "preco_medio": "Preco Medio (EUR)"}
    )
    st.plotly_chart(fig_bv, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top 20 - Melhor Custo-Beneficio")
        st.dataframe(
            best_value[["brand", "model", "preco_medio", "ano_medio", "km_media", "n_anuncios", "valor_ano_ratio"]].style.format({
                "preco_medio": "EUR {:,.0f}",
                "ano_medio": "{:.0f}",
                "km_media": "{:,.0f} km",
                "valor_ano_ratio": "{:.1f}"
            }),
            use_container_width=True, hide_index=True
        )

    with col_b:
        st.subheader("Top 20 - Mais Caros vs Antigos")
        worst_value = model_filtered.nlargest(20, "valor_ano_ratio")
        st.dataframe(
            worst_value[["brand", "model", "preco_medio", "ano_medio", "km_media", "n_anuncios", "valor_ano_ratio"]].style.format({
                "preco_medio": "EUR {:,.0f}",
                "ano_medio": "{:.0f}",
                "km_media": "{:,.0f} km",
                "valor_ano_ratio": "{:.1f}"
            }),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # ==================== Metricas Extras ====================
    st.header("Metricas Complementares")

    st.subheader("Distribuicao por Tipo de Combustivel")
    fuel_dist = filtered["fuel_type"].value_counts().reset_index()
    fuel_dist.columns = ["Combustivel", "Quantidade"]
    fig_fd = px.pie(fuel_dist, names="Combustivel", values="Quantidade",
                    title="Distribuicao de Anuncios por Combustivel")
    st.plotly_chart(fig_fd, use_container_width=True)

    st.subheader("Distribuicao por Transmissao")
    trans_dist = filtered["trans_type"].value_counts().reset_index()
    trans_dist.columns = ["Transmissao", "Quantidade"]
    fig_td = px.pie(trans_dist, names="Transmissao", values="Quantidade",
                    title="Distribuicao de Anuncios por Transmissao")
    st.plotly_chart(fig_td, use_container_width=True)

    st.subheader("Quilometragem Media por Marca")
    top_brands_km = filtered["brand"].value_counts().head(15).index.tolist()
    brand_km = (
        filtered[filtered["brand"].isin(top_brands_km)]
        .groupby("brand")["mileage"]
        .mean()
        .reset_index()
    )
    brand_km.columns = ["Marca", "Km Media"]
    brand_km = brand_km.sort_values("Km Media", ascending=False)

    fig_km = px.bar(brand_km, x="Marca", y="Km Media",
                    color="Km Media", color_continuous_scale="Oranges",
                    title="Quilometragem Media por Marca (Top 15)")
    fig_km.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_km, use_container_width=True)

    st.subheader("Top 10 Modelos Mais Anunciados")
    top_models = filtered.value_counts(["brand", "model"]).head(10).reset_index()
    top_models.columns = ["Marca", "Modelo", "Quantidade"]
    fig_tm = px.bar(top_models, x="Modelo", y="Quantidade", color="Marca",
                    title="Top 10 Modelos Mais Anunciados")
    st.plotly_chart(fig_tm, use_container_width=True)

    # --- Dados brutos ---
    st.markdown("---")
    with st.expander("Ver dados filtrados"):
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "dados_filtrados.csv", "text/csv")


if __name__ == "__main__":
    main()
