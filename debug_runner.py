
import sys
import asyncio
from typing import Optional

try:
    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.agents.llm_agent import Agent
    from google.genai import types
    print("Imports successful.")

    agent = Agent(
        model='gemini-2.5-flash',
        name='test_agent',
        description='test',
        instruction='You are a helpful assistant. Just say "Hello World".',
    )

    session_service = InMemorySessionService()
    
    runner = Runner(
        agent=agent,
        app_name="debug_app",
        session_service=session_service
    )
    print("Runner created.")

    print("Running agent...")
    events = runner.run(
        user_id="test_user",
        session_id="test_session",
        new_message=types.Content(role="user", parts=[types.Part(text="Hi")]),
    )
    
    for event in events:
        # print(f"Event: {event}")
        if event.content and event.content.parts:
            print(f"Content: {event.content.parts[0].text}")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    import traceback
    traceback.print_exc()
