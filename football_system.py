import sys
import os
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

# SANITIZE KEY
api_key = api_key.strip()

# Prepare clean environment for google.genai
os.environ["GOOGLE_API_KEY"] = api_key
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

print(f"DEBUG: Using API Key: {repr(api_key)}")
print(f"DEBUG: Key length: {len(api_key)}")

# Initialize Client
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Error initializing Google GenAI Client: {e}")
    sys.exit(1)

import time

def run_step(step_name, prompt, model_name='gemini-2.0-flash-lite-001', tools=None):
    """
    Executes a single step in the agent pipeline using the Gemini API.
    Includes retry logic for Rate Limits (429).
    """
    print(f"\n--- {step_name} ---")
    
    max_retries = 5
    base_delay = 10  # Start with 10 seconds

    for attempt in range(max_retries):
        try:
            if tools:
                # For data retrieval, use Google Search tool
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=tools,
                        response_modalities=["TEXT"]
                    )
                )
            else:
                # Standard generation
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
            if response.text:
                return response.text
            else:
                # Verify if parts exist
                if response.candidates and response.candidates[0].content.parts:
                    return "".join([part.text for part in response.candidates[0].content.parts if part.text])
                return "No text response generated."
                
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = base_delay * (2 ** attempt) # Exponential backoff: 10, 20, 40, 80...
                print(f"Warning: Rate limit hit (429). Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Error during {step_name}: {e}")
                return ""
    
    print(f"Error: Failed {step_name} after {max_retries} retries due to rate limits.")
    return ""

def collect_user_requirements():
    """
    Step 1: User Requirement Collection
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
    except EOFError:
        print("Input interrupted.")
        sys.exit(1)
        
    return requirements

def main():
    # Step 1: Collect Inputs
    user_reqs = collect_user_requirements()
    print(f"\nCollected Requirements: {user_reqs}")

    # Step 2: Data Retrieval (Search)
    # Use google search tool
    google_search_tool = [types.Tool(google_search=types.GoogleSearch())]
    
    if user_reqs['type'] == 'player':
        search_prompt = f"""
        Act as a Data Retrieval Agent. Find currently active football players who match these criteria:
        - Position: {user_reqs['position']}
        - Age: {user_reqs['age_range']}
        - Experience: {user_reqs['experience']}
        - Style: {user_reqs['style']}
        
        Use Google Search to find REAL, CURRENT data. 
        List at least 5-7 potential candidates with their current team, key stats from the last season, and market value.
        """
    else:
        search_prompt = f"""
        Act as a Data Retrieval Agent. Find football coaches matching these criteria:
        - Style: {user_reqs['style']}
        - Experience: {user_reqs['experience']}
        - Age: {user_reqs['age_range']}
        - Focus: {user_reqs['focus']}
        
        Use Google Search to find REAL, CURRENT data.
        List at least 5-7 potential candidates with their current status, recent achievements, and tactical preferences.
        """

    data_output = run_step("Step 2: Retrieving Data", search_prompt, tools=google_search_tool)
    print("search result received") # feedback
    
    if not data_output or "No text response" in data_output:
        print("Warning: Search failed to return useful text. The system might hallucinate or fail.")
    
    # Step 3: Scoring
    scoring_prompt = f"""
    Act as a Football Scout/Coach (Scoring Agent).
    Analyze these candidates based on the user requirements: {user_reqs}
    
    Candidate Data:
    {data_output}
    
    Task:
    Assign a score (0-100) to each candidate based on:
    1. Performance Consistency
    2. Skill/Tactical Fit
    3. Experience
    
    Provide the list with scores and a brief 1-sentence justification for the score.
    """
    
    scored_output = run_step("Step 3: Scoring Candidates", scoring_prompt)
    print(scored_output)

    # Step 4: Ranking
    ranking_prompt = f"""
    Act as a Recommendation Agent.
    Based on these scored candidates:
    {scored_output}
    
    Task:
    1. Select the Top 5.
    2. Format the output nicely for the user. 
    3. For each recommendation include: Name, Current Team, key reason for recommendation, and final score.
    """
    
    final_output = run_step("Step 4: Final Recommendations", ranking_prompt)
    print("\n" + "="*30)
    print("FINAL RECOMMENDATIONS")
    print("="*30)
    print(final_output)

if __name__ == "__main__":
    main()
