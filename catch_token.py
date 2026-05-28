import requests, os
from dotenv import load_dotenv

# 1. Load env file
load_dotenv()

# 2. Define the token endpoint and payload
token_url = "https://api.digikey.com/v1/oauth2/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": os.getenv("CLIENT_ID"),
    "client_secret": os.getenv("CLIENT_SECRET")
}
token_headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

# 3. Make the request
token_response = requests.post(token_url,token_data,headers=token_headers)

if token_response.status_code == 200:
    # Extract the token
    access_token = token_response.json().get("access_token")
    print("Successfully retrieved access token!")
else:
    print(f"Failed to get token: {token_response.status_code}")
    print(token_response.text)