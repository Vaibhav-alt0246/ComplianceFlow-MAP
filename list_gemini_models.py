import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("🔍 Listing available Gemini models...")
print("=" * 60)

try:
    for model in client.models.list():
        print(f"✓ {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Description: {model.description}")
        print()
except Exception as e:
    print(f"❌ ERROR: {e}")
