# Relatório do Projeto - Sistema de Apoio à Decisão

## Mercado de Automóveis Usados em Portugal

---

**Equipe:**

- João Vitor Fidelix da Silva
- Eric Reullyson Silva Leite
- Rafael dos Santos Sousa

**Data:** Agosto de 2026

**Disciplina:** Sistemas de Apoio à Decisão (SAD)

---

## 1. Introdução

O presente relatório descreve o desenvolvimento de um **Sistema de Apoio à Decisão (SAD)** voltado para a análise do mercado de automóveis usados em Portugal. O sistema foi construído com base em um dataset contendo 37.529 anúncios de veículos, abrangendo informações sobre preço, ano, quilometragem, tipo de combustível, transmissão, cilindrada, potência e localização geográfica.

A motivação do projeto partiu de uma problemática real: **compreender os fatores que influenciam o preço de um veículo usado no mercado português**, permitindo que compradores, vendedores e analistas de mercado tomem decisões mais informadas.

---

## 2. Objetivos

### 2.1 Objetivo Geral

Desenvolver um sistema interativo que permita a exploração e análise dos dados do mercado automóvel português, fornecendo métricas e visualizações que suportem a tomada de decisão.

### 2.2 Objetivos Específicos

- Criar um data warehouse estruturado em modelo estrela (star schema)
- Implementar um pipeline ETL para processamento dos dados brutos
- Desenvolver um dashboard interativo com gráficos e filtros
- Fornecer métricas resumo: preço médio, mediano, mínimo, máximo, quilometragem média, idade média e distribuição por marca, combustível e transmissão

---

## 3. Dataset Utilizado

### 3.1 Origem

O dataset **Portuguese Used Car Market** foi obtido de fonte pública (Kaggle), contendo anúncios de veículos usados coletados em novembro de 2025.

### 3.2 Características

| Propriedade | Valor |
| --- | --- |
| Total de registos | 37.529 |
| Total de colunas | 11 |
| Preço mínimo | EUR 500 |
| Preço mediano | EUR 18.750 |
| Preço máximo | EUR 500.000 |
| Ano mínimo | 1950 |
| Ano máximo | 2025 |
| Quilometragem mediana | 97.950 km |
| Localizações distintas | 978 |

### 3.3 Dicionário de Dados

| Coluna | Tipo | Unidade | Descrição |
| --- | --- | --- | --- |
| index | integer | - | Identificador do anúncio |
| title | string | - | Título do anúncio (contém marca e modelo) |
| price | number | EUR | Preço anunciado do veículo |
| currency | string | - | Código da moeda (EUR) |
| year | integer | - | Ano de registo/matrícula do veículo |
| mileage | number | km | Quilometragem do veículo |
| fuel | string | - | Tipo de combustível (Gasoline, Diesel, Hybrid, etc.) |
| transmission | string | - | Tipo de transmissão (Manual ou Automatic) |
| displacement | number | cc | Cilindrada do motor |
| horsepower | number | hp | Potência do motor em cavalos |
| location | string | - | Localização do anúncio em Portugal |

### 3.4 Validação

O dataset passou em todas as verificações de qualidade:

- Arquivos primários presentes: **PASS**
- Colunas obrigatórias: **PASS**
- Documentação completa: **PASS**

---

## 4. Arquitetura do Sistema

### 4.1 Visão Geral

O sistema é composto por três camadas principais:

```
[Dataset Bruto] --> [Pipeline ETL] --> [Data Warehouse (SQLite)] --> [Dashboard Streamlit]
```

### 4.2 Arquivos do Projeto

| Arquivo | Descrição |
| --- | --- |
| `etl.py` | Pipeline ETL - extração, transformação e carga dos dados |
| `app.py` | Dashboard interativo construído com Streamlit |
| `data_warehouse.db` | Banco de dados SQLite com o data warehouse |
| `requirements.txt` | Dependências do projeto |
| `dataset/` | Pasta com os dados brutos originais |

