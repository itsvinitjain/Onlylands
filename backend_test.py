import requests
import sys
import uuid
import time
import base64
import os
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

    def test_verify_otp_missing_params(self):
        """Test verifying OTP with missing parameters"""
        success, response = self.run_test(
            "Verify OTP - Missing Parameters",
            "POST",
            "api/verify-otp",
            400,
            data={"user_type": "seller"}
        )
        if success:
            print(f"Error Message: {response.get('detail')}")
        return success

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
    
    # Test basic endpoints
    health_check_success = tester.test_health_check()
    stats_success = tester.test_stats()
    
    # Test admin panel endpoints
    print("\n🔍 Testing Admin Panel Endpoints...")
    admin_dashboard_success = tester.test_admin_dashboard()
    admin_users_success = tester.test_admin_users()
    admin_listings_success = tester.test_admin_listings()
    admin_brokers_success = tester.test_admin_brokers()
    admin_payments_success = tester.test_admin_payments()
    admin_notifications_success = tester.test_admin_notifications()
    
    # Test OTP authentication with demo mode
    phone_number = "+917021758061"  # Test phone number from requirements
    otp_code = "123456"  # Demo OTP code
    
    print("\n🔍 Testing OTP Authentication Flow in Demo Mode...")
    
    # Test sending OTP - should return demo mode message
    otp_send_success = tester.test_send_otp(phone_number)
    
    # Test OTP verification with demo code
    otp_verify_success = tester.test_verify_otp(phone_number, otp_code)
    
    # Test media upload and listing creation with media after authentication
    if tester.token:
        print("\n🔍 Testing with authenticated user...")
        
        # Test media upload
        print("\n🔍 Testing Media Upload...")
        test_image_path = '/tmp/test_upload_image.png'
        test_video_path = '/tmp/test_upload_video.mp4'
        
        # Create test files
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        with open(test_video_path, 'wb') as f:
            f.write(b'TEST VIDEO CONTENT')
        
        image_upload_success, _ = tester.test_upload_media(test_image_path, 'image/png')
        video_upload_success, _ = tester.test_upload_media(test_video_path, 'video/mp4')
        
        # Clean up test files
        try:
            os.remove(test_image_path)
            os.remove(test_video_path)
        except:
            pass
        
        # Test listing creation with media
        listing_create_success, _ = tester.test_create_listing_with_media()
        
        # Test S3 storage integration
        s3_storage_success, _ = tester.test_create_listing_with_s3_storage()
        
        # Test regular listing retrieval
        listing_get_success = tester.test_get_listings()
        
        # Test payment order creation and verification
        if tester.listing_id:
            payment_order_success = tester.test_create_payment_order()
            
            if payment_order_success and tester.razorpay_order_id:
                payment_verify_success = tester.test_verify_payment()
                
                # Test WhatsApp broadcast after payment
                if payment_verify_success:
                    broadcast_success = tester.test_whatsapp_broadcast()
                else:
                    print("\n⚠️ Payment verification failed - skipping broadcast test")
                    broadcast_success = False
            else:
                print("\n⚠️ Payment order creation failed - skipping verification")
                payment_verify_success = False
                broadcast_success = False
        else:
            print("\n⚠️ Skipping payment tests - no listing ID available")
            payment_order_success = False
            payment_verify_success = False
            broadcast_success = False
    else:
        print("\n⚠️ Authentication failed - skipping authenticated tests")
        image_upload_success = False
        video_upload_success = False
        listing_create_success = False
        s3_storage_success = False
        listing_get_success = tester.test_get_listings()
        payment_order_success = False
        payment_verify_success = False
        broadcast_success = False
    
    # Check stats again to verify they've been updated
    if payment_verify_success:
        print("\n🔍 Checking if platform stats were updated after payment...")
        updated_stats_success = tester.test_stats()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    # Return success if all critical tests passed
    critical_tests = [
        health_check_success, 
        otp_send_success, 
        otp_verify_success,
        admin_dashboard_success,
        listing_create_success,
        image_upload_success,
        video_upload_success,
        s3_storage_success,  # Added S3 storage test as critical
        payment_order_success,
        payment_verify_success
    ]
    return 0 if all(critical_tests) else 1

if __name__ == "__main__":
    sys.exit(main())