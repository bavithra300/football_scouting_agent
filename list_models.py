import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

print(f"Checking models for key: {api_key[:10]}...")

try:
    client = genai.Client(api_key=api_key)
    print("Listing models...")
    for model in client.models.list():
        print(f" - {model.name}")
except Exception as e:
    print(f"Error: {e}")