---

## 5. Data Warehouse

### 5.1 Modelo Estrela (Star Schema)

O data warehouse foi projetado seguindo o modelo estrela, uma prática recomendada para sistemas de apoio à decisão. Este modelo separa os dados em uma **tabela de fatos** (medidas e métricas) e **tabelas de dimensões** (contexto analítico).

### 5.2 Tabela de Fatos

**fact_listings** (37.529 registos)

| Coluna | Tipo | Descrição |
|---|---|---|
| listing_id | integer | Chave primária do anúncio |
| model_id | integer | Chave estrangeira para dim_model |
| fuel_id | integer | Chave estrangeira para dim_fuel |
| trans_id | integer | Chave estrangeira para dim_transmission |
| location_id | integer | Chave estrangeira para dim_location |
| year | integer | Ano do veículo |
| price | float | Preço em EUR |
| mileage | float | Quilometragem em km |
| displacement | float | Cilindrada em cc |
| horsepower | float | Potência em hp |
| vehicle_age | integer | Idade do veículo (anos) |

### 5.3 Tabelas de Dimensões

| Dimensão | Registos | Colunas |
|---|---|---|
| dim_brand | 84 | brand_id, brand |
| dim_model | 4.207 | model_id, brand_id, model |
| dim_fuel | 6 | fuel_id, fuel_type |
| dim_transmission | 3 | trans_id, trans_type |
| dim_location | 978 | location_id, location |

### 5.4 Diagrama do Data Warehouse

```
                    +-----------------+
                    |   dim_brand     |
                    |-----------------|
                    | brand_id (PK)   |
                    | brand           |
                    +--------+--------+
                             |
                    +--------+--------+
                    |   dim_model     |
                    |-----------------|
                    | model_id (PK)   |
                    | brand_id (FK)   |
                    | model           |
                    +--------+--------+
                             |
+-----------+    +-----------+-----------+    +-------------+
| dim_fuel  |    |    fact_listings      |    | dim_trans   |
|-----------|    |-----------------------|    |-------------|
| fuel_id   +--->| listing_id (PK)       |<---+ trans_id    |
| fuel_type |    | model_id (FK)         |    | trans_type  |
+-----------+    | fuel_id (FK)          |    +-------------+
                 | trans_id (FK)         |
+-----------+    | location_id (FK)      |    +----------------+
| dim_loc   |    | year, price, mileage  |    |  Medidas:      |
|-----------|    | displacement, hp      |    |  - Preço       |
| loc_id    +--->| vehicle_age           |    |  - Km          |
| location  |    +-----------------------+    |  - Idade       |
+-----------+                                 |  - Cilindrada  |
                                              |  - Potência    |
                                              +----------------+
```

### 5.5 Índices Criados

Para otimizar as consultas analíticas, foram criados índices nas seguintes colunas da tabela de fatos:

- `idx_fact_model` (model_id)
- `idx_fact_fuel` (fuel_id)
- `idx_fact_trans` (trans_id)
- `idx_fact_year` (year)

---

## 6. Pipeline ETL

### 6.1 Extração

Os dados são lidos a partir do arquivo CSV `market_analysis_cars_nov2025.csv`, contendo 37.529 registos com 11 colunas.

### 6.2 Transformação

#### 6.2.1 Extração de Marca e Modelo

O campo `title` do dataset contém o nome completo do veículo (ex.: "Peugeot 208 1.2 PureTech Style"). Foi implementado um algoritmo que:

1. Compara o início do título com uma lista de 84 marcas conhecidas no mercado português
2. Extrai o modelo removendo a marca, cilindrada e epítetos comerciais (Style, Comfort, etc.)

**Marcas reconhecidas:** Toyota, Honda, Ford, BMW, Audi, Volkswagen, Peugeot, Renault, Opel, Fiat, Nissan, Hyundai, Kia, Citroën, Mazda, Suzuki, Volvo, Seat, Skoda, Dacia, Mini, Jeep, Porsche, Mercedes-Benz, Land Rover, Tesla, Cupra, entre outras.

