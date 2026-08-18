# Relatorio do Projeto - Sistema de Apoio a Decisao

## Mercado de Automoveis Usados em Portugal

---

**Equipe:**
- Joao Vitor Fidelix da Silva
- Eric Reullyson Silva Leite
- Rafael dos Santos Sousa

**Data:** Agosto de 2026

**Disciplina:** Sistemas de Apoio a Decisao (SAD)

---

## 1. Introducao

O presente relatorio descreve o desenvolvimento de um **Sistema de Apoio a Decisao (SAD)** voltado para a analise do mercado de automoveis usados em Portugal. O sistema foi construido com base em um dataset contendo 37.529 anuncios de veiculos, abrangendo informacoes sobre preco, ano, quilometragem, tipo de combustivel, transmissao, cilindrada, potencia e localizacao geografica.

A motivacao do projeto partiu de uma problematica real: **compreender os fatores que influenciam o preco de um veiculo usado no mercado portugues**, permitindo que compradores, vendedores e analistas de mercado tomem decisoes mais informadas.

---

## 2. Objetivos

### 2.1 Objetivo Geral

Desenvolver um sistema interativo que permita a exploracao e analise dos dados do mercado automovel portugues, fornecendo metricas e visualizacoes que suportem a tomada de decisao.

### 2.2 Objetivos Especificos

- Criar um data warehouse estruturado em modelo estrela (star schema)
- Implementar um pipeline ETL para processamento dos dados brutos
- Desenvolver um dashboard interativo com graficos e filtros
- Responder a 5 perguntas de analise especificas sobre o mercado
- Fornecer metricas resumo: preco medio, mediano, minimo, maximo, quilometragem media, idade media e distribuicao por marca, combustivel e transmissao

---

## 3. Dataset Utilizado

### 3.1 Origem

O dataset **Portuguese Used Car Market** foi obtido de fonte publica (Kaggle), contendo anuncios de veiculos usados coletados em novembro de 2025.

### 3.2 Caracteristicas

| Propriedade | Valor |
|---|---|
| Total de registos | 37.529 |
| Total de colunas | 11 |
| Preco minimo | EUR 500 |
| Preco mediano | EUR 18.750 |
| Preco maximo | EUR 500.000 |
| Ano minimo | 1950 |
| Ano maximo | 2025 |
| Quilometragem mediana | 97.950 km |
| Localizacoes distintas | 978 |

### 3.3 Dicionario de Dados

| Coluna | Tipo | Unidade | Descricao |
|---|---|---|---|
| index | integer | - | Identificador do anuncio |
| title | string | - | Titulo do anuncio (contem marca e modelo) |
| price | number | EUR | Preco anunciado do veiculo |
| currency | string | - | Codigo da moeda (EUR) |
| year | integer | - | Ano de registo/matricula do veiculo |
| mileage | number | km | Quilometragem do veiculo |
| fuel | string | - | Tipo de combustivel (Gasoline, Diesel, Hybrid, etc.) |
| transmission | string | - | Tipo de transmissao (Manual ou Automatic) |
| displacement | number | cc | Cilindrada do motor |
| horsepower | number | hp | Potencia do motor em cavalos |
| location | string | - | Localizacao do anuncio em Portugal |

### 3.4 Validacao

O dataset passou em todas as verificacoes de qualidade:

- Arquivos primarios presentes: **PASS**
- Colunas obrigatorias: **PASS**
- Documentacao completa: **PASS**

---

## 4. Arquitetura do Sistema

### 4.1 Visao Geral

O sistema e composto por tres camadas principais:

```
[Dataset Bruto] --> [Pipeline ETL] --> [Data Warehouse (SQLite)] --> [Dashboard Streamlit]
```

### 4.2 Arquivos do Projeto

| Arquivo | Descricao |
|---|---|
| `etl.py` | Pipeline ETL - extracao, transformacao e carga dos dados |
| `app.py` | Dashboard interativo construido com Streamlit |
| `data_warehouse.db` | Banco de dados SQLite com o data warehouse |
| `requirements.txt` | Dependencias do projeto |
| `dataset/` | Pasta com os dados brutos originais |

---

## 5. Data Warehouse

### 5.1 Modelo Estrela (Star Schema)

O data warehouse foi projetado seguindo o modelo estrela, uma pratica recomendada para sistemas de apoio a decisao. Este modelo separa os dados em uma **tabela de fatos** (medidas e metricas) e **tabelas de dimensoes** (contexto analitico).

### 5.2 Tabela de Fatos

**fact_listings** (37.529 registos)

