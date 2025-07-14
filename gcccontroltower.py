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
# Sidebar Filters and Navigation
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

# Navigation
st.sidebar.markdown("## 🧭 Navigation")
page = st.sidebar.selectbox("Choose a view", ["🏠 Home", "🌍 Countries", "🏭 Sectors", "📈 Markets", "🏢 Companies"])

# -------------------------------
# Pages
# -------------------------------
if page.startswith("🏠"):
    st.title("🏠 GCC Industrial Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        if not filtered_df.empty:
            fig_industrie = px.pie(filtered_df, names="industrie", title="Companies by Industry",
                                   color_discrete_sequence=px.colors.sequential.Blues)
            fig_industrie.update_traces(texttemplate='%{label}: %{percent:.0%}')
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
    for i, row in df_top10.iterrows():
        st.markdown(f"{i+1}. **{row['nom']}** — {row['revenue_formatted']}")
        if st.button(f"View {row['nom']} Details", key=row['nom']):
            st.session_state["page"] = "Companies"
            st.session_state["selected_company"] = row['nom']

elif page.startswith("🌍"):
    st.title("🌍 GCC Countries Overview")
    countries = sorted(set([c for sub in df["pays_activites"] for c in sub]))
    selected_country = st.selectbox("Select a country", countries)
    country_df = filtered_df[filtered_df["pays_activites"].apply(lambda x: selected_country in x)]
    st.metric("Number of companies active", len(country_df))
    st.subheader("Top 3 Industries by Revenue")
    top_industries = country_df.groupby("industrie")["revenue_2024"].sum().sort_values(ascending=False).head(3)
    st.bar_chart(top_industries)
    st.subheader(f"Companies active in {selected_country}")
    st.dataframe(country_df[["nom", "industrie", "marche", "collaborateurs"]])

elif page.startswith("🏭"):
    st.title("🏭 Sector Analysis")
    for sector in sorted(filtered_df["industrie"].unique()):
        sector_df = filtered_df[filtered_df["industrie"] == sector]
        st.subheader(f"{sector} ({len(sector_df)} companies)")
        st.metric("Total 2024 Revenue", f"{sector_df['revenue_2024'].sum() / 1_000_000_000:.1f} BN USD")
        st.dataframe(sector_df[["nom", "marche", "pays_HQ", "collaborateurs"]])

elif page.startswith("📈"):
    st.title("📈 Market/Subsector Analysis")
    sub_markets = sorted(filtered_df["marche"].unique())
    selected_market = st.selectbox("Choose a market", sub_markets)
    market_df = filtered_df[filtered_df["marche"] == selected_market]
    st.metric("Number of companies", len(market_df))
    st.subheader("Companies in this market")
    st.dataframe(market_df[["nom", "industrie", "pays_HQ", "collaborateurs"]])

elif page.startswith("🏢"):
    st.title("🏢 Company Directory")
    selected_company = st.selectbox("Select a company", sorted(filtered_df["nom"].unique()))
    company = df[df["nom"] == selected_company].iloc[0]

    colA, colB = st.columns([3, 1])
    with colA:
        st.subheader(company["nom"])
        st.markdown(f"> {company['description']}")
    with colB:
        if company["logo_url"] != "N/A":
            st.image(company["logo_url"], width=120)

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
        st.metric("2024 Revenue", company["revenue_formatted"])

    st.subheader("🔁 Similar Companies in the Same Market")
    concurrents_df = df[(df["marche"] == company["marche"]) & (df["nom"] != company["nom"])]
    concurrents_df["delta"] = (concurrents_df["revenue_2024"] - company["revenue_2024"]).abs()
    concurrents_df = concurrents_df.sort_values("delta").head(3)
    cols = st.columns(3)
    for i, (_, row) in enumerate(concurrents_df.iterrows()):
        with cols[i]:
            if row["logo_url"] != "N/A":
                st.image(row["logo_url"], width=80)
            st.markdown(f"**{row['nom']}**")
            st.caption(row["revenue_formatted"])

    st.download_button("📄 Download Company Info (JSON)", json.dumps(company.to_dict(), indent=2), file_name=f"{company['nom']}.json")
