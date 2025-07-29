import requests
import jwt
import uuid
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://547a6392-129c-42e0-badb-1a283db0eb37.preview.emergentagent.com"

# Create a test user ID
user_id = str(uuid.uuid4())

# Create a JWT token manually (using the same secret as in the backend)
JWT_SECRET = "onlylands_secret_key_2025"
payload = {
    "user_id": user_id,
    "user_type": "seller",
    "exp": datetime.utcnow() + timedelta(days=7)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print(f"Created test user with ID: {user_id}")
print(f"JWT Token: {token}")

# Headers with the token
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

# Test creating a land listing
listing_data = {
    "title": f"Test Land {uuid.uuid4().hex[:8]}",
    "location": "Test Location, Maharashtra",
    "area": "5 Acres",
    "price": "50 Lakhs",
    "description": "This is a test land listing created for API testing.",
    "latitude": 18.6414,
    "longitude": 72.9897
}

print("\nCreating land listing...")
listing_response = requests.post(f"{BACKEND_URL}/api/listings", json=listing_data, headers=headers)

if listing_response.status_code == 200:
    listing_id = listing_response.json().get('listing_id')
    print(f"Listing created successfully with ID: {listing_id}")
    
    # Test creating a payment order
    payment_data = {
        "amount": 29900,  # ₹299 in paise
        "listing_id": listing_id
    }
    
    print("\nCreating payment order...")
    payment_response = requests.post(f"{BACKEND_URL}/api/payments/create-order", json=payment_data, headers=headers)
    
    if payment_response.status_code == 200:
        order_id = payment_response.json().get('order_id')
        print(f"Payment order created successfully with ID: {order_id}")
        print(f"Amount: {payment_response.json().get('amount')}")
        print(f"Currency: {payment_response.json().get('currency')}")
        print(f"Key ID: {payment_response.json().get('key_id')}")
        
        # Test WhatsApp broadcasting
        print("\nTesting WhatsApp broadcast...")
        broadcast_response = requests.post(f"{BACKEND_URL}/api/broadcast/{listing_id}", headers=headers)
        
        if broadcast_response.status_code == 200:
            print("Broadcast initiated successfully")
            print(f"Response: {broadcast_response.json()}")
        else:
            print(f"Broadcast failed with status code: {broadcast_response.status_code}")
            print(f"Response: {broadcast_response.text}")
    else:
        print(f"Payment order creation failed with status code: {payment_response.status_code}")
        print(f"Response: {payment_response.text}")
else:
    print(f"Listing creation failed with status code: {listing_response.status_code}")
    print(f"Response: {listing_response.text}")

# Test getting listings
print("\nGetting all listings...")
listings_response = requests.get(f"{BACKEND_URL}/api/listings")

if listings_response.status_code == 200:
    listings = listings_response.json().get('listings', [])
    print(f"Retrieved {len(listings)} listings")
    if listings:
        print("First listing:")
        print(f"Title: {listings[0].get('title')}")
        print(f"Location: {listings[0].get('location')}")
        print(f"Status: {listings[0].get('status')}")
else:
    print(f"Failed to get listings with status code: {listings_response.status_code}")
    print(f"Response: {listings_response.text}")