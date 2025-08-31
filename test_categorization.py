import requests
import json

# Test the categorization API
url = "http://127.0.0.1:5000/api/ai/categorize"
data = {
    "subject": "Need access to server",
    "body": "I need access to the production server for deployment",
    "sender": "user@example.com"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print("Status Code:", response.status_code)
    print("Raw Response:", response.text[:500])  # First 500 chars
    
    if response.headers.get('content-type', '').startswith('application/json'):
        print("JSON Response:", json.dumps(response.json(), indent=2))
    else:
        print("Non-JSON response detected")
        
except Exception as e:
    print("Error:", e)