#### 6.2.2 Classificação de Combustível

Os tipos de combustível do dataset foram normalizados para 6 categorias padronizadas:

| Original | Normalizado |
| --- | --- |
| Gasoline | Gasolina |
| Diesel | Diesel |
| Hybrid (Gasoline) | Híbrido |
| Hybrid Plug-In | Híbrido Plug-In |
| Electric | Elétrico |
| LPG | GPL |

#### 6.2.3 Classificação de Transmissão

| Original | Normalizado |
| --- | --- |
| Manual | Manual |
| Automatic, DSG, Tiptronic | Automática |

#### 6.2.4 Cálculo da Idade

A idade do veículo foi calculada subtraindo o ano de fabricação do ano corrente (2026), gerando a coluna derivada `vehicle_age`.

### 6.3 Carga

Os dados transformados são gravados em banco de dados SQLite (`data_warehouse.db`) com as 6 tabelas do modelo estrela e índices de performance.

---

## 7. Dashboard Interativo

### 7.1 Ferramenta

O dashboard foi construído com **Streamlit** (framework Python para aplicações web) e **Plotly** (biblioteca de gráficos interativos).

### 7.2 Filtros Disponíveis

O utilizador pode filtrar os dados por:

- **Marca** (seleção múltipla)
- **Tipo de Combustível** (Gasolina, Diesel, Híbrido, Híbrido Plug-In, Elétrico, GPL)
- **Transmissão** (Manual, Automática)
- **Ano** (slider com range)
- **Preço** (slider com range em EUR)
- **Quilometragem** (slider com range em km)

### 7.3 Métricas Principais (KPIs)

O dashboard exibe 9 indicadores-chave de desempenho:

1. Total de anúncios
2. Preço médio
3. Preço mediano
4. Preço mínimo
5. Preço máximo
6. Idade média dos veículos
7. Quilometragem média
8. Quilometragem mediana
9. Número de marcas distintas

### 7.4 Seções de Análise

#### Seção 1: Marcas Mais Anunciadas

- Gráfico de barras: Top 20 marcas por número de anúncios
- Gráfico de pizza: Participação das Top 10 marcas
- Tabela detalhada com quantidades

**Resultados observados:** Mercedes-Benz (4.909 anúncios), Peugeot (4.128), BMW (3.980), Renault (3.107) e Citroën (1.948) lideram o número de anúncios.

#### Seção 2: Preço Médio por Marca e Modelo

- Gráfico de barras: Preço médio das 15 marcas com mais anúncios
- Seletor de marca com drill-down para preços médios por modelo
- Tabela com preço médio, mediano, mínimo, máximo e contagem

#### Seção 3: Idade vs Preço

- Gráfico de dispersão (scatter): Idade média vs preço médio, com tamanho proporcional à quantidade de anúncios
- Boxplot: Distribuição de preço por ano de fabricação
- Tabela com estatísticas por idade

#### Seção 4: Influência das Características

- Análise por combustível: barras e boxplot comparando preços por tipo de combustível
- Análise por transmissão: barras e boxplot comparando preços por tipo de transmissão
- Matriz de correlação: heatmap entre preço, ano, quilometragem, idade, cilindrada e potência
- Quilometragem vs Preço: scatter com linha de tendência OLS por tipo de combustível
- Potência vs Preço: scatter com linha de tendência OLS por tipo de combustível

#### Seção 5: Melhor Relação Preço/Ano

- Scatter: Preço médio vs ano médio dos modelos, com tamanho proporcional ao número de anúncios e cor indicando ratio custo-benefício
- Slider para filtrar mínimo de anúncios por modelo
- Tabela top 20 melhores e piores relações preço/ano

### 7.5 Métricas Complementares

