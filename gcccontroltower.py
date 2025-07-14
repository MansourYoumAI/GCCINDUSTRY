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
            final_data = top_industries.append(other)

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
            final_rev = top_revs.append(other_rev)

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

# Les autres pages (Countries, Sectors, Markets, Companies) restent inchangées ici
