
import sys
import inspect
from google.adk.agents.llm_agent import Agent

try:
    agent = Agent(
        model='gemini-2.5-flash',
        name='test_agent',
        description='test',
        instruction='test',
    )
    print(f"run_live signature: {inspect.signature(agent.run_live)}")

except Exception as e:
    print(f"Error: {e}")