- Distribuição por tipo de combustível (gráfico de pizza)
- Distribuição por tipo de transmissão (gráfico de pizza)
- Quilometragem média por marca (Top 15, gráfico de barras)
- Top 10 modelos mais anunciados (gráfico de barras empilhado)
- Visualização e exportação dos dados filtrados em CSV

---

## 8. Perguntas de Análise e Respostas

### Pergunta 1: Quais são as marcas de automóveis mais anunciadas em Portugal?

As marcas com maior número de anúncios são Mercedes-Benz, Peugeot, BMW, Renault e Citroën. Estas marcas representam uma parcela significativa do mercado de usados, refletindo sua forte presença no parque automóvel português.

### Pergunta 2: Qual é o preço médio dos carros por marca e modelo?

O preço médio varia significativamente entre marcas. Marcas premium como Mercedes-Benz e BMW apresentam preços médios superiores a EUR 29.000, enquanto marcas populares como Dacia e Fiat situam-se abaixo de EUR 13.000. O drill-down por modelo permite identificar especificamente quais versões são mais acessíveis ou premium dentro de cada marca.

### Pergunta 3: Veículos mais novos possuem preços significativamente maiores?

Sim, existe uma relação inversa clara entre idade e preço. Veículos mais recentes (1-3 anos) apresentam preços médios significativamente superiores. A partir de 5-7 anos, a depreciação começa a se estabilizar, e veículos acima de 15 anos tendem a ter preços muito inferiores, com maior variabilidade.

### Pergunta 4: Quais características têm maior influência no valor do automóvel?

A análise de correlação revela que:

- **Ano de fabricação** tem forte correlação positiva com o preço (quanto mais novo, mais caro)
- **Quilometragem** tem correlação negativa com o preço (quanto mais rodado, mais barato)
- **Potência (hp)** tem correlação positiva moderada com o preço
- **Tipo de combustível** influencia significativamente: veículos elétricos e híbridos plug-in tendem a ser mais caros
- **Transmissão automática** está associada a preços médios superiores

### Pergunta 5: Quais modelos apresentam melhor relação entre preço e ano de fabricação?

Os modelos com melhor custo-benefício são aqueles que combinam anos de fabricação recentes com preços acessíveis. A métrica de ratio (preço médio / ano médio) permite identificar modelos que oferecem o melhor equilíbrio entre modernidade e preço. Modelos de marcas como Dacia, Fiat e Renault entre 2020-2023 tendem a apresentar os melhores ratios.

---

## 9. Tecnologias Utilizadas

| Tecnologia | Versão | Utilização |
|---|---|---|
| Python | 3.12 | Linguagem principal de programação |
| Pandas | 3.0 | Manipulação e análise de dados |
| NumPy | 2.2 | Computação numérica |
| Streamlit | 1.61 | Framework de dashboard web |
| Plotly | 6.9 | Gráficos interativos |
| SQLite | - | Banco de dados para o data warehouse |
| scikit-learn | 1.6 | Análise de regressão (tendências OLS) |

---

## 10. Tutorial de Execução

### 10.1 Pré-requisitos

- **Python 3.12 ou superior** deve estar instalado no sistema.
- Durante a instalação do Python, marque a caixa **"Add Python to PATH"** para que o comando `python` funcione no terminal.
- Para verificar se o Python está instalado, abra o terminal (Prompt de Comando) e digite:

```
python --version
```

Se aparecer a versão do Python instalado, está tudo certo. Caso apareça erro, reinstale o Python marcando a opção "Add to PATH".

### 10.2 Abrir o Terminal

1. Pressione `Win + R` no teclado.
2. Digite `cmd` e aperte Enter.
3. Navegue até a pasta do projeto com o comando:

```
cd C:\Users\PC\Documents\SAD_PROJECT_FINAL
```

### 10.3 Instalar as Dependências

Execute o comando abaixo para instalar todas as bibliotecas necessárias:

```
pip install -r requirements.txt
```

Esse comando instala automaticamente:

