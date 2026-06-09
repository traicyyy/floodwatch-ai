import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from flood_tools import get_live_weather, get_infrastructure_status, get_safety_protocols

# Load environment variables from .env file
load_dotenv()

# Verify that the API Key is present
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("CRITICAL ERROR: OPENAI_API_KEY is not set in the .env file.")

AGENT_TRACE = []   # stores reasoning steps during a run
LAST_INFRA_RESULT = ""

def get_agent_trace():
    return AGENT_TRACE

def clear_agent_trace():
    global AGENT_TRACE
    AGENT_TRACE = []

# 1. WRAP CUSTOM TOOLS FOR LANGCHAIN
@tool
def check_weather_forecast(city: str) -> str:
    """..."""
    result = get_live_weather(city)
    AGENT_TRACE.append(f"🌦️ Weather tool called for {city} → {result}")
    return result

@tool
def check_infrastructure_vulnerability(city: str) -> str:
    """Useful when you need to look up municipal flood control infrastructure assets..."""
    global LAST_INFRA_RESULT
    result = get_infrastructure_status(city)
    LAST_INFRA_RESULT = result                         # store full string
    AGENT_TRACE.append(f"🏗️ Infrastructure tool called for {city} → {result[:100]}...")
    return result

@tool
def check_emergency_response_protocols() -> str:
    """Useful when a High or Critical risk verdict is identified and you need to look up official municipal evacuation and safety action protocols."""
    result = get_safety_protocols()
    AGENT_TRACE.append("📋 Safety protocols retrieved.")
    return result

# List of tools available to the agent
tools = [check_weather_forecast, check_infrastructure_vulnerability, check_emergency_response_protocols]

# 2. DEFINE THE REASONING ENGINE & SYSTEM INSTRUCTIONS
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

system_prompt = """You are DaloyIntel, an autonomous Risk Assessment Agent specializing in flood risk management for municipalities in the Philippines (Marikina, Pasig, Cainta).

Your objective is to provide objective, data‑backed risk verdicts based strictly on the outputs of your available tools.

CRITICAL OPERATIONAL RULES:
1. For ANY request that involves flood risk, infrastructure status, or assessment of a city, you MUST call BOTH tools in order:
   - First, `check_weather_forecast(city)`
   - Then, `check_infrastructure_vulnerability(city)`
   Do NOT skip either tool, even if the user only asks for one of them.
2. If an external API returns an error or a historical fallback baseline, clearly state this to the user. Do NOT hallucinate data.
3. Base your final risk verdict (Low, Medium, High, or Critical Risk) on concrete comparisons: Compare forecasted rainfall levels against structural capacities or known operational issues mentioned in the tool data.
4. Maintain a strictly technical, professional, and advisory tone. Adhere strictly to the Philippine Data Privacy Act—do not request or process any personal user data.
5. Whenever your final risk verdict is HIGH RISK or CRITICAL RISK, you MUST query the emergency response protocols tool and append the specific matching LGU action steps to your final report to guide municipal coordinators.
6. When evaluating risk, treat assets with status "Critical Damage", "Erosion Detected", or "Clogged/Silted" as **severely compromised** – they are at high risk **regardless** of how small the forecasted rainfall is. Do NOT claim that a small rainfall amount “exceeds” the nominal capacity of such an asset; instead, state that the asset’s compromised condition means it cannot reliably handle any significant water flow.
7. After your final verdict, always include a short "Reasoning Summary" (2-3 bullet points of how you arrived at the verdict). Do NOT include a confidence score – a separate system will provide a data‑completeness score.
"""

# 3. ASSEMBLE THE AUTONOMOUS AGENT (USING LANGGRAPH)
# LangGraph is the newest, industry-standard way to build LangChain agents.
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

def compute_confidence(trace: list, city: str) -> int:
    score = 0
    # Weather
    if any("API Error" not in s for s in trace if "Weather tool" in s):
        score += 30
    else:
        score += 15

    # Infrastructure: count lines starting with "- " in the FULL result
    asset_lines = LAST_INFRA_RESULT.count("\n- ")   # each asset line begins with "\n- "
    if asset_lines >= 3:
        score += 40
    elif asset_lines > 0:
        score += 25
    else:
        score += 5

    # Protocols
    if any("Safety protocols" in s for s in trace):
        score += 30
    else:
        score += 10

    return min(score, 100)

# 4. EXECUTION WRAPPER WITH SHORT-TERM MEMORY CONTEXT
def run_flood_agent(user_input: str, history_list: list):
    """
    Executes the agent workflow while retaining conversational memory.
    Returns a tuple: (final_response_string, reasoning_trace_list)
    """
    clear_agent_trace()
    messages = []
    for role, text in history_list:
        messages.append((role, text))
    messages.append(("user", user_input))

    try:
        # Run the LangGraph agent
        response = agent_executor.invoke({"messages": messages})
        
        # Extract the final AI message content
        final_response = response["messages"][-1].content

        # Retrieve the tool-call trace that was recorded globally
        trace = get_agent_trace()

        # Compute initial confidence
        city_mentioned = user_input
        confidence = compute_confidence(trace, city_mentioned)

        # Fallback: force protocol call if verdict is High/Critical but not yet called
        if ("HIGH RISK" in final_response.upper() or "CRITICAL RISK" in final_response.upper()) \
           and not any("Safety protocols" in s for s in trace):
            protocol_result = get_safety_protocols()
            final_response += "\n\n📋 **Emergency Protocols (auto‑retrieved):**\n" + protocol_result
            AGENT_TRACE.append("📋 Safety protocols retrieved (forced).")
            trace = get_agent_trace()
            confidence = compute_confidence(trace, city_mentioned)   # recalculate after adding protocol

        # Now append the Data Completeness Score exactly once
        final_response += f"\n\n📊 **Data Completeness Score:** {confidence}% (based on weather API success, infrastructure data availability, and protocol lookup)"

        return final_response, trace
    except Exception as e:
        return f"System Execution Error: {str(e)}", []


# --- INTERACTIVE TERMINAL TEST BLOCK ---
if __name__ == "__main__":
    print("--- DaloyIntel Agent Reasoning Test ---")
    test_query = "Assess the current flood risk for Marikina based on the forecast and infrastructure status."
    
    print(f"\nUser Prompt: {test_query}\n")
    print("Agent Reasoning Path:")
    
    # For the terminal test, we stream the output so you can see its "thoughts"
    try:
        for step in agent_executor.stream({"messages": [("user", test_query)]}):
            for node_name, node_state in step.items():
                message = node_state["messages"][-1]
                if message.type == "tool":
                    print(f"[Tool Executed] -> Result: {message.content[:100]}...")
                elif message.type == "ai" and message.tool_calls:
                    for tc in message.tool_calls:
                        print(f"[Thought] -> Decided to use tool: {tc['name']} with args: {tc['args']}")
                elif message.type == "ai":
                    print("\n[Final Output] ->")
                    print(message.content)
    except Exception as e:
         print(f"Error: {e}")