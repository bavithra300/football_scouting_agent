
import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

try:
    import google.adk
    print("google.adk imported successfully")
except ImportError as e:
    print(f"Failed to import google.adk: {e}")

try:
    from google.adk.agents.llm_agent import Agent
    print("Agent class imported successfully")
except ImportError as e:
    print(f"Failed to import Agent: {e}")
