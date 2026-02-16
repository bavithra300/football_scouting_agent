import sys
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Force load .env file
load_dotenv(override=True)

# Debug: Check API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try getting from the old 'GEMINI_API_KEY' if not found
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GOOGLE_API_KEY not found. Please check your .env file.")
    sys.exit(1)

# Ensure environment is set for ADK
os.environ["GOOGLE_API_KEY"] = api_key.strip()
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

try:
    from google.adk.agents.llm_agent import Agent
    from google.adk.tools import google_search
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
except ImportError:
    print("Error: google.adk modules not found. Please ensure the ADK is installed.")
    sys.exit(1)

# --- Configuration ---
MODEL_NAME = 'gemini-2.5-flash' # Reverting to 2.5 as per backup

def print_structured_requirements(reqs):
    print("\n" + "="*40)
    print(" PLAYER / COACH REQUIREMENTS")
    print("="*40)
    for key, value in reqs.items():
        print(f"{key.capitalize():<15}: {value}")
    print("="*40 + "\n")
    sys.stdout.flush()

def run_agent_safe(agent, prompt, step_name="Agent Execution"):
    """
    Runs an ADK agent with exponential backoff for Rate Limits (429).
    """
    print(f"\n--- {step_name} ---")
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=f"football_app_{agent.name}",
        session_service=session_service,
        auto_create_session=True
    )
    
    max_retries = 5
    base_delay = 10 

    for attempt in range(max_retries):
        try:
            events = runner.run(
                user_id="user",
                session_id="session",
                new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
            )
            
            full_response = []
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_response.append(part.text)
            
            result = "".join(full_response)
            if not result:
                return "No response generated."
            return result

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = base_delay * (2 ** attempt)
                print(f"Warning: Rate limit hit (429). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue
            elif "404" in error_str and "not found" in error_str:
                 print(f"Error: Model {agent.model} not found. Please check model availability.")
                 return ""
            else:
                print(f"Error during {step_name}: {e}")
                return ""
    
    print(f"Error: Failed {step_name} after {max_retries} retries.")
    return ""

def collect_user_requirements():
    print("\n--- Football Player & Coach Recommendation System (ADK) ---\n")
    
    while True:
        try:
            choice = input("Do you need a player or a coach? (player/coach): ").strip().lower()
        except EOFError:
            sys.exit(1)
            
        if choice in ['player', 'coach']:
            break
        print("Invalid choice. Please enter 'player' or 'coach'.")

    requirements = {"type": choice}

    try:
        if choice == 'player':
            requirements['position'] = input("Playing position (e.g., Forward): ").strip()
            requirements['age_range'] = input("Age range (e.g., 20-25): ").strip()
            requirements['experience'] = input("Experience (e.g., 3+ years): ").strip()
            requirements['style'] = input("Playing style (e.g., Attacking): ").strip()
        else:
            requirements['style'] = input("Coaching style (e.g., Defensive): ").strip()
            requirements['experience'] = input("Experience (e.g., 5+ years): ").strip()
            requirements['age_range'] = input("Age range (e.g., 40-50): ").strip()
            requirements['focus'] = input("Focus (e.g., Youth Dev): ").strip()
    except EOFError:
        sys.exit(1)
        
    return requirements

# --- Agent Instructions ---

DATA_RETRIEVAL_INSTRUCTIONS = """
You are a Data Retrieval Agent. Search for REAL, ACTIVE football candidates matching the user's criteria.
Output the data in this exact format for each candidate:
- Name: [Name]
- Team/Status: [Current Team or Status]
- Age: [Age]
- Key Stats/Achievements: [Stats]
- Market Value: [Value/Salary]
"""

SCORING_INSTRUCTIONS = """
You are a Scout. Analyze the candidates provided.
Assign a score (0-100) based on:
1. Fit for requirements
2. Recent form/performance
3. Long-term potential

Output:
[Name] - Score: [Score]
Justification: [Brief reason]
"""

RANKING_INSTRUCTIONS = """
You are a Head Scout. Select the TOP 5 candidates.
Present them in a clear, text-based table structure.
Columns: Rank | Name | Score | Key Strength | Current Team
"""

def main():
    # 1. Collect
    user_reqs = collect_user_requirements()
    
    # 2. Display Structured
    print_structured_requirements(user_reqs)
    
    # 3. Initialize Agents
    data_agent = Agent(model=MODEL_NAME, name='data_agent', instruction=DATA_RETRIEVAL_INSTRUCTIONS, tools=[google_search])
    scoring_agent = Agent(model=MODEL_NAME, name='scoring_agent', instruction=SCORING_INSTRUCTIONS)
    ranking_agent = Agent(model=MODEL_NAME, name='ranking_agent', instruction=RANKING_INSTRUCTIONS)

    # 4. Run Pipeline
    
    # Data Retrieval
    if user_reqs['type'] == 'player':
        search_prompt = f"Find 5-7 active football players: Position {user_reqs['position']}, Age {user_reqs['age_range']}, Experience {user_reqs['experience']}, Style {user_reqs['style']}."
    else:
        search_prompt = f"Find 5-7 football coaches: Style {user_reqs['style']}, Experience {user_reqs['experience']}, Age {user_reqs['age_range']}, Focus {user_reqs['focus']}."
        
    data_out = run_agent_safe(data_agent, search_prompt, "Retrieving Data")
    if not data_out: return

    # Scoring
    scoring_prompt = f"User Requirements: {user_reqs}\nCandidates:\n{data_out}"
    score_out = run_agent_safe(scoring_agent, scoring_prompt, "Scoring Candidates")
    if not score_out: return

    # Ranking
    ranking_prompt = f"Rank these candidates:\n{score_out}"
    final_out = run_agent_safe(ranking_agent, ranking_prompt, "Ranking & Recommendations")
    
    print("\n" + "="*40)
    print(" FINAL RECOMMENDATIONS")
    print("="*40)
    print(final_out)

if __name__ == "__main__":
    main()
