# 🌊 DaloyIntel — Autonomous Flood Risk Assessment Agent

> **DaloyIntel** (from Filipino *daloy* = flow + *intel* = intelligence) is an AI-powered flood risk assessment agent specialized for **Marikina, Pasig, and Cainta** in Metro Manila, Philippines.

It combines **real-time 48-hour weather forecasts** with **user-uploaded infrastructure data** to autonomously produce a structured flood risk verdict, complete with reasoning steps and official LGU emergency response protocols.

Built as a final project for **AI and Unstructured Data Analytics (ANLYTC4)** at Asia Pacific College.

---

## 🔴 Live Demo

> 🚧 Deployment link will be added here after Streamlit Cloud setup.

---

## 📸 Screenshots

### Risk Assessment — Agent Thinking Trace
The agent shows every tool call it makes before producing a verdict.

### Infrastructure Dashboard
KPI cards, risk heatmap, stacked bar charts, and auto-generated executive summary.

---

## ✨ Features

- 💬 **Chat interface** — ask DaloyIntel to assess flood risk for any of the three cities
- 🧠 **Agent Thinking panel** — see every reasoning step the agent takes (ReAct pattern)
- 🌦️ **Real-time weather** — live 48-hour rainfall forecast via Open-Meteo API
- 📊 **Infrastructure dashboard** — KPI cards, risk heatmap, stacked bar chart, pie chart, scatter plot, and executive summary
- 📋 **Protocol retrieval** — automatically appends official LGU emergency response steps for High/Critical risk verdicts
- 📈 **Data Completeness Score** — transparency metric showing how much of the data pipeline succeeded
- ⚠️ **AI disclaimer** — always reminds users to verify decisions with local authorities

---

## 🤖 Agent Architecture

```
User Input (city name)
        ↓
  Streamlit UI
        ↓
LangGraph ReAct Agent (gpt-4o-mini)
   Think → Act → Observe
        ↓
  ┌─────────────────────────────────────┐
  │  Tool 1: check_weather_forecast     │ ← Open-Meteo API
  │  Tool 2: check_infrastructure_      │ ← Uploaded CSV
  │          vulnerability              │
  │  Tool 3: check_emergency_response_  │ ← RAG from
  │          protocols (High/Critical)  │   flood_protocols.txt
  └─────────────────────────────────────┘
        ↓
Risk Verdict + Reasoning Summary
+ Data Completeness Score
        ↓
  ┌──────────────┐  ┌──────────────────────┐
  │ Chat response│  │ Analytics Dashboard  │
  └──────────────┘  └──────────────────────┘
```

### Agentic Capabilities
| Capability | Implementation |
|---|---|
| Multi-step reasoning | ReAct pattern via LangGraph |
| Tool usage | 3 custom tools (weather, infra, protocols) |
| Short-term memory | Conversation history passed per query |
| Decision-making rules | Risk classification via system prompt |

---

## 🗂️ Project Structure

```
floodwatch-ai/
├── app.py                  # Main Streamlit application
├── agent_logic.py          # LangGraph ReAct agent + tools
├── flood_tools.py          # Tool functions (weather, infra, protocols)
├── flood_protocols.txt     # RAG knowledge base — LGU flood response steps
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── sample_data/
│   ├── infrastructure_sample.csv      # 9-asset demo dataset
│   ├── infrastructure_test_data.csv   # 16-asset full dataset
│   └── infrastructure_stress_test.csv # 10-asset worst-case dataset
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| Streamlit | Latest | Web UI framework |
| LangChain | 0.2+ | Agent framework |
| LangGraph | 0.1+ | ReAct agent orchestration |
| OpenAI API | gpt-4o-mini | LLM reasoning engine |
| Plotly | 5.x | Interactive charts and heatmap |
| Pandas | 2.x | CSV parsing and data processing |
| Open-Meteo API | Free | Real-time weather forecasts |
| python-dotenv | Latest | API key management |

---

## 🚀 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/traicyyy/floodwatch-ai.git
cd floodwatch-ai
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the root folder:
```
OPENAI_API_KEY=sk-your-key-here
```
> Get your API key at https://platform.openai.com/api-keys

### 5. Run the app
```bash
streamlit run app.py
```

### 6. Upload a CSV file
Your CSV must have these exact column names:
```
City, Infrastructure_Asset, Current_Status, Design_Capacity_mm, Maintenance_Deficit_Pct
```
Sample files are in the `sample_data/` folder.

---

## 📋 CSV Format

| Column | Description | Example values |
|---|---|---|
| City | Must be Marikina, Pasig, or Cainta | `Pasig` |
| Infrastructure_Asset | Name of the flood structure | `Manggahan Floodway` |
| Current_Status | Operational condition | `Fully Operational`, `Critical Damage`, `Clogged/Silted`, `Under Maintenance`, `Erosion Detected` |
| Design_Capacity_mm | Rainfall capacity in mm | `150` |
| Maintenance_Deficit_Pct | Maintenance backlog % | `45` |

---

## 🧪 Test Scenarios

10 test cases were run across 3 datasets:

| TC# | Dataset | Query | Expected | Actual | Result |
|---|---|---|---|---|---|
| TC-01 | Small | Assess flood risk for Pasig | Low Risk | Low Risk | ✅ PASS |
| TC-02 | Small | Assess flood risk for Cainta | High Risk | High Risk | ✅ PASS |
| TC-03 | Small | Assess flood risk for Marikina | Medium Risk | Medium Risk | ✅ PASS |
| TC-04 | Full | Assess flood risk for Pasig | High Risk | High Risk | ✅ PASS |
| TC-05 | Full | Assess flood risk for Cainta | Critical Risk | Critical Risk | ✅ PASS |
| TC-06 | Full | Assess flood risk for Marikina | High Risk | High Risk | ✅ PASS |
| TC-07 | Stress | Assess flood risk for Pasig | Critical Risk | Critical Risk | ✅ PASS |
| TC-08 | Stress | Assess flood risk for Cainta | Critical Risk | Critical Risk | ✅ PASS |
| TC-09 | Stress | Assess flood risk for Marikina | Critical Risk | Critical Risk | ✅ PASS |
| TC-10 | Full | Can you give more detail? | Detailed breakdown | Detailed breakdown | ✅ PASS |

---

## ⚠️ Responsible AI

- DaloyIntel is an **advisory tool only**. Always verify flood risk decisions with PAGASA, DPWH, or local DRRM offices.
- No personal data is collected or stored. Only infrastructure metrics (public data) are processed.
- The system complies with **Republic Act No. 10173 — Philippine Data Privacy Act of 2012**.
- Known limitations are documented in the project report. The system is designed for single-user prototype use.

---

## 📚 Data Sources

- Infrastructure asset names based on publicly documented **DPWH-PMRCIP** flood control structures in Pasig, Marikina, and Cainta
- Capacity and maintenance values are **simulated for testing** — real deployment would require integration with DPWH's internal asset management system
- Weather data from **Open-Meteo** (https://open-meteo.com) — free, no API key required
- Flood protocols based on standard **Philippine DRRM** response frameworks

---

## 👤 Author

**Tracie Tomon**
Asia Pacific College — BSIT-MI231
ANLYTC4 — AI and Unstructured Data Analytics
Academic Year 2025–2026

---

## 📄 License

MIT License — free to use and modify for academic and non-commercial purposes.
