import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from agent_logic import run_flood_agent
import flood_tools

# Configure page
st.set_page_config(page_title="DaloyIntel", page_icon="🌊", layout="wide")

# --- CSS STYLING: Static Sidebar & Fixed Chat Input ---
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        resize: none;
        width: 300px !important;
    }
    [data-testid="stSidebarResizeHandle"] {
        display: none;
    }
    section.main > div {
        padding-bottom: 100px;
    }
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 40px;
        left: 300px;
        right: 0;
        padding: 10px 20px;
        background-color: #0e1117;
        z-index: 999;
        border-top: 1px solid #2e2e2e;
        margin: 0 10px;
    }
    .disclaimer-footer {
        position: fixed;
        bottom: 0;
        left: 300px;
        right: 0;
        padding: 26px 20px;
        background-color: #0e1117;
        font-size: 11px;
        color: #888888;
        text-align: center;
        z-index: 998;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: Only file upload & basic controls ---
with st.sidebar:
    st.header("Data Input")
    uploaded_file = st.file_uploader("Upload Infrastructure CSV", type=["csv", "txt"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        except Exception:
            st.error("Could not read file. Try a different delimiter.")
            st.stop()

        # --- Header normalisation (your existing robust code) ---
        raw_cols = list(df.columns)
        clean_cols = [str(c).strip().lower().replace('"', '').replace("'", "")
                      .replace('_', '').replace(' ', '') for c in raw_cols]

        target_keywords = {
            'City': ['city', 'location', 'municipality'],
            'Infrastructure_Asset': ['asset', 'infrastructure', 'name'],
            'Design_Capacity_mm': ['capacity', 'mm', 'design'],
            'Current_Status': ['status', 'condition', 'current'],
            'Maintenance_Deficit_Pct': ['deficit', 'maintenance', 'pct']
        }
        column_mapping = {}
        used_targets = set()
        for original, clean in zip(raw_cols, clean_cols):
            for target, keywords in target_keywords.items():
                if target in used_targets:
                    continue
                if any(kw in clean for kw in keywords):
                    column_mapping[target] = original
                    used_targets.add(target)
                    break

        required_keys = list(target_keywords.keys())
        missing_keys = [k for k in required_keys if k not in column_mapping]

        if missing_keys:
            st.error("⚠️ Incompatible File Layout")
            st.write("Missing: " + ", ".join(missing_keys))
            st.stop()
        else:
            # Rename columns to internal names
            reverse_mapping = {v: k for k, v in column_mapping.items()}
            df = df.rename(columns=reverse_mapping)

            # Ensure numeric
            df['Maintenance_Deficit_Pct'] = pd.to_numeric(df['Maintenance_Deficit_Pct'], errors='coerce').fillna(0)
            df['Design_Capacity_mm'] = pd.to_numeric(df['Design_Capacity_mm'], errors='coerce').fillna(0)

            # Save to global for agent tools
            flood_tools.set_infrastructure_data(df)

            st.success(f"✅ {len(df)} assets loaded across {df['City'].nunique()} cities. Ready for assessment.")

    else:
        st.info("📂 Upload infrastructure data to begin")
        # Clear global data if no file
        flood_tools.set_infrastructure_data(None)

# Add copyright notice at the very bottom of sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; "
    "font-size: 14px; color: #888888; "
    "margin-top: auto;'>© DaloyIntel 2026</div>",
    unsafe_allow_html=True
)

# --- MAIN SCREEN: Tabs ---
tab1, tab2 = st.tabs(["💬 Risk Assessment", "📊 Infrastructure Dashboard"])

# ------------------------------------------------------------------
# TAB 1: CHAT INTERFACE
# ------------------------------------------------------------------
with tab1:
    st.title("🌊 DaloyIntel")
    st.markdown("### Autonomous Risk Assessment Agent")
    st.write("Specialized for Marikina, Pasig, and Cainta infrastructure analysis.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Scrollable container for message history
    with st.container():
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input at the bottom (fixed via CSS)
    if prompt := st.chat_input("Ask DaloyIntel for a risk assessment..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing real-time weather and infrastructure data..."):
                history_list = [(m["role"], m["content"]) for m in st.session_state.messages[:-1]]
                # Inside the assistant's spinner:
                response, trace = run_flood_agent(prompt, history_list)

                # Show agent reasoning if trace available
                if trace:
                    with st.expander("🧠 Agent Thinking – click to see reasoning steps"):
                        for step in trace:
                            st.markdown(f"- {step}")

                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown(
        '<div class="disclaimer-footer">DaloyIntel may produce inaccurate information. Always verify critical decisions with local authorities.</div>',
        unsafe_allow_html=True
    )

# ------------------------------------------------------------------
# TAB 2: ANALYTICS DASHBOARD (only if data loaded)
# ------------------------------------------------------------------
with tab2:
    st.title("📊 Infrastructure Analytics")
    df_analytics = flood_tools.get_infrastructure_data()

    if df_analytics is None or df_analytics.empty:
        st.info("Please upload a CSV file in the sidebar to view analytics.")
    else:
        df = df_analytics.copy()

        # Create Risk Level column early
        df['Risk Level'] = pd.cut(df['Maintenance_Deficit_Pct'],
                                  bins=[0, 20, 40, 60, 100],
                                  labels=['Low', 'Medium', 'High', 'Critical'],
                                  right=False)

        # --- 1. Executive Summary ---
        today_str = pd.Timestamp.today().strftime("%B %d, %Y")
        num_cities = df['City'].nunique()
        critical_list = df[df['Risk Level'] == 'Critical']['Infrastructure_Asset'].tolist()
        high_list = df[df['Risk Level'] == 'High']['Infrastructure_Asset'].tolist()
        worst_city_name = df.groupby('City')['Maintenance_Deficit_Pct'].mean().idxmax()
        worst_city_avg = df.groupby('City')['Maintenance_Deficit_Pct'].mean().max()
        health_score_val = max(0, 100 - df['Maintenance_Deficit_Pct'].mean())

        if health_score_val >= 70:
            readiness = "good; the system is generally prepared for typical rainfall"
        elif health_score_val >= 40:
            readiness = "moderate; some assets require attention before the next monsoon"
        else:
            readiness = "poor; urgent maintenance is recommended to avoid failures"

        exec_summary = (
            f"As of **{today_str}**, **{len(df)} assets** across **{num_cities} cities** are monitored. "
            f"**{len(critical_list)}** are in **Critical** condition ({', '.join(critical_list) if critical_list else 'none'}). "
            f"**{len(high_list)}** are at **High** risk. "
            f"The overall health score is **{health_score_val:.0f}%** – indicating **{readiness}**. "
            f"**{worst_city_name}** requires the most attention with an average deficit of **{worst_city_avg:.1f}%**."
        )
        st.markdown(exec_summary)
        st.divider()

        # --- 2. Key Metrics (KPI row) ---
        col1, col2, col3, col4 = st.columns(4)
        total_assets = len(df)
        critical_count = len(df[df['Maintenance_Deficit_Pct'] >= 60])
        high_count = len(df[(df['Maintenance_Deficit_Pct'] >= 40) & (df['Maintenance_Deficit_Pct'] < 60)])
        avg_deficit = df['Maintenance_Deficit_Pct'].mean()

        col1.metric("Total Assets", total_assets)
        col2.metric("Critical Alerts (≥60%)", critical_count, delta_color="inverse")
        col3.metric("High Risk (40–<60%)", high_count, delta_color="off")
        col4.metric("Avg. Deficit %", f"{avg_deficit:.1f}%")

        st.divider()

        # --- 3. Risk Classification Table ---
        st.subheader("🏷️ Asset Risk Classification")
        st.dataframe(df[['City', 'Infrastructure_Asset', 'Current_Status',
                         'Design_Capacity_mm', 'Maintenance_Deficit_Pct', 'Risk Level']],
                     use_container_width=True)
        st.divider()

        with st.expander("📋 Show Raw Database"):
            st.dataframe(df)

        st.divider()

        # --- 4. Visuals (2 columns) ---
        col_left, col_right = st.columns(2)

        with col_left:
            # Stacked bar of risk levels per city (ordered legend)
            risk_counts = df.groupby(['City', 'Risk Level']).size().reset_index(name='Count')
            fig_city_risk = px.bar(risk_counts, x='City', y='Count', color='Risk Level',
                                   title="Risk Level Distribution per City",
                                   color_discrete_map={
                                       'Low': 'green', 'Medium': 'gold',
                                       'High': 'orange', 'Critical': 'red'
                                   },
                                   category_orders={"Risk Level": ["Low", "Medium", "High", "Critical"]},
                                   text_auto=True)
            st.plotly_chart(fig_city_risk, use_container_width=True)
            st.caption("🏙️ **What this shows:** How many assets in each city fall into Low, Medium, High, or Critical risk buckets. "
                       "Cities with tall red/orange segments need immediate resource allocation.")

            # Status distribution pie
            status_counts = df['Current_Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig2 = px.pie(status_counts, values='Count', names='Status',
                          title="Asset Status Distribution")
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("🔧 **What this shows:** The current operational condition of all assets. "
                       "A large 'Critical Damage' slice signals urgent repair needs.")

        with col_right:
            # Deficit by city (box plot)
            fig3 = px.box(df, x='City', y='Maintenance_Deficit_Pct',
                          color='City', title="Deficit % Distribution by City")
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("📈 **What this shows:** How maintenance deficits are spread across cities. "
                       "Wide boxes or high medians indicate inconsistent or poor upkeep in that city.")

            # Risk Heatmap
            # Custom abbreviation dictionary for clean labels
            label_map = {
                "Cainta Junction Drainage Canal": "CJ Drainage",
                "Cainta River Flood Wall (East)": "CR Flood Wall",
                "Highway 2000 Catch Basin": "HW2000 Basin",
                "Ilugin Pumping Station": "Ilugin Pump",
                "Manggahan Floodway Main Channel": "Manggahan FW",
                "Marikina River Dike (Tumana Section)": "MR Dike",
                "Marikina Sports Center Retention Basin": "MSC Basin",
                "Nangka River Revetment Wall": "Nangka Wall",
                "Napindan Hydraulic Control Structure": "Napindan HCS",
                "Pasig-Marikina River Control Gate": "PM Control Gate",
                "Provident Village Pumping Station": "Provident Pump",
                "Rosario Weir Floodgates": "Rosario Weir",
                "Santolan Flood Barrier": "Santolan Barrier",
                "Tapayan Pumping Station": "Tapayan Pump",
                "Tikling Road Retention Pond": "Tikling Pond",
                "Tumana Bridge Flood Gate": "Tumana Gate"
            }

            df['Short_Label'] = df['Infrastructure_Asset'].map(
                label_map
            ).fillna(df['Infrastructure_Asset'])

            heatmap_data = df.pivot_table(values='Maintenance_Deficit_Pct',
                                          index='City', columns='Short_Label',
                                          aggfunc='mean')
            
            # Create a pivot table with full asset names for customdata (tooltip)
            heatmap_df = df.copy()
            pivot_full = heatmap_df.pivot_table(
                index="City",
                columns="Short_Label",
                values="Infrastructure_Asset",
                aggfunc="first"
            )

            # Create go.Heatmap with customdata for full asset names
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                customdata=pivot_full.values,
                colorscale="Reds",
                text=heatmap_data.values,
                texttemplate="%{text:.1f}",
                textfont=dict(size=10, color="white"),
                hovertemplate=(
                    "Asset: %{customdata}<br>"
                    "City: %{y}<br>"
                    "Deficit: %{z}%"
                    "<extra></extra>"
                )
            ))

            # Update layout for better x-axis label readability
            fig_heat.update_layout(
                title="Risk Heatmap: Deficit % by City & Asset",
                xaxis=dict(tickangle=-35, tickfont=dict(size=10), title="Infrastructure Asset"),
                yaxis=dict(title="City"),
                margin=dict(b=100),
                coloraxis_colorbar=dict(title="Deficit %")
            )

            st.plotly_chart(fig_heat, use_container_width=True)
            st.caption("🔥 **What this shows:** A bird’s‑eye view of problem areas. "
                       "Darker red cells = higher deficit = priority. Helps spot the worst asset in the worst city instantly.")

        st.divider()

        # --- 5. System Health Bar ---
        st.subheader("🩺 Overall System Health")
        health_score_val = max(0, 100 - df['Maintenance_Deficit_Pct'].mean())   # ensure it's current

        # Color code
        if health_score_val >= 70:
            health_color = "green"
        elif health_score_val >= 40:
            health_color = "orange"
        else:
            health_color = "red"

        # Progress bar (value between 0.0 and 1.0)
        st.progress(health_score_val / 100, text=f"{health_score_val:.0f}% – System Readiness")
        st.caption(
            f"This score is the inverse of the average maintenance deficit. "
            f"A higher score means fewer outstanding repairs and better flood readiness. "
            f"Current status: **{readiness}**."
        )

        st.divider()

        # --- 6. Key Recommendations ---
        st.subheader("📋 Key Recommendations")

        critical_assets = df[df['Risk Level'] == 'Critical']
        high_assets = df[df['Risk Level'] == 'High']

        recommendations = []

        if len(critical_assets) > 0:
            rec = f"🚨 **Immediate Action:** {len(critical_assets)} asset(s) are in **Critical** condition. " \
                  f"Focus repair crews on: {', '.join(critical_assets['Infrastructure_Asset'].tolist())}."
            recommendations.append(rec)

        if len(high_assets) > 0:
            rec = f"⚠️ **High Priority:** {len(high_assets)} asset(s) are at **High Risk**. " \
                  f"Schedule preventive maintenance for: {', '.join(high_assets['Infrastructure_Asset'].tolist())}."
            recommendations.append(rec)

        if not critical_assets.empty or not high_assets.empty:
            recommendations.append(f"📍 **Geographic Focus:** {worst_city_name} shows the highest average deficit ({worst_city_avg:.1f}%). "
                                   "Consider allocating additional budget and resources there.")

        status_problems = df[df['Current_Status'].isin(['Critical Damage', 'Erosion Detected', 'Clogged/Silted'])]
        if not status_problems.empty:
            rec = f"🔍 **Status Alerts:** The following assets have hazardous operational status: " \
                  f"{', '.join(status_problems['Infrastructure_Asset'].tolist())}. Immediate inspection recommended."
            recommendations.append(rec)

        if not recommendations:
            recommendations.append("✅ All assets are within acceptable maintenance levels. Continue routine monitoring.")

        for r in recommendations:
            st.markdown(r)