| Coluna | Tipo | Descricao |
|---|---|---|
| listing_id | integer | Chave primaria do anuncio |
| model_id | integer | Chave estrangeira para dim_model |
| fuel_id | integer | Chave estrangeira para dim_fuel |
| trans_id | integer | Chave estrangeira para dim_transmission |
| location_id | integer | Chave estrangeira para dim_location |
| year | integer | Ano do veiculo |
| price | float | Preco em EUR |
| mileage | float | Quilometragem em km |
| displacement | float | Cilindrada em cc |
| horsepower | float | Potencia em hp |
| vehicle_age | integer | Idade do veiculo (anos) |

### 5.3 Tabelas de Dimensoes

| Dimensao | Registos | Colunas |
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
|-----------|    | displacement, hp      |    |  - Preco       |
| loc_id    +--->| vehicle_age           |    |  - Km          |
| location  |    +-----------------------+    |  - Idade       |
+-----------+                                 |  - Cilindrada  |
                                              |  - Potencia    |
                                              +----------------+
```

### 5.5 Indices Criados

Para otimizar as consultas analiticas, foram criados indices nas seguintes colunas da tabela de fatos:

- `idx_fact_model` (model_id)
- `idx_fact_fuel` (fuel_id)
- `idx_fact_trans` (trans_id)
- `idx_fact_year` (year)

---

## 6. Pipeline ETL

### 6.1 Extracao

Os dados sao lidos a partir do arquivo CSV `market_analysis_cars_nov2025.csv`, contendo 37.529 registos com 11 colunas.

### 6.2 Transformacao

#### 6.2.1 Extracao de Marca e Modelo

O campo `title` do dataset contem o nome completo do veiculo (ex.: "Peugeot 208 1.2 PureTech Style"). Foi implementado um algoritmo que:

1. Compara o inicio do titulo com uma lista de 84 marcas conhecidas no mercado portugues
2. Extrai o modelo removendo a marca, cilindrada e epitetos comerciais (Style, Comfort, etc.)

**Marcas reconhecidas:** Toyota, Honda, Ford, BMW, Audi, Volkswagen, Peugeot, Renault, Opel, Fiat, Nissan, Hyundai, Kia, Citroen, Mazda, Suzuki, Volvo, Seat, Skoda, Dacia, Mini, Jeep, Porsche, Mercedes-Benz, Land Rover, Tesla, Cupra, entre outras.

#### 6.2.2 Classificacao de Combustivel

Os tipos de combustivel do dataset foram normalizados para 6 categorias padronizadas:

| Original | Normalizado |
|---|---|
| Gasoline | Gasolina |
| Diesel | Diesel |
| Hybrid (Gasoline) | Hibrido |
| Hybrid Plug-In | Hibrido Plug-In |
| Electric | Eletrico |
| LPG | GPL |

#### 6.2.3 Classificacao de Transmissao

| Original | Normalizado |
|---|---|
| Manual | Manual |
| Automatic, DSG, Tiptronic | Automatica |

#### 6.2.4 Calculo da Idade

A idade do veiculo foi calculada subtraindo o ano de fabricacao do ano corrente (2026), gerando a coluna derivada `vehicle_age`.

### 6.3 Carga

Os dados transformados sao gravados em banco de dados SQLite (`data_warehouse.db`) com as 6 tabelas do modelo estrela e indices de performance.

---

## 7. Dashboard Interativo

### 7.1 Ferramenta

O dashboard foi construido com **Streamlit** (framework Python para aplicacoes web) e **Plotly** (biblioteca de graficos interativos).

### 7.2 Filtros Disponiveis

O utilizador pode filtrar os dados por:

- **Marca** (selecao multipla)
- **Tipo de Combustivel** (Gasolina, Diesel, Hibrido, Hibrido Plug-In, Eletrico, GPL)
- **Transmissao** (Manual, Automatica)
- **Ano** (slider com range)
- **Preco** (slider com range em EUR)
- **Quilometragem** (slider com range em km)

### 7.3 Metricas Principais (KPIs)

O dashboard exibe 9 indicadores-chave de desempenho:

1. Total de anuncios
2. Preco medio
3. Preco mediano
4. Preco minimo
5. Preco maximo
6. Idade media dos veiculos
7. Quilometragem media
8. Quilometragem mediana
9. Numero de marcas distintas

### 7.4 Secoes de Analise

#### Secao 1: Marcas Mais Anunciadas

- Grafico de barras: Top 20 marcas por numero de anuncios
- Grafico de pizza: Participacao das Top 10 marcas
- Tabela detalhada com quantidades

**Resultados observados:** Mercedes-Benz (4.909 anuncios), Peugeot (4.128), BMW (3.980), Renault (3.107) e Citroen (1.948) lideram o numero de anuncios.

#### Secao 2: Preco Medio por Marca e Modelo

- Grafico de barras: Preco medio das 15 marcas com mais anuncios
- Seletor de marca com drill-down para precos medios por modelo
- Tabela com preco medio, mediano, minimo, maximo e contagem

#### Secao 3: Idade vs Preco

- Grafico de dispersao (scatter): Idade media vs preco medio, com tamanho proporcional a quantidade de anuncios
- Boxplot: Distribuicao de preco por ano de fabricacao
- Tabela com estatisticas por idade

#### Secao 4: Influencia das Caracteristicas

- Analise por combustivel: barras e boxplot comparando precos por tipo de combustivel
- Analise por transmissao: barras e boxplot comparando precos por tipo de transmissao
- Matriz de correlacao: heatmap entre preco, ano, quilometragem, idade, cilindrada e potencia
- Quilometragem vs Preco: scatter com linha de tendencia OLS por tipo de combustivel
- Potencia vs Preco: scatter com linha de tendencia OLS por tipo de combustivel

#### Secao 5: Melhor Relacao Preco/Ano

- Scatter: Preco medio vs ano medio dos modelos, com tamanho proporcional ao numero de anuncios e cor indicando ratio custo-beneficio
- Slider para filtrar minimo de anuncios por modelo
- Tabela top 20 melhores e piores relacoes preco/ano

### 7.5 Metricas Complementares

- Distribuicao por tipo de combustivel (grafico de pizza)
- Distribuicao por tipo de transmissao (grafico de pizza)
- Quilometragem media por marca (Top 15, grafico de barras)
- Top 10 modelos mais anunciados (grafico de barras empilhado)
- Visualizacao e exportacao dos dados filtrados em CSV

---

## 8. Perguntas de Analise e Respostas

### Pergunta 1: Quais sao as marcas de automoveis mais anunciadas em Portugal?

As marcas com maior numero de anuncios sao Mercedes-Benz, Peugeot, BMW, Renault e Citroen. Estas marcas representam uma parcela significativa do mercado de usados, refletindo sua forte presenca no parque automovel portugues.

### Pergunta 2: Qual e o preco medio dos carros por marca e modelo?

O preco medio varia significativamente entre marcas. Marcas premium como Mercedes-Benz e BMW apresentam precos medios superiores a EUR 29.000, enquanto marcas populares como Dacia e Fiat situam-se abaixo de EUR 13.000. O drill-down por modelo permite identificar especificamente quais versoes sao mais acessiveis ou premium dentro de cada marca.

### Pergunta 3: Veiculos mais novos possuem precos significativamente maiores?

Sim, existe uma relacao inversa clara entre idade e preco. Veiculos mais recentes (1-3 anos) apresentam precos medios significativamente superiores. A partir de 5-7 anos, a deprecacao comeca a se estabilizar, e veiculos acima de 15 anos tendem a ter precos muito inferiores, com maior variabilidade.

### Pergunta 4: Quais caracteristicas tem maior influencia no valor do automovel?

A analise de correlacao revela que:

- **Ano de fabricacao** tem forte correlacao positiva com o preco (quanto mais novo, mais caro)
- **Quilometragem** tem correlacao negativa com o preco (quanto mais rodado, mais barato)
- **Potencia (hp)** tem correlacao positiva moderada com o preco
- **Tipo de combustivel** influencia significativamente: veiculos eletricos e hibridos plug-in tendem a ser mais caros
- **Transmissao automatica** esta associada a precos medios superiores

### Pergunta 5: Quais modelos apresentam melhor relacao entre preco e ano de fabricacao?

Os modelos com melhor custo-beneficio sao aqueles que combinam anos de fabricacao recentes com precos acessiveis. A metrica de ratio (preco medio / ano medio) permite identificar modelos que oferecem o melhor equilibrio entre modernidade e preco. Modelos de marcas como Dacia, Fiat e Renault entre 2020-2023 tendem a apresentar os melhores ratios.

---

## 9. Tecnologias Utilizadas

| Tecnologia | Versao | Utilizacao |
|---|---|---|
| Python | 3.12 | Linguagem principal de programacao |
| Pandas | 3.0 | Manipulacao e analise de dados |
| NumPy | 2.2 | Computacao numerica |
| Streamlit | 1.61 | Framework de dashboard web |
| Plotly | 6.9 | Graficos interativos |
| SQLite | - | Banco de dados para o data warehouse |
| scikit-learn | 1.6 | Analise de regressao (tendencias OLS) |

---

## 10. Tutorial de Execucao

### 10.1 Pré-requisitos

- **Python 3.12 ou superior** deve estar instalado no sistema.
- Durante a instalacao do Python, marque a caixa **"Add Python to PATH"** para que o comando `python` funcione no terminal.
- Para verificar se o Python esta instalado, abra o terminal (Prompt de Comando) e digite:

```
python --version
```

Se aparecer a versao do Python instalado, esta tudo certo. Caso apareca erro, reinstale o Python marcando a opcao "Add to PATH".

### 10.2 Abrir o Terminal

1. Pressione `Win + R` no teclado.
2. Digite `cmd` e aperte Enter.
3. Navegue ate a pasta do projeto com o comando:

```
cd C:\Users\PC\Documents\SAD_PROJECT_FINAL
```

### 10.3 Instalar as Dependencias

Execute o comando abaixo para instalar todas as bibliotecas necessarias:

```
pip install -r requirements.txt
```

Esse comando instala automaticamente:

| Biblioteca | Funcao |
|---|---|
| pandas | Manipulacao de dados |
| streamlit | Framework do dashboard |
| plotly | Graficos interativos |
| scikit-learn | Analise de regressao |
| numpy | Computacao numerica |

> **Se aparecer erro de permissao**, tente:
> ```
> pip install -r requirements.txt --user
> ```

> **Se o download demorar muito**, e normal na primeira vez. Aguarde a conclusao.

### 10.4 Criar o Data Warehouse

Execute o pipeline ETL para processar o dataset bruto e criar o banco de dados:

```
python etl.py
```

Esse comando vai:
1. Ler o arquivo `dataset/market_analysis_cars_nov2025.csv` (37.529 registos)
2. Extrair marcas e modelos dos titulos dos anuncios
3. Classificar combustiveis e transmissoes
4. Criar as tabelas de dimensoes e fatos
5. Gravar tudo no arquivo `data_warehouse.db`

**Saida esperada no terminal:**

```
Lendo dataset bruto...
  Registos carregados: 37529