| Biblioteca | Função |
|---|---|
| pandas | Manipulação de dados |
| streamlit | Framework do dashboard |
| plotly | Gráficos interativos |
| scikit-learn | Análise de regressão |
| numpy | Computação numérica |

> **Se aparecer erro de permissão**, tente:
> ```
> pip install -r requirements.txt --user
> ```

> **Se o download demorar muito**, é normal na primeira vez. Aguarde a conclusão.

### 10.4 Criar o Data Warehouse

Execute o pipeline ETL para processar o dataset bruto e criar o banco de dados:

```
python etl.py
```

Esse comando vai:
1. Ler o arquivo `dataset/market_analysis_cars_nov2025.csv` (37.529 registos)
2. Extrair marcas e modelos dos títulos dos anúncios
3. Classificar combustíveis e transmissões
4. Criar as tabelas de dimensões e fatos
5. Gravar tudo no arquivo `data_warehouse.db`

**Saída esperada no terminal:**

```
Lendo dataset bruto...
  Registos carregados: 37529
A extrair marcas e modelos...
A classificar combustível e transmissão...
A criar dimensões...
A criar tabela de factos...
A gravar data warehouse em data_warehouse.db...
Data warehouse criado com sucesso!
  Marcas: 84
  Modelos: 4207
  Tipos de combustível: 6
  Tipos de transmissão: 3
  Localizações: 978
  Factos: 37529
```

> **Esse passo só é necessário uma vez.** Se o arquivo `data_warehouse.db` já existir na pasta, o ETL pode ser re-executado para atualizar os dados.

### 10.5 Abrir o Dashboard

Após criar o data warehouse, execute:

```
streamlit run app.py
```

O dashboard será aberto automaticamente no navegador padrão em:

```
http://localhost:8501
```

Se não abrir automaticamente, copie e cole o endereço acima na barra de endereço do navegador.

**Saída esperada no terminal:**

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 10.6 Resumo dos Comandos

Para rodar o projeto do zero, basta seguir esses 3 passos no terminal:

```
cd C:\Users\PC\Documents\SAD_PROJECT_FINAL
pip install -r requirements.txt
streamlit run app.py
```

Se precisar recriar o data warehouse antes:

```
cd C:\Users\PC\Documents\SAD_PROJECT_FINAL
python etl.py
streamlit run app.py
```

### 10.7 Possíveis Problemas e Soluções

| Problema | Solução |
|---|---|
| `'python' não é reconhecido` | Reinstale o Python marcando "Add to PATH" |
| `'pip' não é reconhecido` | Execute `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError` | Execute `pip install -r requirements.txt` novamente |
| `data_warehouse.db not found` | Execute `python etl.py` antes de abrir o dashboard |
| `Port 8501 already in use` | Feche a aba anterior do Streamlit ou use `streamlit run app.py --server.port 8502` |
| Dashboard não abre no navegador | Acesse manualmente `http://localhost:8501` |

---

## 11. Considerações Finais

O sistema desenvolvido atende a todos os requisitos estabelecidos:

1. **Data Warehouse criado a partir de um dataset**: O data warehouse em modelo estrela foi construído a partir do dataset de 37.529 anúncios, com 5 tabelas de dimensões e 1 tabela de fatos.

2. **Motivação real**: A análise do mercado de automóveis usados em Portugal representa uma problemática real e relevante, com aplicações práticas para compradores, vendedores e analistas.

3. **Dados incorporados ao SAD**: O dataset já está incorporado ao sistema, com pipeline ETL completo que processa e normaliza os dados automaticamente.

4. **Gráficos e inputs interativos**: O dashboard oferece 6 tipos de filtros interativos e mais de 15 gráficos Plotly (barras, pizza, dispersão, boxplot, heatmap), permitindo exploração completa dos dados para tomada de decisão.

5. **Clareza e consistência dos dados**: Os dados foram normalizados (combustível, transmissão, marcas), o data warehouse segue o modelo estrela para clareza analítica, e o dashboard apresenta métricas de forma clara e organizada.