import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, URL

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & EXECUTIVE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Social Media Performance & Engagement Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e4e8;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DATA LOADING (MySQL Primary + CSV Fallback)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        # Update password below if connecting live to MySQL
        connection_url = URL.create(
            drivername="mysql+pymysql",
            username="root",
            password="ENTER_YOUR_MYSQL_PASSWORD_HERE",
            host="localhost",
            port=3306,
            database="social_media_db",
            query={"charset": "utf8mb4"}
        )
        engine = create_engine(connection_url)
        df = pd.read_sql("SELECT * FROM posts", con=engine)
        source = "Live MySQL Database (social_media_db.posts)"
    except Exception:
        df = pd.read_csv("cleaned_social_media_posts.csv")
        source = "Cleaned Dataset (cleaned_social_media_posts.csv)"
    return df, source

df, data_source = load_data()

# ---------------------------------------------------------
# 3. SIDEBAR FILTERS (Interactive Controls for Demo)
# ---------------------------------------------------------
st.sidebar.header("Filter Dashboard")
st.sidebar.caption(f"Connected to: **{data_source}**")

platforms = ["All"] + sorted(df["Platform"].dropna().unique().tolist())
selected_platform = st.sidebar.selectbox("Select Platform", platforms)

domains = ["All"] + sorted(df["Domain"].dropna().unique().tolist())
selected_domain = st.sidebar.selectbox("Select Content Domain", domains)

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
available_days = [d for d in days_order if d in df["Day_of_Week"].unique()]
selected_days = st.sidebar.multiselect("Filter by Day of Week", available_days, default=available_days)

# Apply filters
filtered_df = df.copy()
if selected_platform != "All":
    filtered_df = filtered_df[filtered_df["Platform"] == selected_platform]
if selected_domain != "All":
    filtered_df = filtered_df[filtered_df["Domain"] == selected_domain]
if selected_days:
    filtered_df = filtered_df[filtered_df["Day_of_Week"].isin(selected_days)]

# ---------------------------------------------------------
# 4. HEADER & EXECUTIVE KPI CARDS
# ---------------------------------------------------------
st.title("📊 Social Media Analytics & Content Strategy Dashboard")
st.markdown("End-to-end ETL Pipeline: **Python Data Cleaning → MySQL Warehouse → Interactive BI Dashboard**")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Posts Analyzed", f"{len(filtered_df):,}")
kpi2.metric("Total Views", f"{int(filtered_df['Views'].sum()):,}")
kpi3.metric("Total Likes", f"{int(filtered_df['Likes'].sum()):,}")
kpi4.metric("Total Comments", f"{int(filtered_df['Comments'].sum()):,}")
avg_er = filtered_df["Engagement_Rate_Pct"].mean()
kpi5.metric("Avg Engagement Rate", f"{avg_er:.2f}%" if pd.notna(avg_er) else "0.00%")

st.divider()

# ---------------------------------------------------------
# 5. AUTOMATED EXECUTIVE INSIGHTS CALLOUT
# ---------------------------------------------------------
if not filtered_df.empty:
    top_domain = filtered_df.groupby("Domain")["Engagement_Rate_Pct"].mean().idxmax()
    top_domain_er = filtered_df.groupby("Domain")["Engagement_Rate_Pct"].mean().max()
    best_day = filtered_df.groupby("Day_of_Week")["Engagement_Rate_Pct"].mean().idxmax()
    best_hour = int(filtered_df.groupby("Published_Hour")["Engagement_Rate_Pct"].mean().idxmax())

    st.info(
        f"**Executive Takeaways (Filtered View):** **{top_domain}** leads all domains with an average engagement rate of "
        f"**{top_domain_er:.2f}%**. Audience responsiveness peaks on **{best_day}s** around **{best_hour:02d}:00 UTC**."
    )

