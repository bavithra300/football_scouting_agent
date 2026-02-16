import sys
import os
from dotenv import load_dotenv

# Force load .env file BEFORE importing google libraries
load_dotenv(override=True)

# Debug: Check API Key status
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment or .env file.")
    sys.exit(1)

# Remove GEMINI_API_KEY to prevent conflicts if it exists
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
    
print(f"DEBUG: Loaded GOOGLE_API_KEY (Length: {len(api_key)}, Starts with: {api_key[:4]}...)")

try:
    from google.adk.agents.llm_agent import Agent
    from google.adk.tools import google_search
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.genai import types

    
except ImportError:
    print("Error: google.adk modules not found. Please ensure the ADK is installed.")
    sys.exit(1)


def run_agent(agent, prompt):
    """
    Runs an ADK agent with the given prompt using a temporary runner and session.
    Returns the accumulated text response.
    """
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=f"football_app_{agent.name}",
        session_service=session_service,
        auto_create_session=True
    )
    
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
    
    return "".join(full_response)

def collect_user_requirements():
    """
    Step 1: User Requirement Collection
    Interacts with the user to gather requirements for player or coach recommendation.
    """
    print("\n--- Football Player & Coach Recommendation System ---\n")
    
    while True:
        try:
            choice = input("Do you need a player or a coach? (player/coach): ").strip().lower()
        except EOFError:
            choice = ""
            
        if choice in ['player', 'coach']:
            break
        if choice == "":
            print("Exiting due to empty input (EOF).")
            # Return defaults for testing if needed, or exit
            # return {"type": "player", "position": "forward", "age_range": "20-25", "experience": "3", "style": "attacking"} 
            sys.exit(1)
        print("Invalid choice. Please enter 'player' or 'coach'.")

    requirements = {"type": choice}

    try:
        if choice == 'player':
            requirements['position'] = input("Playing position (Goalkeeper, Defender, Midfielder, Forward): ").strip()
            requirements['age_range'] = input("Preferred age range (e.g., 20-25): ").strip()
            requirements['experience'] = input("Years of experience (e.g., 3+ years): ").strip()
            requirements['style'] = input("Playing style or strengths (e.g., defensive, attacking, playmaker): ").strip()
        else: # coach
            requirements['style'] = input("Coaching style (offensive, defensive, balanced): ").strip()
            requirements['experience'] = input("Experience level (e.g., 5+ years, former player): ").strip()
            requirements['age_range'] = input("Preferred age range (e.g., 40-50): ").strip()
            requirements['focus'] = input("Team development focus (youth development, professional level, etc.): ").strip()
            requirements['budget'] = input("Available Budget (e.g. $5M, High, Unlimited): ").strip()
    except EOFError:
        print("Input interrupted during requirement collection.")
        sys.exit(1)
        
    return requirements

# Define Instructions for Agents
# --- PLAYER INSTRUCTIONS ---
DATA_RETRIEVAL_INSTRUCTIONS_PLAYER = """
You are a Data Retrieval Agent for football scouting.
Your goal is to find detailed, real-time data about football players based on strict user requirements.

RULES:
1. Filter players ONLY within the given AGE and EXPERIENCE range.
2. For GOALKEEPERS, find: Matches, Clean Sheets, Goals Conceded, Saves, Save %.
3. For DEFENDERS, find: Matches, Tackles, Interceptions, Clearances, Duels Won %.
4. For MIDFIELDERS, find: Matches, Goals, Assists, Key Passes, Pass Accuracy %.
5. For FORWARDS, find: Matches, Goals, Assists, Shots on Target, Conversion Rate.
6. Use google_search to find actual 2024/2025 season data.
7. Output a structured list of at least 7 candidates with this specific data.
"""

SCORING_INSTRUCTIONS_PLAYER = """
You are a Scoring Agent, acting as a Professional Head Coach & Scout.
STRICT FILTER: Discard any candidate that does NOT match the Age Range or Experience Range exactly.

For valid candidates, assign a Scout Score (0-100) based on:
1. Position relevance
2. Tactical fit to playing style
3. Performance consistency
4. Long-term potential

Output the list of qualified candidates with their scores and a brief "Coach Note" justifying the score.
"""

RANKING_INSTRUCTIONS_PLAYER = """
You are a Ranking & Recommendation Agent.
Select the Top 5 candidates matching ALL requirements.

IMPORTANT RULES:
1. Filter based on Age/Experience, but DO NOT display them in the final output.
2. Follow the output format EXACTLY.

OUTPUT FORMAT FOR EACH PLAYER:

Rank #: [Rank]
Player Name      : [Name]
Scout Score      : [Score]/100
Current Club     : [Club]
Matches Played   : [Matches]
Role Performance : [Specific role stats, e.g. Clean Sheets/Saves for GK]
Key Strength     : [Main Attribute]

📊 PERFORMANCE ANALYSIS:
[Provide a short, data-driven analysis of the player’s on-field impact, based strictly on their role and playing style.]

🧠 COACH JUSTIFICATION:
[Write 2–3 confident lines in a real coach’s voice explaining:
- Why this player fits the tactical system
- How their strengths support the playing style
- What value they bring to the squad]

Use professional football language.
NO GENERIC PRAISE.
NO MENTION OF AGE OR EXPERIENCE IN THE FINAL OUTPUT.
"""

