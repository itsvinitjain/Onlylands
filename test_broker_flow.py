import requests
import jwt
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://33ca28b1-5bbc-432a-bf14-76b1e4dca3a4.preview.emergentagent.com"

# Get the broker ID from the previous test
# We'll use the broker we registered during the API test
broker_id = "7e156b0a-2285-487c-abda-8ab57f1992be"

# Create a JWT token manually for the broker
JWT_SECRET = "onlylands_secret_key_2025"
payload = {
    "user_id": broker_id,
    "user_type": "broker",
    "exp": datetime.utcnow() + timedelta(days=7)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print(f"Using broker with ID: {broker_id}")
print(f"JWT Token: {token}")

# Headers with the token
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

# Test getting broker leads
print("\nGetting broker leads...")
leads_response = requests.get(f"{BACKEND_URL}/api/brokers/{broker_id}/leads", headers=headers)

if leads_response.status_code == 200:
    leads = leads_response.json().get('leads', [])
    print(f"Retrieved {len(leads)} leads")
    if leads:
        print("First lead:")
        print(f"Title: {leads[0].get('title')}")
        print(f"Location: {leads[0].get('location')}")
        print(f"Status: {leads[0].get('status')}")
else:
    print(f"Failed to get leads with status code: {leads_response.status_code}")
    print(f"Response: {leads_response.text}")

# Test getting all brokers
print("\nGetting all brokers...")
brokers_response = requests.get(f"{BACKEND_URL}/api/brokers")

if brokers_response.status_code == 200:
    brokers = brokers_response.json().get('brokers', [])
    print(f"Retrieved {len(brokers)} brokers")
    if brokers:
        print("First broker:")
        print(f"Name: {brokers[0].get('name')}")
        print(f"Agency: {brokers[0].get('agency')}")
        print(f"Phone: {brokers[0].get('phone')}")
else:
    print(f"Failed to get brokers with status code: {brokers_response.status_code}")
    print(f"Response: {brokers_response.text}")