# ---------------------------------------------------------
# 6. INTERACTIVE CHARTS (ROW 1)
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Engagement Rate & Volume by Domain")
    domain_df = filtered_df.groupby("Domain", as_index=False).agg(
        Avg_Engagement=("Engagement_Rate_Pct", "mean"),
        Total_Posts=("Post_ID", "count"),
        Total_Views=("Views", "sum")
    ).sort_values("Avg_Engagement", ascending=True)

    fig_domain = px.bar(
        domain_df,
        x="Avg_Engagement",
        y="Domain",
        orientation="h",
        text=domain_df["Avg_Engagement"].round(2).astype(str) + "%",
        color="Avg_Engagement",
        color_continuous_scale="Blues",
        hover_data=["Total_Posts", "Total_Views"],
        labels={"Avg_Engagement": "Avg Engagement Rate (%)"}
    )
    fig_domain.update_layout(showlegend=False, coloraxis_showscale=False, height=380)
    st.plotly_chart(fig_domain, use_container_width=True)

with col2:
    st.subheader("Engagement Performance by Day of Week")
    day_df = filtered_df.groupby("Day_of_Week", as_index=False).agg(
        Avg_Engagement=("Engagement_Rate_Pct", "mean"),
        Avg_Views=("Views", "mean"),
        Posts=("Post_ID", "count")
    )
    day_df["Day_of_Week"] = pd.Categorical(day_df["Day_of_Week"], categories=days_order, ordered=True)
    day_df = day_df.sort_values("Day_of_Week")

    fig_day = px.line(
        day_df,
        x="Day_of_Week",
        y="Avg_Engagement",
        markers=True,
        hover_data=["Posts", "Avg_Views"],
        labels={"Day_of_Week": "Day of Week", "Avg_Engagement": "Avg Engagement Rate (%)"}
    )
    fig_day.update_traces(line=dict(width=3, color="#1f77b4"), marker=dict(size=9))
    fig_day.update_layout(height=380)
    st.plotly_chart(fig_day, use_container_width=True)

# ---------------------------------------------------------
# 7. INTERACTIVE CHARTS (ROW 2)
# ---------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("Best Posting Hours (00:00 – 23:00)")
    hour_df = filtered_df.groupby("Published_Hour", as_index=False).agg(
        Avg_Engagement=("Engagement_Rate_Pct", "mean"),
        Posts=("Post_ID", "count")
    )
    fig_hour = px.bar(
        hour_df,
        x="Published_Hour",
        y="Avg_Engagement",
        color="Avg_Engagement",
        color_continuous_scale="Teal",
        hover_data=["Posts"],
        labels={"Published_Hour": "Hour of Day (24h)", "Avg_Engagement": "Avg Engagement Rate (%)"}
    )
    fig_hour.update_layout(coloraxis_showscale=False, height=360)
    st.plotly_chart(fig_hour, use_container_width=True)

with col4:
    st.subheader("Content Type Breakdown")
    type_df = filtered_df.groupby("Content_Type", as_index=False).agg(
        Posts=("Post_ID", "count"),
        Avg_Engagement=("Engagement_Rate_Pct", "mean")
    )
    fig_type = px.pie(
        type_df,
        names="Content_Type",
        values="Posts",
        hole=0.45,
        hover_data=["Avg_Engagement"]
    )
    fig_type.update_layout(height=360)
    st.plotly_chart(fig_type, use_container_width=True)

# ---------------------------------------------------------
# 8. TOP PERFORMING POSTS LEADERBOARD & EXPORT
# ---------------------------------------------------------
st.subheader("🏆 Top 10 Performing Posts")
top_10 = filtered_df.sort_values("Engagement_Rate_Pct", ascending=False)[
    ["Post_ID", "Platform", "Domain", "Content_Type", "Published_Date", "Views", "Likes", "Comments", "Engagement_Rate_Pct", "Post_URL"]
].head(10)

st.dataframe(top_10, use_container_width=True, hide_index=True)

csv_export = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered Report (CSV)",
    data=csv_export,
    file_name="filtered_social_media_report.csv",
    mime="text/csv"
)