A extrair marcas e modelos...
A classificar combustivel e transmissao...
A criar dimensoes...
A criar tabela de factos...
A gravar data warehouse em data_warehouse.db...
Data warehouse criado com sucesso!
  Marcas: 84
  Modelos: 4207
  Tipos de combustivel: 6
  Tipos de transmissao: 3
  Localizacoes: 978
  Factos: 37529
```

> **Esse passo so e necessario uma vez.** Se o arquivo `data_warehouse.db` ja existir na pasta, o ETL pode ser re-executado para atualizar os dados.

### 10.5 Abrir o Dashboard

Apos criar o data warehouse, execute:

```
streamlit run app.py
```

O dashboard sera aberto automaticamente no navegador padrao em:

```
http://localhost:8501
```

Se nao abrir automaticamente, copie e cole o endereco acima na barra de endereco do navegador.

**Saida esperada no terminal:**

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

### 10.7 Possiveis Problemas e Solucoes

| Problema | Solucao |
|---|---|
| `'python' nao e reconhecido` | Reinstale o Python marcando "Add to PATH" |
| `'pip' nao e reconhecido` | Execute `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError` | Execute `pip install -r requirements.txt` novamente |
| `data_warehouse.db not found` | Execute `python etl.py` antes de abrir o dashboard |
| `Port 8501 already in use` | Feche a aba anterior do Streamlit ou use `streamlit run app.py --server.port 8502` |
| Dashboard nao abre no navegador | Acesse manualmente `http://localhost:8501` |

---

## 11. Consideracoes Finais

O sistema desenvolvido atende a todos os requisitos estabelecidos:

1. **Data Warehouse criado a partir de um dataset**: O data warehouse em modelo estrela foi construido a partir do dataset de 37.529 anuncios, com 5 tabelas de dimensoes e 1 tabela de fatos.

2. **Motivacao real**: A analise do mercado de automoveis usados em Portugal representa uma problematica real e relevante, com aplicações praticas para compradores, vendedores e analistas.

3. **Dados incorporados ao SAD**: O dataset ja esta incorporado ao sistema, com pipeline ETL completo que processa e normaliza os dados automaticamente.

4. **Graficos e inputs interativos**: O dashboard oferece 6 tipos de filtros interativos e mais de 15 graficos Plotly (barras, pizza, dispersao, boxplot, heatmap), permitindo exploracao completa dos dados para tomada de decisao.

5. **Clareza e consistencia dos dados**: Os dados foram normalizados (combustivel, transmissao, marcas), o data warehouse segue o modelo estrela para clareza analitica, e o dashboard apresenta metricas de forma clara e organizada.
