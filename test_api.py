"""
Test the chatbot API endpoint directly
"""
import requests
import json

# Test with session to simulate being logged in
session = requests.Session()

# First, try to login (you'll need to replace with actual credentials)
login_url = "http://127.0.0.1:5000/login"
login_data = {
    "username": "admin",  # Replace with actual username
    "password": "password123"  # Replace with actual password
}

# Attempt login
try:
    login_response = session.post(login_url, data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Now test the chatbot API
        chatbot_url = "http://127.0.0.1:5000/api/ai/chatbot"
        chatbot_data = {
            "message": "tell me about this ticket",
            "ticket_id": 4
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        chatbot_response = session.post(chatbot_url, json=chatbot_data, headers=headers)
        print(f"Chatbot API status: {chatbot_response.status_code}")
        print(f"Response headers: {dict(chatbot_response.headers)}")
        
        try:
            response_data = chatbot_response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Raw response: {chatbot_response.text[:500]}")
    else:
        print("Login failed, cannot test chatbot API")
        print(f"Login response: {login_response.text[:200]}")
        
except Exception as e:
    print(f"Error testing API: {e}")
