"""
App Streamlit - Sistema de Apoio a Decisao (SAD)
=================================================
Dashboard interativo para análise do mercado de automóveis em Portugal.
Conecta-se ao data warehouse SQLite e apresenta KPIs, graficos e tabelas
respondendo a perguntas de negócio sobre marcas, preços, idade,
características influentes e relação preço/ano.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

# ===================== CONFIGURACAO DA PAGINA =====================
# Define titulo da aba do navegador e layout wide (tela cheia)
st.set_page_config(page_title="SAD - Mercado de Automóveis PT", layout="wide")

# Caminho do banco de dados SQLite (relativo ao script)
DB_PATH = os.path.join(os.path.dirname(__file__), "data_warehouse.db")


# ===================== CARREGAMENTO DOS DADOS =====================
@st.cache_data
def load_data():
    """
    Carrega os dados do data warehouse SQLite, fazendo JOINs entre a
    tabela de factos e todas as dimensoes para obter nomes legiveis.

    Usa @st.cache_data para caches os dados e evitar recarregar a cada
    interacao do usuario no Streamlit.

    Retorna um DataFrame com todas as colunas necessarias para as analises.
    """
    conn = sqlite3.connect(DB_PATH)
    # Query que junta fact_listings com todas as dimensoes
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
    # ===================== TITULO E CABECALHO =====================
    st.title("Sistema de Apoio à Decisão - Mercado de Automóveis em Portugal")
    st.caption("Equipe: João Vitor Fidelix da Silva | Eric Reullyson Silva Leite | Rafael dos Santos Sousa")
    st.markdown("---")

    # Carrega os dados do data warehouse
    df = load_data()

    # ===================== SIDEBAR - FILTROS =====================
    # Filtros interativos na barra lateral para o usuario refinar a analise
    st.sidebar.header("Filtros")

    # Filtro por marca (multiselect - varias opcoes)
    brands = sorted(df["brand"].unique())
    sel_brands = st.sidebar.multiselect("Marca", brands, default=[])

    # Filtro por tipo de combustivel (todas selecionadas por padrao)
    fuels = sorted(df["fuel_type"].unique())
    sel_fuels = st.sidebar.multiselect("Combustível", fuels, default=fuels)

    # Filtro por tipo de transmissao (todas selecionadas por padrao)
    trans_options = sorted(df["trans_type"].unique())
    sel_trans = st.sidebar.multiselect("Transmissão", trans_options, default=trans_options)

    # Filtro por ano (slider de intervalo)
    year_min = int(df["year"].min())
    year_max = int(df["year"].max())
    sel_year = st.sidebar.slider("Ano", year_min, year_max, (year_min, year_max))

    # Filtro por preco (slider de intervalo em EUR)
    price_max = int(df["price"].max())
    sel_price = st.sidebar.slider("Preço (EUR)", 0, price_max, (0, price_max))

    # Filtro por quilometragem (slider de intervalo em km)
    mileage_max = int(df["mileage"].max())
    sel_mileage = st.sidebar.slider("Quilometragem (km)", 0, int(mileage_max), (0, int(mileage_max)))

    # ===================== APLICACAO DOS FILTROS =====================
    # Aplica todos os filtros selecionados ao DataFrame
    filtered = df.copy()
    if sel_brands:
        filtered = filtered[filtered["brand"].isin(sel_brands)]
    filtered = filtered[filtered["fuel_type"].isin(sel_fuels)]
    filtered = filtered[filtered["trans_type"].isin(sel_trans)]
    filtered = filtered[(filtered["year"] >= sel_year[0]) & (filtered["year"] <= sel_year[1])]
    filtered = filtered[(filtered["price"] >= sel_price[0]) & (filtered["price"] <= sel_price[1])]
    filtered = filtered[(filtered["mileage"] >= sel_mileage[0]) & (filtered["mileage"] <= sel_mileage[1])]

    # Se nenhum registro corresponder aos filtros, exibe aviso e encerra
    if filtered.empty:
        st.warning("Nenhum registro corresponde aos filtros selecionados.")
        return

    # ==================== KPIs - METRICAS GERAIS ====================
    # Primeira linha de metricas: total de anuncios, precos e idade media
    st.subheader("Métricas Gerais")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total de Anúncios", f"{len(filtered):,}")
    c2.metric("Preço Médio", f"EUR {filtered['price'].mean():,.0f}")
    c3.metric("Preço Mediano", f"EUR {filtered['price'].median():,.0f}")
    c4.metric("Preço Mínimo", f"EUR {filtered['price'].min():,.0f}")
    c5.metric("Preço Máximo", f"EUR {filtered['price'].max():,.0f}")
    c6.metric("Idade Média", f"{filtered['vehicle_age'].mean():.1f} anos")

    # Segunda linha de metricas: quilometragem media e marcas distintas
    c7, c8, c9 = st.columns(3)
    c7.metric("Quilometragem Média", f"{filtered['mileage'].mean():,.0f} km")
    c8.metric("Quilometragem Mediana", f"{filtered['mileage'].median():,.0f} km")
    c9.metric("Marcas Distintas", f"{filtered['brand'].nunique()}")

    # ==================== SAD - ESTIMATIVA DE PRECO JUSTO ====================
    st.markdown("---")
    st.header("SAD: Estimar o preço justo de um carro")
    st.write("Informe as características do veículo para comparar com anúncios semelhantes.")

    sad_brands = sorted(filtered["brand"].dropna().unique())
    sad_brand = st.selectbox("Marca", sad_brands, key="sad_brand")
    sad_models = sorted(filtered.loc[filtered["brand"] == sad_brand, "model"].dropna().unique())

    with st.form("price_estimator_form"):
        sad_col1, sad_col2, sad_col3 = st.columns(3)
        with sad_col1:
            sad_year = st.number_input(
                "Ano", min_value=year_min, max_value=year_max,
                value=year_max, step=1, key="sad_year"
            )
            sad_mileage = st.number_input(
                "Quilometragem (km)", min_value=0, max_value=mileage_max,
                value=int(filtered["mileage"].median()), step=1000, key="sad_mileage"
            )
        with sad_col2:
            sad_model = st.selectbox("Modelo", sad_models, key=f"sad_model_{sad_brand}")
            sad_fuel = st.selectbox("Combustível", fuels, key="sad_fuel")
            sad_trans = st.selectbox("Transmissão", trans_options, key="sad_trans")
        with sad_col3:
            displacement_median = filtered["displacement"].median()
            horsepower_median = filtered["horsepower"].median()
            sad_displacement = st.number_input(
                "Cilindrada (cm³)", min_value=0.0, value=float(displacement_median),
                step=100.0, key="sad_displacement"
            )
            sad_horsepower = st.number_input(
                "Potência (CV)", min_value=0.0, value=float(horsepower_median),
                step=1.0, key="sad_horsepower"
            )
            estimate_submitted = st.form_submit_button("Estimar preço", type="primary")

    if estimate_submitted:
        numeric_features = ["year", "mileage", "displacement", "horsepower"]
        target_values = pd.Series({
            "year": sad_year,
            "mileage": sad_mileage,
            "displacement": sad_displacement,
            "horsepower": sad_horsepower,
        })
        comparison_pool = filtered[filtered["brand"] == sad_brand].copy()
        same_model_pool = comparison_pool[comparison_pool["model"] == sad_model]
        if len(same_model_pool) >= 5:
            comparison_pool = same_model_pool

        comparison_pool = comparison_pool.copy()
        for feature in numeric_features:
            comparison_pool[feature] = comparison_pool[feature].fillna(filtered[feature].median())
            scale = comparison_pool[feature].quantile(0.75) - comparison_pool[feature].quantile(0.25)
            if not scale or pd.isna(scale):
                scale = comparison_pool[feature].std()
            if not scale or pd.isna(scale):
                scale = 1.0
            comparison_pool[f"distance_{feature}"] = (
                (comparison_pool[feature] - target_values[feature]).abs() / scale
            )

        comparison_pool["distance_categorical"] = (
            (comparison_pool["model"] != sad_model).astype(float) * 0.8
            + (comparison_pool["fuel_type"] != sad_fuel).astype(float) * 0.4
            + (comparison_pool["trans_type"] != sad_trans).astype(float) * 0.3
        )
        comparison_pool["similarity_distance"] = (
            comparison_pool["distance_year"] * 0.35
            + comparison_pool["distance_mileage"] * 0.30
            + comparison_pool["distance_displacement"] * 0.10
            + comparison_pool["distance_horsepower"] * 0.10
            + comparison_pool["distance_categorical"]
        )
        comparables = comparison_pool.nsmallest(min(20, len(comparison_pool)), "similarity_distance")
        fair_price = comparables["price"].median()
        low_price = comparables["price"].quantile(0.25)
        high_price = comparables["price"].quantile(0.75)

        result_col1, result_col2, result_col3 = st.columns(3)
        result_col1.metric("Estimativa de preço justo", f"EUR {fair_price:,.0f}")
        result_col2.metric("Faixa recomendada", f"EUR {low_price:,.0f} - EUR {high_price:,.0f}")
        result_col3.metric("Anúncios comparáveis", f"{len(comparables)}")
        st.caption("Estimativa baseada na mediana dos anúncios mais semelhantes dentro dos filtros selecionados.")

        comparable_table = comparables[["brand", "model", "year", "mileage", "fuel_type", "trans_type", "price"]].copy()
        comparable_table.columns = ["Marca", "Modelo", "Ano", "Km", "Combustível", "Transmissão", "Preço"]
        st.dataframe(
            comparable_table.style.format({"Km": "{:,.0f} km", "Preço": "EUR {:,.0f}"}),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # ==================== PERGUNTA 1 ====================
    # Quais sao as marcas de automoveis mais anunciadas em Portugal?
    # Apresenta grafico de barras (top 20) e pizza (top 10)
    st.header("1. Quais são as marcas de automóveis mais anunciadas em Portugal?")

    brand_counts = filtered["brand"].value_counts().head(20).reset_index()
    brand_counts.columns = ["Marca", "Quantidade"]

    col_a, col_b = st.columns(2)
    with col_a:
        # Grafico de barras: top 20 marcas por numero de anuncios
        fig_bar = px.bar(
            brand_counts, x="Marca", y="Quantidade",
            color="Quantidade", color_continuous_scale="Blues",
            title="Top 20 Marcas por Número de Anúncios"
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        # Grafico de pizza: participacao das top 10 marcas
        fig_pie = px.pie(
            brand_counts.head(10), names="Marca", values="Quantidade",
            title="Participação das Top 10 Marcas"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabela com os dados por baixo do grafico
    st.dataframe(brand_counts, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==================== PERGUNTA 2 ====================
    # Qual e o preco medio dos carros por marca e modelo?
    # Mostra preco medio por marca (top 15) e permite selecionar marca
    # para ver preco medio por modelo
    st.header("2. Qual é o preço médio dos carros por marca e modelo?")

    # Calcula estatisticas de preco para as 15 marcas com mais anuncios
    top_brands = filtered["brand"].value_counts().head(15).index.tolist()
    brand_price = (
        filtered[filtered["brand"].isin(top_brands)]
        .groupby("brand")["price"]
        .agg(["mean", "median", "min", "max", "count"])
        .reset_index()
    )
    brand_price.columns = ["Marca", "Preço Médio", "Preço Mediano", "Mínimo", "Máximo", "N"]
    brand_price = brand_price.sort_values("Preço Médio", ascending=False)

    # Grafico de barras com erro (mostra ate o preco maximo)
    fig_bp = px.bar(
        brand_price, x="Marca", y="Preço Médio",
        error_y=brand_price["Máximo"] - brand_price["Preço Médio"],
        color="Preço Médio", color_continuous_scale="RdYlGn_r",
        title="Preço Médio por Marca (Top 15 com mais anúncios)"
    )
    fig_bp.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bp, use_container_width=True)

    # Tabela formatada com precos em EUR
    st.dataframe(brand_price.style.format({
        "Preço Médio": "EUR {:,.0f}",
        "Preço Mediano": "EUR {:,.0f}",
        "Mínimo": "EUR {:,.0f}",
        "Máximo": "EUR {:,.0f}"
    }), use_container_width=True, hide_index=True)

    # Preco medio por modelo dentro de uma marca selecionada
    st.subheader("Preço Médio por Modelo")
    selected_brand = st.selectbox("Selecione uma marca para ver os modelos:", top_brands)
    model_price = (
        filtered[filtered["brand"] == selected_brand]
        .groupby("model")["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    model_price.columns = ["Modelo", "Preço Médio", "Preço Mediano", "N"]
    model_price = model_price.sort_values("N", ascending=False)

    # Grafico de barras com o preco medio dos modelos da marca selecionada
    fig_mp = px.bar(
        model_price.head(15), x="Modelo", y="Preço Médio",
        color="N", color_continuous_scale="Teal",
        title=f"Preço Médio por Modelo - {selected_brand}"
    )
    st.plotly_chart(fig_mp, use_container_width=True)

    st.markdown("---")

    # ==================== PERGUNTA 3 ====================
    # Veiculos mais novos possuem precos significativamente maiores?
    # Analise da relacao entre idade do veiculo e preco
    st.header("3. Veículos mais novos possuem preços significativamente maiores?")

    # Agrupa por idade e calcula preco medio/mediano
    age_price = (
        filtered.groupby("vehicle_age")["price"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    age_price.columns = ["Idade (anos)", "Preço Médio", "Preço Mediano", "N"]

    col_a, col_b = st.columns(2)
    with col_a:
        # Scatter plot: preco medio vs idade (tamanho = quantidade de anuncios)
        fig_age = px.scatter(
            age_price, x="Idade (anos)", y="Preço Médio",
            size="N", color="Preço Médio",
            color_continuous_scale="RdYlGn_r",
            title="Relação entre Idade do Veículo e Preço Médio",
            size_max=40
        )
        st.plotly_chart(fig_age, use_container_width=True)

    with col_b:
        # Box plot: distribuicao de preco para cada idade
        fig_box = px.box(
            filtered, x="vehicle_age", y="price",
            title="Distribuição de Preço por Idade",
            labels={"vehicle_age": "Idade (anos)", "price": "Preço (EUR)"}
        )
        fig_box.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_box, use_container_width=True)

    # Tabela detalhada com estatisticas por idade
    st.dataframe(age_price.sort_values("Idade (anos)"), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==================== PERGUNTA 4 ====================
    # Quais caracteristicas tem maior influencia no valor do automovel?
    # Analises por combustivel, transmissao, correlacao e dispersao
    st.header("4. Quais características têm maior influência no valor do automóvel?")

    # --- Subsecao: Analise por Combustivel ---
    st.subheader("Análise por Combustível")
    col_a, col_b = st.columns(2)
    with col_a:
        # Estatisticas de preco agrupadas por tipo de combustivel
        fuel_stats = (
            filtered.groupby("fuel_type")["price"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        fuel_stats.columns = ["Combustível", "Preço Médio", "Preço Mediano", "N"]
        fuel_stats = fuel_stats.sort_values("Preço Médio", ascending=False)

        # Grafico de barras: preco medio por combustivel
        fig_fuel = px.bar(
            fuel_stats, x="Combustível", y="Preço Médio",
            color="Combustível", title="Preço Médio por Tipo de Combustível"
        )
        st.plotly_chart(fig_fuel, use_container_width=True)

    with col_b:
        # Box plot: distribuicao de preco por combustivel
        fig_fuel_box = px.box(
            filtered, x="fuel_type", y="price",
            color="fuel_type",
            title="Distribuição de Preço por Combustível",
            labels={"price": "Preço (EUR)"}
        )
        st.plotly_chart(fig_fuel_box, use_container_width=True)

    # --- Subsecao: Analise por Transmissao ---
    st.subheader("Análise por Transmissão")
    col_a, col_b = st.columns(2)
    with col_a:
        # Estatisticas de preco agrupadas por tipo de transmissao
        trans_stats = (
            filtered.groupby("trans_type")["price"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        trans_stats.columns = ["Transmissão", "Preço Médio", "Preço Mediano", "N"]

        # Grafico de barras: preco medio por transmissao
        fig_trans = px.bar(
            trans_stats, x="Transmissão", y="Preço Médio",
            color="Transmissão", title="Preço Médio por Transmissão"
        )
        st.plotly_chart(fig_trans, use_container_width=True)

    with col_b:
        # Box plot: distribuicao de preco por transmissao
        fig_trans_box = px.box(
            filtered, x="trans_type", y="price",
            color="trans_type",
            title="Distribuição de Preço por Transmissão",
            labels={"price": "Preço (EUR)"}
        )
        st.plotly_chart(fig_trans_box, use_container_width=True)

    # --- Subsecao: Matriz de Correlacao ---
    st.subheader("Análise de Correlação (Características Numéricas)")
    # Seleciona apenas colunas numericas e calcula correlacao de Pearson
    numeric_cols = ["price", "year", "mileage", "vehicle_age", "displacement", "horsepower"]
    corr_df = filtered[numeric_cols].dropna()
    corr = corr_df.corr()

    # Heatmap da matriz de correlacao
    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r",
        title="Matriz de Correlação entre Variáveis",
        labels=dict(color="Correlação")
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # --- Subsecao: Quilometragem vs Preco ---
    st.subheader("Importância: Quilometragem vs Preço por Combustível")
    # Scatter plot com linha de tendencia OLS (regressao linear)
    # Requer o pacote statsmodels para a linha de tendencia
    sample_size = min(3000, len(filtered))
    fig_mil = px.scatter(
        filtered.sample(sample_size, random_state=42),
        x="mileage", y="price", color="fuel_type",
        opacity=0.5, title="Quilometragem vs Preço",
        labels={"mileage": "Quilometragem (km)", "price": "Preço (EUR)"},
        trendline="ols"
    )
    st.plotly_chart(fig_mil, use_container_width=True)

    # --- Subsecao: Potencia vs Preco ---
    st.subheader("Importância: Potência (CV) vs Preço")
    # Scatter plot filtrando apenas registros com valor de potencia valido
    hp_df = filtered[filtered["horsepower"].notna()]
    sample_size_hp = min(3000, len(hp_df))
    fig_hp = px.scatter(
        hp_df.sample(sample_size_hp, random_state=42),
        x="horsepower", y="price", color="fuel_type",
        opacity=0.5, title="Potência vs Preço",
        labels={"horsepower": "Potência (CV)", "price": "Preço (EUR)"},
        trendline="ols"
    )
    st.plotly_chart(fig_hp, use_container_width=True)

    st.markdown("---")

    # ==================== PERGUNTA 5 ====================
    # Quais modelos apresentam melhor relacao entre preco e ano?
    # Calcula um "valor_ano_ratio" (preco medio / ano medio) para ranquear
    # modelos do melhor (mais novo e barato) ao pior (mais caro e antigo)
    st.header("5. Quais modelos apresentam melhor relação entre preço e ano de fabricação?")

    # Agrupa por marca e modelo, calculando metricas agregadas
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

    # Slider para filtrar modelos com no minimo N anuncios (evita outliers)
    min_anuncios = st.slider(
        "Mínimo de anúncios por modelo para análise:", 1, 50, 5
    )
    model_filtered = model_analysis[model_analysis["n_anuncios"] >= min_anuncios].copy()

    # Calcula o ratio preco/ano: valores menores indicam melhor custo-beneficio
    model_filtered["valor_ano_ratio"] = model_filtered["preco_medio"] / model_filtered["ano_medio"]

    # Scatter plot: preco medio vs ano medio, com tamanho = nr anuncios, cor = ratio
    st.subheader("Modelos com Melhor Relação Preço/Ano (Mais Novos e Mais Baratos)")
    best_value = model_filtered.nsmallest(20, "valor_ano_ratio")
    fig_bv = px.scatter(
        model_filtered, x="ano_medio", y="preco_medio",
        size="n_anuncios", color="valor_ano_ratio",
        color_continuous_scale="RdYlGn",
        hover_name="model", hover_data=["brand", "km_media"],
        title="Relação Preço vs Ano (tamanho = nº de anúncios, cor = razão)",
        labels={
            "ano_medio": "Ano Médio", "preco_medio": "Preço Médio (EUR)",
            "brand": "Marca", "model": "Modelo", "km_media": "Quilometragem Média",
            "n_anuncios": "Nº de Anúncios", "valor_ano_ratio": "Razão Preço/Ano"
        }
    )
    st.plotly_chart(fig_bv, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        # Tabela top 20 melhores custo-beneficio (menor ratio)
        st.subheader("Top 20 - Melhor Custo-Benefício")
        best_value_display = best_value[[
            "brand", "model", "preco_medio", "ano_medio", "km_media", "n_anuncios", "valor_ano_ratio"
        ]].rename(columns={
            "brand": "Marca", "model": "Modelo", "preco_medio": "Preço Médio",
            "ano_medio": "Ano Médio", "km_media": "Quilometragem Média",
            "n_anuncios": "Nº de Anúncios", "valor_ano_ratio": "Razão Preço/Ano"
        })
        st.dataframe(
            best_value_display.style.format({
                "Preço Médio": "EUR {:,.0f}",
                "Ano Médio": "{:.0f}",
                "Quilometragem Média": "{:,.0f} km",
                "Razão Preço/Ano": "{:.1f}"
            }),
            use_container_width=True, hide_index=True
        )

    with col_b:
        # Tabela top 20 piores custo-beneficio (maior ratio = mais caro e antigo)
        st.subheader("Top 20 - Mais Caros versus Antigos")
        worst_value = model_filtered.nlargest(20, "valor_ano_ratio")
        worst_value_display = worst_value[[
            "brand", "model", "preco_medio", "ano_medio", "km_media", "n_anuncios", "valor_ano_ratio"
        ]].rename(columns={
            "brand": "Marca", "model": "Modelo", "preco_medio": "Preço Médio",
            "ano_medio": "Ano Médio", "km_media": "Quilometragem Média",
            "n_anuncios": "Nº de Anúncios", "valor_ano_ratio": "Razão Preço/Ano"
        })
        st.dataframe(
            worst_value_display.style.format({
                "Preço Médio": "EUR {:,.0f}",
                "Ano Médio": "{:.0f}",
                "Quilometragem Média": "{:,.0f} km",
                "Razão Preço/Ano": "{:.1f}"
            }),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # ==================== METRICAS COMPLEMENTARES ====================
    # Graficos adicionais para enriquecer a analise
    st.header("Métricas Complementares")

    # Grafico de pizza: distribuicao de anuncios por combustivel
    st.subheader("Distribuição por Tipo de Combustível")
    fuel_dist = filtered["fuel_type"].value_counts().reset_index()
    fuel_dist.columns = ["Combustível", "Quantidade"]
    fig_fd = px.pie(fuel_dist, names="Combustível", values="Quantidade",
                    title="Distribuição de Anúncios por Combustível")
    st.plotly_chart(fig_fd, use_container_width=True)

    # Grafico de pizza: distribuicao de anuncios por transmissao
    st.subheader("Distribuição por Transmissão")
    trans_dist = filtered["trans_type"].value_counts().reset_index()
    trans_dist.columns = ["Transmissão", "Quantidade"]
    fig_td = px.pie(trans_dist, names="Transmissão", values="Quantidade",
                    title="Distribuição de Anúncios por Transmissão")
    st.plotly_chart(fig_td, use_container_width=True)

    # Grafico de barras: quilometragem media por marca (top 15)
    st.subheader("Quilometragem Média por Marca")
    top_brands_km = filtered["brand"].value_counts().head(15).index.tolist()
    brand_km = (
        filtered[filtered["brand"].isin(top_brands_km)]
        .groupby("brand")["mileage"]
        .mean()
        .reset_index()
    )
    brand_km.columns = ["Marca", "Quilometragem Média"]
    brand_km = brand_km.sort_values("Quilometragem Média", ascending=False)

    fig_km = px.bar(brand_km, x="Marca", y="Quilometragem Média",
                    color="Quilometragem Média", color_continuous_scale="Oranges",
                    title="Quilometragem Média por Marca (Top 15)")
    fig_km.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_km, use_container_width=True)

    # Grafico de barras: top 10 modelos mais anunciados
    st.subheader("Top 10 Modelos Mais Anunciados")
    top_models = filtered.value_counts(["brand", "model"]).head(10).reset_index()
    top_models.columns = ["Marca", "Modelo", "Quantidade"]
    fig_tm = px.bar(top_models, x="Modelo", y="Quantidade", color="Marca",
                    title="Top 10 Modelos Mais Anunciados")
    st.plotly_chart(fig_tm, use_container_width=True)

    # ==================== DADOS BRUTOS ====================
    # Secao expansivel com tabela de dados filtrados e opcao de download CSV
    st.markdown("---")
    with st.expander("Ver dados filtrados"):
        filtered_display = filtered.rename(columns={
            "listing_id": "ID do Anúncio", "year": "Ano", "price": "Preço",
            "mileage": "Quilometragem", "displacement": "Cilindrada",
            "horsepower": "Potência", "vehicle_age": "Idade do Veículo",
            "brand": "Marca", "model": "Modelo", "fuel_type": "Combustível",
            "trans_type": "Transmissão", "location": "Localização"
        })
        st.dataframe(filtered_display, use_container_width=True, hide_index=True)
        # Gera CSV em memoria para download
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV", csv, "dados_filtrados.csv", "text/csv")


if __name__ == "__main__":
    main()
