import requests
import sys
import uuid
import time
from datetime import datetime

class OnlyLandsAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.listing_id = None
        self.broker_id = None
        self.razorpay_order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if not headers:
            headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        if success:
            print(f"Health Status: {response.get('status')}")
            print(f"Database: {response.get('database')}")
        return success

    def test_stats(self):
        """Test the stats endpoint"""
        success, response = self.run_test(
            "Platform Statistics",
            "GET",
            "api/stats",
            200
        )
        if success:
            print(f"Total Listings: {response.get('total_listings')}")
            print(f"Active Listings: {response.get('active_listings')}")
            print(f"Total Brokers: {response.get('total_brokers')}")
            print(f"Active Brokers: {response.get('active_brokers')}")
            print(f"Total Payments: {response.get('total_payments')}")
        return success

    def test_send_otp(self, phone_number):
        """Test sending OTP"""
        success, response = self.run_test(
            "Send OTP",
            "POST",
            "api/auth/send-otp",
            200,
            data={"phone_number": phone_number}
        )
        if success:
            print(f"OTP Status: {response.get('status')}")
            print(f"Phone: {response.get('phone')}")
        return success

    def test_verify_otp(self, phone_number, otp_code):
        """Test verifying OTP"""
        success, response = self.run_test(
            "Verify OTP",
            "POST",
            "api/auth/verify-otp",
            200,
            data={"phone_number": phone_number, "otp_code": otp_code}
        )
        if success and response.get('verified'):
            self.token = response.get('token')
            self.user_id = response.get('user_id')
            print(f"Verified: {response.get('verified')}")
            print(f"User ID: {response.get('user_id')}")
            print(f"User Type: {response.get('user_type')}")
            return True
        return False

    def test_create_listing(self):
        """Test creating a land listing"""
        listing_data = {
            "title": f"Test Land {uuid.uuid4().hex[:8]}",
            "location": "Test Location, Maharashtra",
            "area": "5 Acres",
            "price": "50 Lakhs",
            "description": "This is a test land listing created for API testing.",
            "latitude": 18.6414,
            "longitude": 72.9897
        }
        
        success, response = self.run_test(
            "Create Land Listing",
            "POST",
            "api/listings",
            200,
            data=listing_data
        )
        
        if success:
            self.listing_id = response.get('listing_id')
            print(f"Listing ID: {self.listing_id}")
            print(f"Status: {response.get('status')}")
        return success

    def test_get_listings(self):
        """Test getting all listings"""
        success, response = self.run_test(
            "Get Listings",
            "GET",
            "api/listings",
            200
        )
        
        if success:
            listings = response.get('listings', [])
            print(f"Total Listings Retrieved: {len(listings)}")
            if listings:
                print(f"First Listing: {listings[0].get('title')}")
        return success

    def test_register_broker(self):
        """Test broker registration"""
        broker_data = {
            "name": f"Test Broker {uuid.uuid4().hex[:8]}",
            "agency": "Test Agency",
            "phone": f"+9198{uuid.uuid4().hex[:8]}",
            "email": f"test{uuid.uuid4().hex[:8]}@example.com",
            "location": "Mumbai, Maharashtra"
        }
        
        success, response = self.run_test(
            "Register Broker",
            "POST",
            "api/brokers/register",
            200,
            data=broker_data
        )
        
        if success:
            self.broker_id = response.get('broker_id')
            print(f"Broker ID: {self.broker_id}")
            print(f"Status: {response.get('status')}")
        return success

    def test_get_brokers(self):
        """Test getting all brokers"""
        success, response = self.run_test(
            "Get Brokers",
            "GET",
            "api/brokers",
            200
        )
        
        if success:
            brokers = response.get('brokers', [])
            print(f"Total Brokers Retrieved: {len(brokers)}")
            if brokers:
                print(f"First Broker: {brokers[0].get('name')}")
        return success

    def test_create_payment_order(self):
        """Test creating a payment order"""
        if not self.listing_id:
            print("❌ Cannot test payment - no listing ID available")
            return False
            
        payment_data = {
            "amount": 29900,  # ₹299 in paise
            "listing_id": self.listing_id
        }
        
        success, response = self.run_test(
            "Create Payment Order",
            "POST",
            "api/payments/create-order",
            200,
            data=payment_data
        )
        
        if success:
            self.razorpay_order_id = response.get('order_id')
            print(f"Order ID: {self.razorpay_order_id}")
            print(f"Amount: {response.get('amount')}")
            print(f"Currency: {response.get('currency')}")
            print(f"Key ID: {response.get('key_id')}")
        return success

    def test_whatsapp_broadcast(self):
        """Test WhatsApp broadcasting"""
        if not self.listing_id:
            print("❌ Cannot test broadcast - no listing ID available")
            return False
            
        success, response = self.run_test(
            "WhatsApp Broadcast",
            "POST",
            f"api/broadcast/{self.listing_id}",
            200
        )
        
        if success:
            print(f"Total Brokers: {response.get('total_brokers', 0)}")
            print(f"Success Count: {response.get('success_count', 0)}")
            print(f"Failed Count: {response.get('failed_count', 0)}")
            if response.get('error'):
                print(f"Error: {response.get('error')}")
                return False
        return success

def main():
    # Get the backend URL from environment variable
    backend_url = "https://88f8fa02-c167-4ec2-8817-e66be1aafac0.preview.emergentagent.com"
    
    print(f"Testing OnlyLands API at: {backend_url}")
    print("=" * 50)
    
    tester = OnlyLandsAPITester(backend_url)
    
    # Test basic endpoints
    health_check_success = tester.test_health_check()
    stats_success = tester.test_stats()
    
    # Test OTP authentication (will likely fail with real Twilio)
    phone_number = "+919876543210"  # Test phone number
    otp_code = "123456"  # Test OTP code
    
    print("\n🔍 Testing OTP Authentication Flow...")
    print("Note: This will likely fail with real Twilio integration unless sandbox is configured")
    
    otp_send_success = tester.test_send_otp(phone_number)
    
    # We'll skip actual OTP verification since we don't have a real OTP
    # Instead, we'll just test the endpoint with a dummy OTP
    otp_verify_success = tester.test_verify_otp(phone_number, otp_code)
    
    # Test listing creation and retrieval
    if tester.token:
        print("\n🔍 Testing with authenticated user...")
        listing_create_success = tester.test_create_listing()
        listing_get_success = tester.test_get_listings()
    else:
        print("\n⚠️ Skipping authenticated tests - no token available")
        listing_get_success = tester.test_get_listings()
    
    # Test broker registration and retrieval
    broker_register_success = tester.test_register_broker()
    broker_get_success = tester.test_get_brokers()
    
    # Test payment order creation
    if tester.listing_id:
        payment_success = tester.test_create_payment_order()
    else:
        print("\n⚠️ Skipping payment test - no listing ID available")
        payment_success = False
    
    # Test WhatsApp broadcasting
    if tester.listing_id:
        broadcast_success = tester.test_whatsapp_broadcast()
    else:
        print("\n⚠️ Skipping broadcast test - no listing ID available")
        broadcast_success = False
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    # Return success if all critical tests passed
    critical_tests = [health_check_success, stats_success, listing_get_success]
    return 0 if all(critical_tests) else 1

if __name__ == "__main__":
    sys.exit(main())