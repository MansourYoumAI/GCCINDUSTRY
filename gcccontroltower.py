import streamlit as st
import pandas as pd
import plotly.express as px
# Supprime ou commente cette ligne, si tu ne veux pas utiliser AgGrid
# from st_aggrid import AgGrid
import json

# -------------------------------
# Load and cache data
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_json("data/entreprises.json")
    return df

df = load_data()

# -------------------------------
# Sidebar Navigation
# -------------------------------
st.sidebar.title("📊 GCC Industrial Explorer")

# Filters
pays_HQ_filter = st.sidebar.multiselect("📍 HQ Country", sorted(df["pays_HQ"].unique()))
industrie_filter = st.sidebar.multiselect("🏭 Industry", sorted(df["industrie"].unique()))
marche_filter = st.sidebar.multiselect("🔍 Market", sorted(df["marche"].unique()))
collab_filter = st.sidebar.multiselect("👥 Workforce Size", sorted(df["collaborateurs"].unique()))
search_query = st.sidebar.text_input("🔎 Search company")

# Apply filters
filtered_df = df.copy()
if pays_HQ_filter:
    filtered_df = filtered_df[filtered_df["pays_HQ"].isin(pays_HQ_filter)]
if industrie_filter:
    filtered_df = filtered_df[filtered_df["industrie"].isin(industrie_filter)]
if marche_filter:
    filtered_df = filtered_df[filtered_df["marche"].isin(marche_filter)]
if collab_filter:
    filtered_df = filtered_df[filtered_df["collaborateurs"].isin(collab_filter)]
if search_query:
    filtered_df = filtered_df[filtered_df["nom"].str.contains(search_query, case=False)]

# Navigation
page = st.sidebar.radio("Navigation", ["Home", "Countries", "Sectors", "Markets", "Companies"])

# -------------------------------
# Helper Functions
# -------------------------------
def revenue_latest(company):
    return company["chiffre_affaires"].get("2024", 0)

# -------------------------------
# Home Page
# -------------------------------
if page == "Home":
    st.title("🏠 GCC Industrial Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        fig_industrie = px.pie(filtered_df, names="industrie", title="Companies by Industry")
        st.plotly_chart(fig_industrie, use_container_width=True)

    with col2:
if not filtered_df.empty:
    fig_pays = px.bar(
        filtered_df["pays_HQ"].value_counts().reset_index(),
        x="index", y="pays_HQ",
        labels={"index": "Country", "pays_HQ": "Number of Companies"},
        title="Companies by HQ Country"
    )
    st.plotly_chart(fig_pays, use_container_width=True)
else:
    st.info("Aucune entreprise à afficher pour ce filtre.")

    # Top 10 by revenue
    st.subheader("💰 Top 10 Companies by 2024 Revenue")
    df_top10 = filtered_df.copy()
    df_top10["revenue_2024"] = df_top10["chiffre_affaires"].apply(lambda x: x.get("2024", 0))
    df_top10 = df_top10.sort_values("revenue_2024", ascending=False).head(10)
    st.dataframe(df_top10[["nom", "industrie", "pays_HQ", "revenue_2024"]])

# -------------------------------
# Countries Page
# -------------------------------
elif page == "Countries":
    st.title("🌍 GCC Countries Overview")
    countries = sorted(set([country for sublist in df["pays_activites"] for country in sublist]))
    selected_country = st.selectbox("Select a country", countries)

    country_df = filtered_df[filtered_df["pays_activites"].apply(lambda x: selected_country in x)]

    st.metric("Number of companies active", len(country_df))
    st.subheader("Top 3 Industries")
    top_industries = country_df["industrie"].value_counts().head(3)
    st.bar_chart(top_industries)

    st.subheader("Companies active in " + selected_country)
    st.dataframe(country_df[["nom", "industrie", "marche", "collaborateurs"]])

# -------------------------------
# Sectors Page
# -------------------------------
elif page == "Sectors":
    st.title("🏭 Sector Analysis")
    sectors = sorted(filtered_df["industrie"].unique())

    for sector in sectors:
        sector_df = filtered_df[filtered_df["industrie"] == sector]
        st.subheader(f"{sector} ({len(sector_df)} companies)")
        sector_df["total_rev"] = sector_df["chiffre_affaires"].apply(lambda x: x.get("2024", 0))
        st.metric("Total 2024 Revenue", f"${sector_df['total_rev'].sum():,.0f}")
        st.dataframe(sector_df[["nom", "marche", "pays_HQ", "collaborateurs"]])

# -------------------------------
# Markets Page
# -------------------------------
elif page == "Markets":
    st.title("📈 Market/Subsector Analysis")
    sub_markets = sorted(filtered_df["marche"].unique())
    selected_market = st.selectbox("Choose a market", sub_markets)

    market_df = filtered_df[filtered_df["marche"] == selected_market]
    st.metric("Number of companies", len(market_df))
    st.subheader("Companies in this market")
    st.dataframe(market_df[["nom", "industrie", "pays_HQ", "collaborateurs"]])

# -------------------------------
# Company Page
# -------------------------------
elif page == "Companies":
    st.title("🏢 Company Directory")
    company_list = sorted(filtered_df["nom"].unique())
    selected_company = st.selectbox("Select a company", company_list)

    company = filtered_df[filtered_df["nom"] == selected_company].iloc[0]
    st.header(company["nom"])

    # Logo
    if company["logo_url"] != "N/A":
        st.image(company["logo_url"], width=200)

    col1, col2 = st.columns(2)
    with col1:
        st.write("**HQ Country:**", company["pays_HQ"])
        st.write("**Countries of Operation:**", ", ".join(company["pays_activites"]))
        st.write("**Industry:**", company["industrie"])
        st.write("**Market:**", company["marche"])
        st.write("**Workforce:**", company["collaborateurs"])
    with col2:
        revenue = company["chiffre_affaires"]
        revenue_df = pd.DataFrame({"Year": list(revenue.keys()), "Revenue (USD)": list(revenue.values())})
        fig = px.bar(revenue_df.sort_values("Year"), x="Year", y="Revenue (USD)", title="Revenue 2020–2024")
        st.plotly_chart(fig, use_container_width=True)

    st.download_button("📄 Download Company Info (JSON)", json.dumps(company.to_dict(), indent=2), file_name=f"{company['nom']}.json")

