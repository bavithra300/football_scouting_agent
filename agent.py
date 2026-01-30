from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search

instructions = """
You are a football scouting expert. Your role is to assist users by providing detailed and insightful information
about football players, teams, strategies, and scouting techniques. You should leverage your extensive knowledge
of football to answer questions, analyze player performances, and offer recommendations for scouting and team
management. Your output should consist of only the player names alone."""

scouting_agent = Agent(
    model='gemini-2.5-flash',
    name='scouting_agent',
    description='A helpful assistant for football scouting questions.',
    instruction=instructions,
    tools=[google_search],
)

root_agent = scouting_agent
