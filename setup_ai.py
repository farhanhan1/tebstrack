#!/usr/bin/env python
"""
TeBSTrack AI Setup Script - Configure OpenAI API Key
"""

import os
import sys

def setup_openai_key():
    print("=" * 50)
    print("🤖 TeBSTrack AI Setup")
    print("=" * 50)
    print()
    print("This script will help you configure the OpenAI API key for AI features.")
    print()
    print("Steps:")
    print("1. Get your API key from: https://platform.openai.com/account/api-keys")
    print("2. Copy the API key (starts with sk-...)")
    print("3. Enter it below")
    print()
    
    # Check if already set
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        print(f"✅ OpenAI API key is already set: {current_key[:7]}...{current_key[-4:]}")
        choice = input("Do you want to update it? (y/N): ").lower()
        if choice != 'y':
            print("Setup cancelled.")
            return
    
    # Get new API key
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ Error: No API key provided")
        return False
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: API key should start with 'sk-'")
        choice = input("Continue anyway? (y/N): ").lower()
        if choice != 'y':
            return False
    
    # Set environment variable for current session
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Try to set permanently (Windows)
    if os.name == 'nt':
        try:
            import subprocess
            subprocess.run(['setx', 'OPENAI_API_KEY', api_key], check=True, capture_output=True)
            permanent_set = True
        except:
            permanent_set = False
    else:
        # For Unix-like systems, suggest manual setup
        permanent_set = False
    
    print()
    print("=" * 50)
    print("✅ OpenAI API key configured!")
    print("=" * 50)
    print()
    print("Status:")
    print(f"- Current session: ✅ {api_key[:7]}...{api_key[-4:]}")
    
    if permanent_set:
        print("- Future sessions: ✅ Set permanently")
    else:
        print("- Future sessions: ⚠️  Manual setup needed")
        print()
        print("To set permanently:")
        if os.name == 'nt':
            print(f"  setx OPENAI_API_KEY \"{api_key}\"")
        else:
            print(f"  export OPENAI_API_KEY=\"{api_key}\"")
            print("  # Add to ~/.bashrc or ~/.zshrc for persistence")
    
    print()
    print("🚀 What you can do now:")
    print("1. Start TeBSTrack: python run.py")
    print("2. Click the AI chatbot bubble")
    print("3. Use 'Analyze with AI' on tickets")
    print("4. Generate email templates")
    print()
    
    # Test the API key
    test_choice = input("Would you like to test the API key? (y/N): ").lower()
    if test_choice == 'y':
        test_api_key(api_key)
    
    return True

def test_api_key(api_key):
    print("\n🧪 Testing OpenAI API key...")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API key works!'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ API key test successful! Response: {result}")
        
    except ImportError:
        print("⚠️  OpenAI library not found. Install with: pip install openai")
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        if "invalid_api_key" in str(e).lower():
            print("   The API key appears to be invalid.")
        elif "quota" in str(e).lower():
            print("   You may have exceeded your API quota.")
        else:
            print("   Check your API key and try again.")

if __name__ == "__main__":
    try:
        setup_openai_key()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\nError during setup: {e}")
    
    input("\nPress Enter to exit...")
