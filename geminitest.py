import requests
import json
import os

def test_gemini_api():
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        return

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "AI エージェントって何？"
                    }
                ]
            }
        ]
    }

    response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
    print(response.json())

if __name__ == "__main__":
    test_gemini_api()
