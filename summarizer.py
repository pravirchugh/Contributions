import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    print("OPENAI API KEY Invalid.")

url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}

data = {
    "model": "gpt-4o",
    "messages": [
        {
            "role": "user",
            "content": "You are an agent designed to examine a user's commit histories within a GitHub repository and provide a concise bullet-point description of their contributions."
        },
        {
            "role": "system",
            "content": "Hello!"
        },
        {
            "role": "user",
            "content": "What have you been tasked to do? Provide an example."
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(response.json()['choices'][0]['message']['content'])
else:
    print("Error:", response.status_code, response.text)