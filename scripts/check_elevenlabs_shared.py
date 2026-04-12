"""Search shared Arabic voices on ElevenLabs"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("EVEN_LAB_KEY")

# Search shared library for Arabic voices
url = "https://api.elevenlabs.io/v1/shared-voices"
params = {"page_size": 20, "language": "ar", "sort": "usage_character_count_7d"}
r = requests.get(url, headers={"xi-api-key": key}, params=params)
data = r.json()
voices = data.get("voices", [])
print(f"Arabic shared voices found: {len(voices)}\n")
for v in voices[:15]:
    name = v.get("name", "")
    accent = v.get("accent", "")
    gender = v.get("gender", "")
    age = v.get("age", "")
    use_case = v.get("use_case", "")
    vid = v.get("voice_id", "")
    cat = v.get("category", "")
    desc = v.get("description", "")
    print(f"  Name: {name}")
    print(f"  voice_id: {vid}")
    print(f"  accent: {accent} | gender: {gender} | age: {age}")
    print(f"  use_case: {use_case} | category: {cat}")
    print(f"  description: {desc}")
    print()
