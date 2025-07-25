import requests
import sys
import uuid
import time
import base64
import os
import jwt
from datetime import datetime

class OnlyLandsAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.listing_id = None
        self.s3_listing_id = None  # Added for S3 testing
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

    def test_send_otp(self, phone_number, user_type="seller"):
        """Test sending OTP with user_type parameter"""
        success, response = self.run_test(
            f"Send OTP for {user_type}",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": phone_number, "user_type": user_type}
        )
        if success:
            print(f"OTP Status: {response.get('status')}")
            print(f"Message: {response.get('message')}")
            if response.get('demo_info'):
                print(f"Demo Info: {response.get('demo_info')}")
        return success

    def test_verify_otp(self, phone_number, otp_code, user_type="seller"):
        """Test verifying OTP with user_type parameter"""
        success, response = self.run_test(
            f"Verify OTP for {user_type}",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": otp_code, "user_type": user_type}
        )
        if success and response.get('token'):
            self.token = response.get('token')
            user_data = response.get('user', {})
            self.user_id = user_data.get('user_id')
            print(f"Message: {response.get('message')}")
            print(f"User ID: {user_data.get('user_id')}")
            print(f"User Type: {user_data.get('user_type')}")
            print(f"Phone Number: {user_data.get('phone_number')}")
            return True
        return False

    def test_send_otp_missing_phone(self):
        """Test sending OTP with missing phone number"""
        success, response = self.run_test(
            "Send OTP - Missing Phone Number",
            "POST",
            "api/send-otp",
            400,
            data={"user_type": "seller"}
        )
        if success:
            print(f"Error Message: {response.get('detail')}")
        return success

    def test_verify_otp_invalid(self, phone_number, user_type="seller"):
        """Test verifying OTP with invalid OTP"""
        success, response = self.run_test(
            f"Verify OTP - Invalid OTP for {user_type}",
            "POST",
            "api/verify-otp",
            400,
            data={"phone_number": phone_number, "otp": "999999", "user_type": user_type}
        )
        if success:
            print(f"Error Message: {response.get('detail')}")
        return success

    def decode_jwt_token(self, token):
        """Decode JWT token to verify its contents"""
        try:
            # Use the same secret as the backend
            JWT_SECRET = 'your-secure-jwt-secret-key-here-change-this-in-production'
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload
        except Exception as e:
            print(f"Error decoding JWT token: {e}")
            return None

    def test_broker_login_user_type_bug_fix(self):
        """
        CRITICAL TEST: Test the broker login user_type bug fix
        This test verifies that when users select "Login as Broker" and complete OTP verification,
        they are correctly logged in as "Broker" instead of "Seller"
        """
        print("\n" + "="*80)
        print("🚨 CRITICAL BUG FIX TEST: Broker Login User Type")
        print("="*80)
        
        test_phone = "+919876543210"
        demo_otp = "123456"
        
        # Test 1: Seller Login Test
        print("\n📱 TEST 1: SELLER LOGIN")
        print("-" * 40)
        
        # Send OTP for seller
        seller_send_success, seller_send_response = self.run_test(
            "Send OTP for Seller",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": test_phone, "user_type": "seller"}
        )
        
        if not seller_send_success:
            print("❌ CRITICAL FAILURE: Seller OTP send failed")
            return False
            
        # Verify OTP for seller
        seller_verify_success, seller_verify_response = self.run_test(
            "Verify OTP for Seller",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": test_phone, "otp": demo_otp, "user_type": "seller"}
        )
        
        if not seller_verify_success:
            print("❌ CRITICAL FAILURE: Seller OTP verification failed")
            return False
            
        # Decode and verify seller JWT token
        seller_token = seller_verify_response.get('token')
        seller_user = seller_verify_response.get('user', {})
        
        if not seller_token:
            print("❌ CRITICAL FAILURE: No JWT token returned for seller")
            return False
            
        seller_jwt_payload = self.decode_jwt_token(seller_token)
        if not seller_jwt_payload:
            print("❌ CRITICAL FAILURE: Could not decode seller JWT token")
            return False
            
        print(f"✅ Seller JWT Token Payload: {seller_jwt_payload}")
        print(f"✅ Seller User Object: {seller_user}")
        
        # Verify seller user_type in JWT token
        if seller_jwt_payload.get('user_type') != 'seller':
            print(f"❌ CRITICAL FAILURE: Seller JWT token has wrong user_type: {seller_jwt_payload.get('user_type')}")
            return False
        else:
            print("✅ PASS: Seller JWT token has correct user_type: 'seller'")
            
        # Verify seller user_type in user object
        if seller_user.get('user_type') != 'seller':
            print(f"❌ CRITICAL FAILURE: Seller user object has wrong user_type: {seller_user.get('user_type')}")
            return False
        else:
            print("✅ PASS: Seller user object has correct user_type: 'seller'")
        
        # Test 2: Broker Login Test (THE CRITICAL BUG FIX TEST)
        print("\n🏢 TEST 2: BROKER LOGIN (CRITICAL BUG FIX)")
        print("-" * 40)
        
        # Send OTP for broker
        broker_send_success, broker_send_response = self.run_test(
            "Send OTP for Broker",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": test_phone, "user_type": "broker"}
        )
        
        if not broker_send_success:
            print("❌ CRITICAL FAILURE: Broker OTP send failed")
            return False
            
        # Verify OTP for broker
        broker_verify_success, broker_verify_response = self.run_test(
            "Verify OTP for Broker",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": test_phone, "otp": demo_otp, "user_type": "broker"}
        )
        
        if not broker_verify_success:
            print("❌ CRITICAL FAILURE: Broker OTP verification failed")
            return False
            
        # Decode and verify broker JWT token
        broker_token = broker_verify_response.get('token')
        broker_user = broker_verify_response.get('user', {})
        
        if not broker_token:
            print("❌ CRITICAL FAILURE: No JWT token returned for broker")
            return False
            
        broker_jwt_payload = self.decode_jwt_token(broker_token)
        if not broker_jwt_payload:
            print("❌ CRITICAL FAILURE: Could not decode broker JWT token")
            return False
            
        print(f"✅ Broker JWT Token Payload: {broker_jwt_payload}")
        print(f"✅ Broker User Object: {broker_user}")
        
        # THE CRITICAL TEST: Verify broker user_type in JWT token
        if broker_jwt_payload.get('user_type') != 'broker':
            print(f"❌ CRITICAL BUG STILL EXISTS: Broker JWT token has wrong user_type: {broker_jwt_payload.get('user_type')}")
            print("❌ BUG: Users selecting 'Login as Broker' are being logged in with wrong user_type!")
            return False
        else:
            print("✅ BUG FIXED: Broker JWT token has correct user_type: 'broker'")
            
        # Verify broker user_type in user object
        if broker_user.get('user_type') != 'broker':
            print(f"❌ CRITICAL BUG STILL EXISTS: Broker user object has wrong user_type: {broker_user.get('user_type')}")
            print("❌ BUG: Database not updated with correct user_type for broker login!")
            return False
        else:
            print("✅ BUG FIXED: Broker user object has correct user_type: 'broker'")
        
        # Test 3: User Type Switch Test
        print("\n🔄 TEST 3: USER TYPE SWITCHING")
        print("-" * 40)
        
        # Switch back to seller
        seller_switch_success, seller_switch_response = self.run_test(
            "Switch Back to Seller",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": test_phone, "otp": demo_otp, "user_type": "seller"}
        )
        
        if seller_switch_success:
            seller_switch_token = seller_switch_response.get('token')
            seller_switch_user = seller_switch_response.get('user', {})
            seller_switch_jwt = self.decode_jwt_token(seller_switch_token)
            
            if seller_switch_jwt and seller_switch_jwt.get('user_type') == 'seller':
                print("✅ PASS: Successfully switched back to seller")
            else:
                print(f"❌ FAILURE: Could not switch back to seller. JWT user_type: {seller_switch_jwt.get('user_type') if seller_switch_jwt else 'None'}")
                return False
        else:
            print("❌ FAILURE: Could not switch back to seller")
            return False
            
        # Switch back to broker again
        broker_switch_success, broker_switch_response = self.run_test(
            "Switch Back to Broker",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": test_phone, "otp": demo_otp, "user_type": "broker"}
        )
        
        if broker_switch_success:
            broker_switch_token = broker_switch_response.get('token')
            broker_switch_user = broker_switch_response.get('user', {})
            broker_switch_jwt = self.decode_jwt_token(broker_switch_token)
            
            if broker_switch_jwt and broker_switch_jwt.get('user_type') == 'broker':
                print("✅ PASS: Successfully switched back to broker")
            else:
                print(f"❌ FAILURE: Could not switch back to broker. JWT user_type: {broker_switch_jwt.get('user_type') if broker_switch_jwt else 'None'}")
                return False
        else:
            print("❌ FAILURE: Could not switch back to broker")
            return False
        
        # Test 4: JWT Token Verification Details
        print("\n🔐 TEST 4: JWT TOKEN VERIFICATION DETAILS")
        print("-" * 40)
        
        # Verify all required fields in JWT tokens
        required_jwt_fields = ['user_id', 'phone_number', 'user_type', 'exp']
        
        print("Seller JWT Token Fields:")
        for field in required_jwt_fields:
            if field in seller_jwt_payload:
                print(f"  ✅ {field}: {seller_jwt_payload[field]}")
            else:
                print(f"  ❌ Missing field: {field}")
                return False
                
        print("Broker JWT Token Fields:")
        for field in required_jwt_fields:
            if field in broker_jwt_payload:
                print(f"  ✅ {field}: {broker_jwt_payload[field]}")
            else:
                print(f"  ❌ Missing field: {field}")
                return False
        
        # Verify phone numbers match
        if (seller_jwt_payload.get('phone_number') == test_phone and 
            broker_jwt_payload.get('phone_number') == test_phone):
            print("✅ PASS: Phone numbers match in both tokens")
        else:
            print("❌ FAILURE: Phone numbers don't match in tokens")
            return False
            
        # Verify user_ids are the same (same user, different login types)
        if seller_jwt_payload.get('user_id') == broker_jwt_payload.get('user_id'):
            print("✅ PASS: User IDs match (same user, different login types)")
        else:
            print("❌ FAILURE: User IDs don't match")
            return False
        
        print("\n" + "="*80)
        print("🎉 BROKER LOGIN BUG FIX VERIFICATION: ALL TESTS PASSED!")
        print("✅ Seller login works correctly with user_type: 'seller'")
        print("✅ Broker login works correctly with user_type: 'broker'")
        print("✅ User type switching works correctly")
        print("✅ JWT tokens contain correct user_type")
        print("✅ Database is updated correctly when switching user types")
        print("="*80)
        
        return True

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
        
    def test_verify_payment(self):
        """Test payment verification with demo data"""
        if not self.razorpay_order_id or not self.listing_id:
            print("❌ Cannot test payment verification - no order ID or listing ID available")
            return False
            
        # Create demo payment verification data
        payment_data = {
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": f"pay_demo_{int(time.time())}",
            "razorpay_signature": f"demo_signature_{int(time.time())}"
        }
        
        success, response = self.run_test(
            "Verify Payment (Demo Mode)",
            "POST",
            "api/payments/verify",
            200,
            data=payment_data
        )
        
        if success:
            print(f"Status: {response.get('status')}")
            print(f"Message: {response.get('message')}")
            
            # Check if listing status was updated
            time.sleep(1)  # Wait a bit for the database to update
            listing_success, listing_response = self.run_test(
                "Check Listing Status After Payment",
                "GET",
                "api/listings",
                200
            )
            
            if listing_success:
                listings = listing_response.get('listings', [])
                found = False
                for listing in listings:
                    if listing.get('listing_id') == self.listing_id:
                        found = True
                        print(f"Listing Status: {listing.get('status')}")
                        print(f"Payment Status: {listing.get('payment_status')}")
                        print(f"Broadcast Sent: {listing.get('broadcast_sent')}")
                        if listing.get('status') == 'active' and listing.get('payment_status') == 'paid':
                            print("✅ Listing was successfully activated after payment")
                        else:
                            print("❌ Listing was not properly activated after payment")
                            return False
                
                if not found:
                    print("❌ Listing not found after payment verification")
                    return False
            
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
        
    def test_admin_dashboard(self):
        """Test the admin dashboard endpoint"""
        success, response = self.run_test(
            "Admin Dashboard",
            "GET",
            "api/admin/dashboard",
            200
        )
        
        if success:
            print(f"User Statistics: {response.get('statistics', {}).get('users', {})}")
            print(f"Listing Statistics: {response.get('statistics', {}).get('listings', {})}")
            print(f"Recent Activity: {len(response.get('recent_activity', {}).get('listings', []))} listings, {len(response.get('recent_activity', {}).get('users', []))} users")
        return success
    
    def test_admin_users(self):
        """Test the admin users endpoint"""
        success, response = self.run_test(
            "Admin Users",
            "GET",
            "api/admin/users",
            200
        )
        
        if success:
            users = response.get('users', [])
            print(f"Total Users: {response.get('total')}")
            print(f"Users Retrieved: {len(users)}")
        return success
    
    def test_admin_listings(self):
        """Test the admin listings endpoint"""
        success, response = self.run_test(
            "Admin Listings",
            "GET",
            "api/admin/listings",
            200
        )
        
        if success:
            listings = response.get('listings', [])
            print(f"Total Listings: {response.get('total')}")
            print(f"Listings Retrieved: {len(listings)}")
            if listings:
                print(f"First Listing Image Count: {listings[0].get('image_count')}")
                print(f"First Listing Video Count: {listings[0].get('video_count')}")
        return success
    
    def test_admin_brokers(self):
        """Test the admin brokers endpoint"""
        success, response = self.run_test(
            "Admin Brokers",
            "GET",
            "api/admin/brokers",
            200
        )
        
        if success:
            brokers = response.get('brokers', [])
            print(f"Total Brokers: {response.get('total')}")
            print(f"Brokers Retrieved: {len(brokers)}")
        return success
    
    def test_admin_payments(self):
        """Test the admin payments endpoint"""
        success, response = self.run_test(
            "Admin Payments",
            "GET",
            "api/admin/payments",
            200
        )
        
        if success:
            payments = response.get('payments', [])
            print(f"Total Payments: {response.get('total')}")
            print(f"Payments Retrieved: {len(payments)}")
        return success
    
    def test_admin_notifications(self):
        """Test the admin notifications endpoint"""
        success, response = self.run_test(
            "Admin Notifications",
            "GET",
            "api/admin/notifications",
            200
        )
        
        if success:
            notifications = response.get('notifications', [])
            print(f"Total Notifications: {response.get('total')}")
            print(f"Notifications Retrieved: {len(notifications)}")
        return success
    
    def test_upload_media(self, file_path, content_type):
        """Test uploading media files"""
        # Create a test file if it doesn't exist
        if not os.path.exists(file_path):
            if 'image' in content_type:
                # Create a simple test image (1x1 pixel)
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
            elif 'video' in content_type:
                # Create a simple test video file
                with open(file_path, 'wb') as f:
                    f.write(b'TEST VIDEO CONTENT')
        
        # Prepare multipart form data
        files = [('files', (os.path.basename(file_path), open(file_path, 'rb'), content_type))]
        
        url = f"{self.base_url}/api/upload-media"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing Upload Media...")
        
        try:
            response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                result = response.json()
                print(f"Uploaded Files: {len(result.get('uploaded_files', []))}")
                return success, result
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
        finally:
            # Close the file
            for _, file_tuple in files:
                file_tuple[1].close()
    
    def test_create_listing_with_media(self):
        """Test creating a land listing with photos and videos"""
        # Create test files
        test_image_path = '/tmp/test_image.png'
        test_video_path = '/tmp/test_video.mp4'
        
        # Create a simple test image (1x1 pixel)
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        # Create a simple test video file
        with open(test_video_path, 'wb') as f:
            f.write(b'TEST VIDEO CONTENT')
        
        # Prepare form data
        form_data = {
            'title': f"Test Land with Media {uuid.uuid4().hex[:8]}",
            'location': "Test Location, Maharashtra",
            'area': "5 Acres",
            'price': "50 Lakhs",
            'description': "This is a test land listing with photos and videos.",
            'seller_id': self.user_id or "test-seller-123",  # Add seller_id
            'latitude': 18.6414,
            'longitude': 72.9897
        }
        
        # Prepare files
        files = [
            ('images', ('image1.png', open(test_image_path, 'rb'), 'image/png')),
            ('images', ('image2.png', open(test_image_path, 'rb'), 'image/png')),
            ('videos', ('video1.mp4', open(test_video_path, 'rb'), 'video/mp4'))
        ]
        
        url = f"{self.base_url}/api/listings"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing Create Land Listing with Media...")
        
        try:
            response = requests.post(url, data=form_data, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                result = response.json()
                self.listing_id = result.get('listing_id')
                print(f"Listing ID: {self.listing_id}")
                print(f"Status: {result.get('status')}")
                print(f"Images Count: {result.get('images_count')}")
                print(f"Videos Count: {result.get('videos_count')}")
                return success, result
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
        finally:
            # Close the files
            for _, file_tuple in files:
                file_tuple[1].close()
            
            # Clean up test files
            try:
                os.remove(test_image_path)
                os.remove(test_video_path)
            except:
                pass
                
    def test_create_listing_with_s3_storage(self):
        """Test creating a land listing with S3 storage for images"""
        # Create test files
        test_image_path = '/tmp/test_s3_image.png'
        
        # Create a simple test image (1x1 pixel)
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        # Prepare form data with specific seller_id for testing
        form_data = {
            'title': f"S3 Test Land {uuid.uuid4().hex[:8]}",
            'location': "S3 Test Location, Maharashtra",
            'area': "10 Acres",
            'price': "75 Lakhs",
            'description': "This is a test land listing to verify S3 storage integration.",
            'seller_id': "test-seller-123",  # Specific seller_id for testing
            'latitude': 18.6414,
            'longitude': 72.9897
        }
        
        # Prepare files
        files = [
            ('images', ('s3_test_image.png', open(test_image_path, 'rb'), 'image/png'))
        ]
        
        url = f"{self.base_url}/api/listings"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing Create Land Listing with S3 Storage...")
        
        try:
            response = requests.post(url, data=form_data, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                result = response.json()
                self.s3_listing_id = result.get('listing_id')
                print(f"S3 Listing ID: {self.s3_listing_id}")
                print(f"Status: {result.get('status')}")
                print(f"Images Count: {result.get('images_count')}")
                
                # Now test the preview endpoint to verify S3 URL storage
                self.test_preview_endpoint("test-seller-123")
                
                return success, result
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
        finally:
            # Close the files
            for _, file_tuple in files:
                file_tuple[1].close()
            
            # Clean up test files
            try:
                os.remove(test_image_path)
            except:
                pass
                
    def test_preview_endpoint(self, seller_id):
        """Test the preview endpoint for a specific seller"""
        success, response = self.run_test(
            "Get Seller Listings Preview",
            "GET",
            f"api/listings/preview/{seller_id}",
            200
        )
        
        if success:
            listings = response.get('listings', [])
            print(f"Total Seller Listings Retrieved: {len(listings)}")
            
            if listings:
                # Check for S3 URLs in the listings
                s3_listings = 0
                base64_listings = 0
                
                for listing in listings:
                    images = listing.get('images', [])
                    for image in images:
                        if image.get('storage_type') == 's3' and 's3_url' in image:
                            s3_listings += 1
                            s3_url = image.get('s3_url', '')
                            print(f"Found S3 URL: {s3_url}")
                            
                            # Verify S3 URL format
                            if 'onlyland.s3.eu-north-1.amazonaws.com' in s3_url:
                                print(f"✅ S3 URL format is correct")
                            else:
                                print(f"❌ S3 URL format is incorrect: {s3_url}")
                        elif 'data' in image:
                            base64_listings += 1
                
                print(f"S3 Storage Listings: {s3_listings}")
                print(f"Base64 Storage Listings: {base64_listings}")
                
                # Verify hybrid approach works
                if s3_listings > 0:
                    print(f"✅ S3 storage is working correctly")
                else:
                    print(f"❌ No S3 storage listings found")
                    
                # Check if we have both types (hybrid approach)
                if s3_listings > 0 and base64_listings > 0:
                    print(f"✅ Hybrid approach (both S3 and base64) is working")
                
            return True
        return False

def main():
    # Get the backend URL from environment variable
    backend_url = "https://e1833c0e-8697-4c1d-82e1-ad61f5ff183e.preview.emergentagent.com"
    
    print(f"Testing OnlyLands API at: {backend_url}")
    print("=" * 50)
    
    tester = OnlyLandsAPITester(backend_url)
    
    # CRITICAL TEST: Broker Login User Type Bug Fix
    print("\n🚨 RUNNING CRITICAL BROKER LOGIN BUG FIX TEST")
    print("This test verifies the fix for the issue where broker logins were incorrectly")
    print("returning 'seller' user_type instead of 'broker' user_type in JWT tokens.")
    print("=" * 80)
    
    broker_bug_fix_success = tester.test_broker_login_user_type_bug_fix()
    
    if not broker_bug_fix_success:
        print("\n❌ CRITICAL FAILURE: Broker login bug fix test failed!")
        print("The broker login user_type bug still exists.")
        return 1
    
    # Test basic health check
    print("\n🔍 Testing Basic API Health...")
    health_check_success = tester.run_test(
        "API Health Check",
        "GET", 
        "api/",
        200
    )[0]
    
    # Test additional OTP edge cases
    print("\n🔍 Testing OTP Edge Cases...")
    
    # Test missing phone number
    missing_phone_success = tester.test_send_otp_missing_phone()
    
    # Test invalid OTP
    invalid_otp_seller_success = tester.test_verify_otp_invalid("+919876543210", "seller")
    invalid_otp_broker_success = tester.test_verify_otp_invalid("+919876543210", "broker")
    
    # Test missing parameters in verify OTP
    missing_params_success = tester.run_test(
        "Verify OTP - Missing Parameters",
        "POST",
        "api/verify-otp",
        400,
        data={"user_type": "seller"}
    )[0]
    
    # Test listings endpoint
    print("\n🔍 Testing Listings API...")
    listings_success = tester.test_get_listings()
    
    # Print final results
    print("\n" + "=" * 80)
    print("📊 BROKER LOGIN BUG FIX TEST RESULTS")
    print("=" * 80)
    print(f"🚨 CRITICAL: Broker Login Bug Fix: {'✅ PASSED' if broker_bug_fix_success else '❌ FAILED'}")
    print(f"🔍 API Health Check: {'✅ PASSED' if health_check_success else '❌ FAILED'}")
    print(f"🔍 OTP Edge Cases: {'✅ PASSED' if all([missing_phone_success, invalid_otp_seller_success, invalid_otp_broker_success, missing_params_success]) else '❌ FAILED'}")
    print(f"🔍 Listings API: {'✅ PASSED' if listings_success else '❌ FAILED'}")
    print(f"📊 Total Tests: {tester.tests_run}, Passed: {tester.tests_passed}")
    print("=" * 80)
    
    if broker_bug_fix_success:
        print("🎉 SUCCESS: The broker login user_type bug has been successfully fixed!")
        print("✅ Sellers login correctly with user_type: 'seller'")
        print("✅ Brokers login correctly with user_type: 'broker'")
        print("✅ User type switching works correctly")
        print("✅ JWT tokens contain the correct user_type")
        return 0
    else:
        print("❌ FAILURE: The broker login user_type bug still exists!")
        print("❌ Brokers are not being logged in with the correct user_type")
        return 1

if __name__ == "__main__":
    sys.exit(main())