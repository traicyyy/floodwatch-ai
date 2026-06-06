import streamlit as st
import pandas as pd
from agent_logic import run_flood_agent

# Configure the visual style to "wide" to fit the dashboard
st.set_page_config(page_title="DaloyIntel", page_icon="🌊", layout="wide")


# --- SIDEBAR: ANALYTICS DASHBOARD & UPLOAD ---
with st.sidebar:
    st.header("📊 System Dashboard")
    st.write("Upload municipal data to activate analytics.")
    
    # The CSV File Uploader
    uploaded_file = st.file_uploader("Upload Infrastructure CSV", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read the uploaded CSV using Pandas
            df = pd.read_csv(uploaded_file)
            
            # BULLETPROOF CLEANING: Strip hidden spaces, BOM characters, and quotes from headers
            df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
            
            # Define the exact columns DaloyIntel needs to do its math
            required_columns = ['City', 'Infrastructure_Asset', 'Design_Capacity_mm', 'Current_Status', 'Maintenance_Deficit_Pct']
            
            # Check if the uploaded file has the right columns after cleaning
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                st.error("⚠️ Invalid Dataset Format.")
                st.write("The file you uploaded is missing the following required columns:")
                for col in missing_cols:
                    st.write(f"- `{col}`")
                st.info("Please ensure you are uploading the official DaloyIntel DPWH baseline file.")
            else:
                st.success("Data loaded successfully!")
                st.divider()
                
                # 1. Dashboard Numbers (Metrics)
                st.subheader("Live Metrics")
                total_assets = len(df)
                critical_assets = len(df[df['Maintenance_Deficit_Pct'] > 20])
                
                col1, col2 = st.columns(2)
                col1.metric("Total Assets Tracked", total_assets)
                col2.metric("Critical Alerts", critical_assets, delta="Action Needed", delta_color="inverse")
                
                st.divider()
                
                # 2. Dashboard Graph (Bar Chart)
                st.subheader("Maintenance Deficit (%)")
                chart_data = df[['Infrastructure_Asset', 'Maintenance_Deficit_Pct']].set_index('Infrastructure_Asset')
                st.bar_chart(chart_data)
                
                # 3. Raw Data Viewer
                if st.checkbox("Show Raw Database"):
                    st.dataframe(df)
                    
        except Exception as e:
            st.error("⚠️ Could not read the file. Please ensure it is a standard CSV document.")
            
    else:
        st.info("Awaiting file upload...")


# --- MAIN SCREEN: AI CHAT INTERFACE ---
st.title("🌊 DaloyIntel")
st.markdown("### Autonomous Risk Assessment Agent")
st.write("Specialized for Marikina, Pasig, and Cainta infrastructure analysis.")

# Initialize the chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Field
if prompt := st.chat_input("Ask DaloyIntel for a risk assessment..."):
    
    # Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Run the LangGraph Agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing real-time weather and infrastructure data..."):
            
            history_list = [(m["role"], m["content"]) for m in st.session_state.messages[:-1]]
            agent_response = run_flood_agent(prompt, history_list)
            
            st.markdown(agent_response)
            
    # Save Agent Response to Memory
    st.session_state.messages.append({"role": "assistant", "content": agent_response})