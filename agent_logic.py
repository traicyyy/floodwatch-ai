import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from flood_tools import get_live_weather, get_infrastructure_status

# Load environment variables from .env file
load_dotenv()

# Verify that the API Key is present
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("CRITICAL ERROR: OPENAI_API_KEY is not set in the .env file.")

# 1. WRAP CUSTOM TOOLS FOR LANGCHAIN
@tool
def check_weather_forecast(city: str) -> str:
    """Useful when you need to fetch the real-time 48-hour forecasted rainfall in mm for a specific city."""
    return get_live_weather(city)

@tool
def check_infrastructure_vulnerability(city: str) -> str:
    """Useful when you need to look up municipal flood control infrastructure assets, pumping stations, and conditions for a specific city."""
    return get_infrastructure_status(city)

# List of tools available to the agent
tools = [check_weather_forecast, check_infrastructure_vulnerability]

# 2. DEFINE THE REASONING ENGINE & SYSTEM INSTRUCTIONS
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

system_prompt = """You are DaloyIntel, an autonomous Risk Assessment Agent specializing in flood risk management for municipalities in the Philippines (specifically Marikina, Pasig, and Cainta).

Your objective is to provide objective, data-backed risk verdicts based strictly on the outputs of your available tools.

CRITICAL OPERATIONAL RULES:
1. Always use multi-step reasoning: First check the weather forecast, then check the city's local infrastructure status before providing a final verdict.
2. If an external API returns an error or a historical fallback baseline, clearly state this to the user. Do NOT hallucinate data.
3. Base your final risk verdict (Low, Medium, High, or Critical Risk) on concrete comparisons: Compare forecasted rainfall levels against structural capacities or known operational issues mentioned in the tool data.
4. Maintain a strictly technical, professional, and advisory tone. Adhere strictly to the Philippine Data Privacy Act—do not request or process any personal user data.
"""

# 3. ASSEMBLE THE AUTONOMOUS AGENT (USING LANGGRAPH)
# LangGraph is the newest, industry-standard way to build LangChain agents.
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

# 4. EXECUTION WRAPPER WITH SHORT-TERM MEMORY CONTEXT
def run_flood_agent(user_input: str, history_list: list) -> str:
    """
    Executes the agent workflow while retaining conversational memory.
    """
    messages = []
    for role, text in history_list:
        messages.append((role, text))
    messages.append(("user", user_input))
        
    try:
        # Run the LangGraph agent
        response = agent_executor.invoke({"messages": messages})
        # Extract the final AI message content
        return response["messages"][-1].content
    except Exception as e:
        return f"System Execution Error: {str(e)}"

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