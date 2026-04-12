"""Check ElevenLabs models supporting Arabic and available default voices"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("EVEN_LAB_KEY")

# Check models supporting Arabic
r = requests.get("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": key})
models = r.json()
print("=== MODELS SUPPORTING ARABIC ===")
for m in models:
    langs = [lang.get("language_id", "") for lang in m.get("languages", [])]
    has_ar = any("ar" in lid for lid in langs)
    if has_ar:
        print(f"  Model: {m['model_id']}")
        print(f"  Name: {m['name']}")
        print(f"  Description: {m.get('description', '')[:100]}")
        for lang in m.get("languages", []):
            if "ar" in lang.get("language_id", ""):
                print(f"  -> {lang}")
        print()

# Try to do a TTS call with multilingual model
print("\n=== TEST TTS ARABIC ===")
test_text = "كيف داير؟ لاباس عليك؟"  # Darija: How are you? Are you ok?
test_url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Rachel (default voice)
payload = {
    "text": test_text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
}
r = requests.post(
    test_url,
    headers={"xi-api-key": key, "Content-Type": "application/json"},
    json=payload,
)
print(f"TTS Status: {r.status_code}")
if r.status_code == 200:
    with open("test_darija.mp3", "wb") as f:
        f.write(r.content)
    print(f"Audio saved: test_darija.mp3 ({len(r.content)} bytes)")
else:
    print(f"Error: {r.text[:200]}")
