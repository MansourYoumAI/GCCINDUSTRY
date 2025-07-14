import streamlit as st
import pandas as pd
import plotly.express as px
import json

# -------------------------------
# Config
# -------------------------------
st.set_page_config(page_title="Gulf Industry Explorer", layout="wide")

# -------------------------------
# Initialize session state for navigation
# -------------------------------
if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

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
# Sidebar Navigation Only
# -------------------------------
st.sidebar.markdown("## 🧭 Navigation")
if st.sidebar.button("🏠 Home"): st.session_state.page = "🏠 Home"
if st.sidebar.button("🌍 Countries"): st.session_state.page = "🌍 Countries"
if st.sidebar.button("🏭 Sectors"): st.session_state.page = "🏭 Sectors"
if st.sidebar.button("📈 Markets"): st.session_state.page = "📈 Markets"
if st.sidebar.button("🏢 Companies"): st.session_state.page = "🏢 Companies"
page = st.session_state.get("page", "🏠 Home")

# -------------------------------
# Pages
# -------------------------------
if page.startswith("🏠"):
    st.title("🏠 Gulf Industry Explorer v1")

    # Filters directly on page
    col_filters = st.columns([2, 2, 2, 2, 2])
    with col_filters[0]:
        pays_HQ_filter = st.multiselect("📍 HQ Country", sorted(df["pays_HQ"].unique()))
    with col_filters[1]:
        industrie_filter = st.multiselect("🏭 Industry", sorted(df["industrie"].unique()))
    with col_filters[2]:
        marche_filter = st.multiselect("🔍 Market", sorted(df["marche"].unique()))
    with col_filters[3]:
        collab_filter = st.multiselect("👥 Workforce Size", sorted(df["collaborateurs"].unique()))
    with col_filters[4]:
        search_query = st.text_input("🔎 Search company")

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

    col1, col2 = st.columns(2)
    with col1:
        if not filtered_df.empty:
            industry_counts = filtered_df["industrie"].value_counts()
            top_industries = industry_counts[:7]
            other = pd.Series({'Other': industry_counts[7:].sum()})
            final_data = pd.concat([top_industries, other])

            fig_industrie = px.pie(
                names=final_data.index,
                values=final_data.values,
                title="Companies by Industry",
                color=final_data.index,
                color_discrete_sequence=px.colors.sequential.Blues[-8:][::-1],
                category_orders={"industrie": list(top_industries.index) + ["Other"]}
            )
            fig_industrie.update_traces(texttemplate='%{label}: %{percent:.0%}')
            st.plotly_chart(fig_industrie, use_container_width=True)
        else:
            st.info("No data available to build the industry chart.")

    with col2:
        if not filtered_df.empty:
            rev_data = filtered_df.groupby("industrie")["revenue_2024"].sum().sort_values(ascending=False)
            top_revs = rev_data[:7]
            other_rev = pd.Series({'Other': rev_data[7:].sum()})
            final_rev = pd.concat([top_revs, other_rev])

            fig_revenue = px.pie(
                names=final_rev.index,
                values=final_rev.values,
                title="Revenues by Industry",
                color=final_rev.index,
                color_discrete_sequence=px.colors.sequential.Greens[-8:][::-1],
                category_orders={"industrie": list(top_revs.index) + ["Other"]}
            )
            fig_revenue.update_traces(texttemplate='%{label}: %{percent:.0%}')
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No data available for industry revenue.")

    st.subheader("💰 Top 10 Companies by 2024 Revenue")
    df_top10 = filtered_df.sort_values("revenue_2024", ascending=False).head(10).reset_index(drop=True)
    st.table(df_top10[["nom", "industrie", "pays_HQ", "revenue_formatted"]])

    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align: right; font-size: 0.8em;'>Made by Mansour YOUM, July 14 2025 • <a href='https://www.linkedin.com/in/mansour-youm/' target='_blank'>LinkedIn</a></div>", unsafe_allow_html=True)

elif page == "🌍 Countries":
    st.title("🌍 Countries Overview")
    countries = sorted(set([country for sublist in df["pays_activites"] for country in sublist]))
    selected_country = st.selectbox("Select a country", countries)
    country_df = df[df["pays_activites"].apply(lambda x: selected_country in x)]

    st.metric("Number of Companies Active", len(country_df))
    top_industries = country_df.groupby("industrie")["revenue_2024"].sum().sort_values(ascending=False).head(3)
    st.bar_chart(top_industries)

    st.subheader(f"Companies active in {selected_country}")
    st.dataframe(country_df[["nom", "industrie", "marche", "collaborateurs"]])

elif page == "🏭 Sectors":
    st.title("🏭 Sector Analysis")
    sectors = sorted(df["industrie"].unique())
    for sector in sectors:
        sector_df = df[df["industrie"] == sector]
        st.subheader(f"{sector} ({len(sector_df)} companies)")
        st.metric("Total 2024 Revenue", f"${sector_df['revenue_2024'].sum():,.0f}")
        st.dataframe(sector_df[["nom", "marche", "pays_HQ", "collaborateurs"]])

elif page == "📈 Markets":
    st.title("📈 Market/Subsector Analysis")
    sub_markets = sorted(df["marche"].unique())
    selected_market = st.selectbox("Choose a market", sub_markets)
    market_df = df[df["marche"] == selected_market]

    st.metric("Number of companies", len(market_df))
    st.subheader("Companies in this market")
    st.dataframe(market_df[["nom", "industrie", "pays_HQ", "collaborateurs"]])

elif page == "🏢 Companies":
    st.title("🏢 Company Directory")
    search_company = st.text_input("🔍 Search for a company")
    filtered_companies = df[df["nom"].str.contains(search_company, case=False)] if search_company else df
    company_list = sorted(filtered_companies["nom"].unique())
    selected_company = st.selectbox("Select a company", company_list)

    company = df[df["nom"] == selected_company].iloc[0]
    st.header(company["nom"])

    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"<div style='font-size: 1.2em; font-style: italic;'>{company['description']}</div>", unsafe_allow_html=True)
    with cols[1]:
        if company["logo_url"] != "N/A":
            st.image(company["logo_url"], width=120)

    col1, col2 = st.columns(2)
    with col1:
        st.write("**HQ Country:**", company["pays_HQ"])
        st.write("**Countries of Operation:**", ", ".join(company["pays_activites"]))
        st.write("**Industry:**", company["industrie"])
        st.write("**Market:**", company["marche"])
        st.write("**Workforce:**", company["collaborateurs"])
        st.write("**Year Founded:**", company.get("annee_creation", "N/A"))
    with col2:
        revenue_df = pd.DataFrame({
        "Year": ["2024"],
        "Revenue (USD)": [company["chiffre_affaires_2024"]]
})
fig = px.bar(revenue_df, x="Year", y="Revenue (USD)", title="2024 Revenue")
st.plotly_chart(fig, use_container_width=True)


    if company.get("site_web") != "N/A":
        st.markdown(f"🌐 [Website]({company['site_web']})")
    if company.get("linkedin") != "N/A":
        st.markdown(f"🔗 [LinkedIn]({company['linkedin']})")
