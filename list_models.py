import google.generativeai as genai
import os

# Configure API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("API key not found in environment.")
    GEMINI_API_KEY = input("Please enter your Gemini API key: ").strip()
    if not GEMINI_API_KEY:
        print("No API key provided. Exiting.")
        exit(1)

genai.configure(api_key=GEMINI_API_KEY)

print("\nFetching available Gemini models...")
print("=" * 60)

try:
    # List all available models
    models_found = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            models_found.append(model.name)
            print(f"✓ {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print("-" * 50)

    if models_found:
        print(f"\nFound {len(models_found)} available models for generateContent:")
        for model_name in models_found:
            print(f"  - {model_name}")

        # Recommend the best one to use
        print(f"\n🎯 RECOMMENDATION:")
        if any('gemini-1.5-pro' in name for name in models_found):
            recommended = next(name for name in models_found if 'gemini-1.5-pro' in name)
            print(f"   Use: {recommended}")
        elif any('gemini-1.5' in name for name in models_found):
            recommended = next(name for name in models_found if 'gemini-1.5' in name)
            print(f"   Use: {recommended}")
        else:
            recommended = models_found[0]
            print(f"   Use: {recommended}")

        print(f"\n📝 Update your main.py with:")
        print(f"   model = genai.GenerativeModel('{recommended}')")
    else:
        print("No models found that support generateContent!")

except Exception as e:
    print(f"Error fetching models: {e}")
    print("This might be due to API key issues or network connectivity.")
