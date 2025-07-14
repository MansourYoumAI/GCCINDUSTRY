import streamlit as st
import pandas as pd
import plotly.express as px
import json

# -------------------------------
# Config
# -------------------------------
st.set_page_config(page_title="Gulf Industry Explorer", layout="wide")
st.sidebar.title("🌍 Gulf Industry Explorer")

# -------------------------------
# Load and cache data
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_json("data/entreprises.json")
    df["revenue_2024"] = df["chiffre_affaires_2024"]
    df["revenue_formatted"] = df["revenue_2024"].apply(lambda x: f"{x / 1_000_000_000:.1f} BN USD" if isinstance(x, (int, float)) else "N/A")
    return df

df = load_data()

# -------------------------------
# Sidebar Filters
# -------------------------------
pays_HQ_filter = st.sidebar.multiselect("📍 HQ Country", sorted(df["pays_HQ"].unique()))
industrie_filter = st.sidebar.multiselect("🏭 Industry", sorted(df["industrie"].unique()))
marche_filter = st.sidebar.multiselect("🔍 Market", sorted(df["marche"].unique()))
collab_filter = st.sidebar.multiselect("👥 Workforce Size", sorted(df["collaborateurs"].unique()))
search_query = st.sidebar.text_input("🔎 Search company")

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

page = st.sidebar.radio("Navigation", ["Home", "Countries", "Sectors", "Markets", "Companies"])

# -------------------------------
# Pages
# -------------------------------
if page == "Home":
    st.title("🏠 GCC Industrial Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        if not filtered_df.empty:
            fig_industrie = px.pie(filtered_df, names="industrie", title="Companies by Industry")
            st.plotly_chart(fig_industrie, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour construire le graphique des industries.")

    with col2:
        if not filtered_df.empty:
            pays_counts = filtered_df["pays_HQ"].value_counts().reset_index()
            pays_counts.columns = ["Country", "Number of Companies"]
            fig_pays = px.bar(pays_counts, x="Country", y="Number of Companies", title="Companies by HQ Country")
            st.plotly_chart(fig_pays, use_container_width=True)
        else:
            st.info("Aucune entreprise à afficher pour ce filtre.")

    st.subheader("💰 Top 10 Companies by 2024 Revenue")
    df_top10 = filtered_df.copy()
    df_top10 = df_top10.sort_values("revenue_2024", ascending=False).head(10)
    df_top10 = df_top10.reset_index(drop=True)
    df_top10.index += 1
    st.dataframe(df_top10[["nom", "industrie", "pays_HQ", "revenue_formatted"]].rename(columns={"nom": "Company", "industrie": "Industry", "pays_HQ": "HQ Country", "revenue_formatted": "2024 Revenue"}))

elif page == "Countries":
    st.title("🌍 GCC Countries Overview")
    countries = sorted(set([c for sub in df["pays_activites"] for c in sub]))
    selected_country = st.selectbox("Select a country", countries)
    country_df = filtered_df[filtered_df["pays_activites"].apply(lambda x: selected_country in x)]
    st.metric("Number of companies active", len(country_df))
    st.subheader("Top 3 Industries")
    st.bar_chart(country_df["industrie"].value_counts().head(3))
    st.subheader(f"Companies active in {selected_country}")
    st.dataframe(country_df[["nom", "industrie", "marche", "collaborateurs"]])

elif page == "Sectors":
    st.title("🏭 Sector Analysis")
    for sector in sorted(filtered_df["industrie"].unique()):
        sector_df = filtered_df[filtered_df["industrie"] == sector]
        st.subheader(f"{sector} ({len(sector_df)} companies)")
        st.metric("Total 2024 Revenue", f"{sector_df['revenue_2024'].sum() / 1_000_000_000:.1f} BN USD")
        st.dataframe(sector_df[["nom", "marche", "pays_HQ", "collaborateurs"]])

elif page == "Markets":
    st.title("📈 Market/Subsector Analysis")
    sub_markets = sorted(filtered_df["marche"].unique())
    selected_market = st.selectbox("Choose a market", sub_markets)
    market_df = filtered_df[filtered_df["marche"] == selected_market]
    st.metric("Number of companies", len(market_df))
    st.subheader("Companies in this market")
    st.dataframe(market_df[["nom", "industrie", "pays_HQ", "collaborateurs"]])

elif page == "Companies":
    st.title("🏢 Company Directory")
    company_list = sorted(filtered_df["nom"].unique())
    selected_company = st.selectbox("Select a company", company_list)
    company = df[df["nom"] == selected_company].iloc[0]

    st.header(company["nom"])
    if company["logo_url"] != "N/A":
        st.image(company["logo_url"], width=200)

    col1, col2 = st.columns(2)
    with col1:
        st.write("**HQ Country:**", company["pays_HQ"])
        st.write("**Countries of Operation:**", ", ".join(company["pays_activites"]))
        st.write("**Industry:**", company["industrie"])
        st.write("**Market:**", company["marche"])
        st.write("**Workforce:**", company["collaborateurs"])
        st.write("**Founded:**", company["annee_creation"])
        st.write("**Website:** [Visit Site](%s)" % company["site_web"])
        st.write("**LinkedIn:** [LinkedIn Profile](%s)" % company["linkedin_url"])
    with col2:
        revenue_df = pd.DataFrame({"Year": ["2024"], "Revenue": [company["revenue_formatted"]]})
        st.metric("2024 Revenue", company["revenue_formatted"])

    st.subheader("🔁 Similar Companies in the Same Market")
    concurrents_df = df[(df["marche"] == company["marche"]) & (df["nom"] != company["nom"])].copy()
    concurrents_df["delta"] = (concurrents_df["revenue_2024"] - company["revenue_2024"]).abs()
    concurrents_df = concurrents_df.sort_values("delta").head(3)
    cols = st.columns(3)
    for i, (_, row) in enumerate(concurrents_df.iterrows()):
        with cols[i]:
            if row["logo_url"] != "N/A":
                st.image(row["logo_url"], width=100)
            st.markdown(f"**{row['nom']}**")
            st.caption(f"{row['revenue_formatted']}")

    st.download_button("📄 Download Company Info (JSON)", json.dumps(company.to_dict(), indent=2), file_name=f"{company['nom']}.json")
