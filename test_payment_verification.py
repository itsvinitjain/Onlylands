import requests
import jwt
import uuid
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://e1833c0e-8697-4c1d-82e1-ad61f5ff183e.preview.emergentagent.com"

# Use the order ID from the previous test
razorpay_order_id = "order_Qjo1uD8sq4Cir7"
listing_id = "045fef2c-a0b9-4831-a069-aea17ebe5383"

# Create a test payment ID and signature
razorpay_payment_id = f"pay_test_{uuid.uuid4().hex[:10]}"
razorpay_signature = f"sig_test_{uuid.uuid4().hex[:16]}"

# Create a JWT token manually
JWT_SECRET = "onlylands_secret_key_2025"
user_id = str(uuid.uuid4())
payload = {
    "user_id": user_id,
    "user_type": "seller",
    "exp": datetime.utcnow() + timedelta(days=7)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print(f"Using order ID: {razorpay_order_id}")
print(f"Generated payment ID: {razorpay_payment_id}")
print(f"Generated signature: {razorpay_signature}")

# Headers with the token
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

# Test payment verification
payment_data = {
    "razorpay_order_id": razorpay_order_id,
    "razorpay_payment_id": razorpay_payment_id,
    "razorpay_signature": razorpay_signature
}

print("\nVerifying payment...")
verify_response = requests.post(f"{BACKEND_URL}/api/payments/verify", json=payment_data, headers=headers)

if verify_response.status_code == 200:
    print("Payment verified successfully")
    print(f"Response: {verify_response.json()}")
    
    # Check if the listing is now active
    print("\nChecking if listing is now active...")
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
else:
    print(f"Payment verification failed with status code: {verify_response.status_code}")
    print(f"Response: {verify_response.text}")