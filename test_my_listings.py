#!/usr/bin/env python3

import requests
import jwt
import uuid
from datetime import datetime, timedelta

def test_my_listings_auth():
    base_url = "https://91a3d332-8408-4b2f-93db-7686f4570aca.preview.emergentagent.com"
    
    print("Testing /api/my-listings authentication...")
    
    # Test 1: Without any headers
    print("\n1. Testing without any headers:")
    response = requests.get(f"{base_url}/api/my-listings")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")
    
    # Test 2: With empty Authorization header
    print("\n2. Testing with empty Authorization header:")
    headers = {'Authorization': ''}
    response = requests.get(f"{base_url}/api/my-listings", headers=headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")
    
    # Test 3: With invalid token
    print("\n3. Testing with invalid token:")
    headers = {'Authorization': 'Bearer invalid-token'}
    response = requests.get(f"{base_url}/api/my-listings", headers=headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")
    
    # Test 4: With valid token
    print("\n4. Testing with valid token:")
    JWT_SECRET = 'your-secure-jwt-secret-key-here-change-this-in-production'
    test_user_id = str(uuid.uuid4())
    
    payload = {
        "user_id": test_user_id,
        "phone_number": "+919876543210",
        "user_type": "seller",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{base_url}/api/my-listings", headers=headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response text: {response.text}")

if __name__ == "__main__":
    test_my_listings_auth()