# --- COACH INSTRUCTIONS (Technical Director Persona) ---
DATA_RETRIEVAL_INSTRUCTIONS_COACH = """
You are a Data Retrieval Agent for football technical directors.
Your goal is to find head coach candidates matching specific requirements.

RULES:
1. Find estimated SALARY or CONTRACT value if available.
2. Focus on: Tactical Identity, Win %, Trophies/Achievements, Youth Development Record.
3. Filter by Age and Experience.
4. Output a list of candidates with their current situation and financial estimates.
"""

SCORING_INSTRUCTIONS_COACH = """
You are a Technical Director evaluating Head Coaches.
CRITICAL RULES:
1. HARD BUDGET CONSTRAINT: Discard any coach whose estimated salary/compensation EXCEEDS the budget.
2. Filter strictly by Age and Experience ranges.

Score (0-100) based on:
1. Tactical Match (Style)
2. Strategic Value (Promotions, Development)
3. Financial Fit

Output qualified candidates only.
"""

RANKING_INSTRUCTIONS_COACH = """
You are a Technical Director.
Recommend Top 5 Coaches.

STRICT RULES:
1. NO "Coach Justification" section.
2. NO player-related stats.
3. Factual, analytical tone only.

OUTPUT FORMAT FOR EACH COACH:

Rank #: [Rank]
Coach Name     : [Name]
Scout Score    : [Score]/100
Current Club   : [Club]
Budget         : [Within Budget comment]
Key Strength   : [Tactical/Strategic Strength]

📊 PERFORMANCE ANALYSIS:
[Factual analysis covering:
- Tactical system and style
- Measurable achievements (promotions, league finishes)
- Suitability for professional level
]

NO MOTIVATIONAL LANGUAGE. NO FUTURE PROMISES.
"""

def create_agents(user_reqs):
    is_coach = user_reqs['type'] == 'coach'
    
    # Select Instructions
    if is_coach:
        data_instr = DATA_RETRIEVAL_INSTRUCTIONS_COACH
        score_instr = SCORING_INSTRUCTIONS_COACH
        rank_instr = RANKING_INSTRUCTIONS_COACH
    else:
        data_instr = DATA_RETRIEVAL_INSTRUCTIONS_PLAYER
        score_instr = SCORING_INSTRUCTIONS_PLAYER
        rank_instr = RANKING_INSTRUCTIONS_PLAYER

    # Step 2: Data Retrieval Agent
    data_agent = Agent(
        model='gemini-2.5-flash',
        name='data_retrieval_agent',
        description='Collects data based on requirements.',
        instruction=data_instr,
        tools=[google_search],
    )

    # Step 3: Scoring Agent
    scoring_agent = Agent(
        model='gemini-2.5-flash',
        name='scoring_agent',
        description='Analyzes data and scores candidates.',
        instruction=score_instr,
    )

    # Step 4: Ranking Agent
    ranking_agent = Agent(
        model='gemini-2.5-flash',
        name='ranking_agent',
        description='Ranks and recommends the top candidates.',
        instruction=rank_instr,
    )
    
    return data_agent, scoring_agent, ranking_agent

def main():
    # Step 1: Collect User Requirements
    user_reqs = collect_user_requirements()
    print(f"\nCollected Requirements: {user_reqs}")
    
    # Initialize Agents
    data_agent, scoring_agent, ranking_agent = create_agents(user_reqs)

    print("\n--- Step 2: Retrieving Data (This may take a moment) ---")
    # Construct a search query/prompt from requirements
    if user_reqs['type'] == 'player':
        search_prompt = f"Find 10 active football players who are {user_reqs['position']}s, aged exactly {user_reqs['age_range']}, with exactly {user_reqs['experience']} experience, playing style: {user_reqs['style']}. IMPORTANT: retrieve role-specific stats (e.g. clean sheets for GK, tackles for DEF, assists for MID, goals for FWD)."
    else:
        search_prompt = f"Find football coaches who have a {user_reqs['style']} style, {user_reqs['experience']} experience, aged {user_reqs['age_range']}, and focus on {user_reqs['focus']}. BUDGET LIMIT: {user_reqs.get('budget', 'Unknown')}. List their key achievements, tactical style, and estimated salary."

    data_response = run_agent(data_agent, search_prompt)
    print("Data Retrieval Complete.")
    
    if not data_response:
        print("Warning: No data retrieved. The agents might not be connected to the internet or search tool failed.")
        # Proceed anyway to see if scoring agent handles it (it will likely complain)

    print("\n--- Step 3: Scoring Candidates ---")
    scoring_prompt = f"Based on the user requirements: {user_reqs}, analyze and score these candidates:\n\n{data_response}"
    scored_data = run_agent(scoring_agent, scoring_prompt)
    print("Scoring Complete.")

    print("\n--- Step 4: Ranking & Recommendations ---")
    ranking_prompt = f"Rank these scored candidates and provide the final Top 5 recommendations:\n\n{scored_data}"
    final_recommendations = run_agent(ranking_agent, ranking_prompt)
    
    print("\n--- Final Recommendations ---")
    print(final_recommendations)

if __name__ == "__main__":
    main()
