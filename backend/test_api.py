import google.generativeai as genai

# Paste your API key here
genai.configure(api_key="AIzaSyA-KJXn8KvrR_BK1crArJ_xsTCelVUJCyw")

print("Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Supported Model: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")