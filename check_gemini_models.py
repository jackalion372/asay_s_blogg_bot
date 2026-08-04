import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"Testing key prefix: {gemini_key[:12]}...")

client = genai.Client(api_key=gemini_key)

models_to_test = [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.0-pro"
]

for m in models_to_test:
    try:
        res = client.models.generate_content(
            model=m,
            contents="Hello"
        )
        print(f"✅ SUCCESS with model '{m}': {res.text.strip()}")
        break
    except Exception as e:
        print(f"❌ Failed with model '{m}': {e}")
