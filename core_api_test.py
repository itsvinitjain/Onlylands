#!/usr/bin/env python3

import requests
import sys
import uuid
import time
import base64
import os
import jwt
from datetime import datetime, timedelta

class CoreAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.listing_id = None
        self.broker_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if not headers:
            headers = {}
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            # Handle both single status code and list of acceptable status codes
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                expected_str = str(expected_status) if not isinstance(expected_status, list) else f"one of {expected_status}"
                print(f"❌ Failed - Expected {expected_str}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_test_jwt_token(self):
        """Create a test JWT token for authentication"""
        try:
            JWT_SECRET = 'your-secure-jwt-secret-key-here-change-this-in-production'
            test_user_id = str(uuid.uuid4())
            test_phone = "+919876543210"
            
            test_payload = {
                "user_id": test_user_id,
                "phone_number": test_phone,
                "user_type": "seller",
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            
            test_token = jwt.encode(test_payload, JWT_SECRET, algorithm="HS256")
            self.token = test_token
            self.user_id = test_user_id
            
            print(f"✅ Test JWT token created successfully")
            print(f"✅ User ID: {test_user_id}")
            return True
            
        except Exception as e:
            print(f"❌ FAILURE: Could not create test JWT token: {e}")
            return False

    def test_post_land_api(self):
        """Test POST /api/post-land endpoint"""
        print("\n" + "="*80)
        print("🏞️ CRITICAL TEST: POST LAND API (/api/post-land)")
        print("="*80)
        
        # Test 1: Without authentication (should fail)
        print("\n🔒 TEST 1: POST LAND WITHOUT AUTHENTICATION")
        print("-" * 50)
        
        # Create test files
        test_image_path = '/tmp/test_land_image.jpg'
        test_video_path = '/tmp/test_land_video.mp4'
        
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        with open(test_video_path, 'wb') as f:
            f.write(b'TEST VIDEO CONTENT FOR LAND LISTING')
        
        form_data = {
            'title': 'Beautiful Agricultural Land in Maharashtra',
            'area': '5 Acres',
            'price': '50 Lakhs',
            'description': 'Prime agricultural land with water facility and road connectivity.',
            'latitude': '18.6414',
            'longitude': '72.9897'
        }
        
        files = [
            ('photos', ('land_photo1.jpg', open(test_image_path, 'rb'), 'image/jpeg')),
            ('videos', ('land_video1.mp4', open(test_video_path, 'rb'), 'video/mp4'))
        ]
        
        try:
            success, response = self.run_test(
                "POST Land without Authentication",
                "POST",
                "api/post-land",
                [401, 403],
                data=form_data,
                files=files,
                headers={}
            )
            
            if success:
                print("✅ PASS: Authentication required")
                auth_required = True
            else:
                print("❌ FAILURE: POST /api/post-land doesn't require authentication!")
                auth_required = False
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()
            try:
                os.remove(test_image_path)
                os.remove(test_video_path)
            except:
                pass
        
        if not auth_required:
            return False
        
        # Test 2: With authentication
        print("\n🔐 TEST 2: POST LAND WITH AUTHENTICATION")
        print("-" * 50)
        
        if not self.create_test_jwt_token():
            return False
        
        # Create new test files
        test_image_path = '/tmp/test_land_image_auth.jpg'
        test_video_path = '/tmp/test_land_video_auth.mp4'
        
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        with open(test_video_path, 'wb') as f:
            f.write(b'TEST VIDEO CONTENT FOR AUTHENTICATED LAND LISTING')
        
        form_data = {
            'title': f'Premium Agricultural Land {uuid.uuid4().hex[:8]}',
            'area': '10 Acres',
            'price': '75 Lakhs',
            'description': 'Excellent agricultural land with bore well, electricity connection, and road access.',
            'latitude': '18.6414',
            'longitude': '72.9897'
        }
        
        files = [
            ('photos', ('land_main_photo.jpg', open(test_image_path, 'rb'), 'image/jpeg')),
            ('videos', ('land_walkthrough.mp4', open(test_video_path, 'rb'), 'video/mp4'))
        ]
        
        try:
            success, response = self.run_test(
                "POST Land with Authentication",
                "POST",
                "api/post-land",
                200,
                data=form_data,
                files=files
            )
            
            if success:
                self.listing_id = response.get('listing_id')
                print(f"✅ Listing ID: {self.listing_id}")
                print(f"✅ Message: {response.get('message')}")
                post_land_success = True
            else:
                print("❌ FAILURE: Could not create land listing")
                post_land_success = False
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()
            try:
                os.remove(test_image_path)
                os.remove(test_video_path)
            except:
                pass
        
        print("\n" + "="*80)
        if post_land_success:
            print("🎉 POST LAND API: WORKING!")
        else:
            print("❌ POST LAND API: BROKEN!")
        print("="*80)
        
        return post_land_success

    def test_my_listings_api(self):
        """Test GET /api/my-listings endpoint"""
        print("\n" + "="*80)
        print("📋 CRITICAL TEST: MY LISTINGS API (/api/my-listings)")
        print("="*80)
        
        # Test 1: Without authentication (should fail)
        print("\n🔒 TEST 1: MY LISTINGS WITHOUT AUTHENTICATION")
        print("-" * 50)
        
        success, response = self.run_test(
            "My Listings without Authentication",
            "GET",
            "api/my-listings",
            [401, 403],
            headers={}
        )
        
        if success:
            print("✅ PASS: Authentication required")
            auth_required = True
        else:
            print("❌ FAILURE: GET /api/my-listings doesn't require authentication!")
            auth_required = False
        
        if not auth_required:
            return False
        
        # Test 2: With authentication
        print("\n📋 TEST 2: MY LISTINGS WITH AUTHENTICATION")
        print("-" * 50)
        
        if not self.token and not self.create_test_jwt_token():
            return False
        
        success, response = self.run_test(
            "My Listings with Authentication",
            "GET",
            "api/my-listings",
            200
        )
        
        if success:
            listings = response.get('listings', [])
            print(f"✅ Total listings: {len(listings)}")
            
            if 'listings' in response and isinstance(listings, list):
                print("✅ Response structure is correct")
                my_listings_success = True
            else:
                print("❌ Response structure is incorrect")
                my_listings_success = False
        else:
            print("❌ FAILURE: Could not retrieve my listings")
            my_listings_success = False
        
        print("\n" + "="*80)
        if my_listings_success:
            print("🎉 MY LISTINGS API: WORKING!")
        else:
            print("❌ MY LISTINGS API: BROKEN!")
        print("="*80)
        
        return my_listings_success

    def test_broker_signup_api(self):
        """Test POST /api/broker-signup endpoint"""
        print("\n" + "="*80)
        print("🏢 CRITICAL TEST: BROKER SIGNUP API (/api/broker-signup)")
        print("="*80)
        
        # Test 1: Valid broker signup
        print("\n✅ TEST 1: BROKER SIGNUP WITH VALID DATA")
        print("-" * 50)
        
        unique_id = uuid.uuid4().hex[:8]
        broker_data = {
            "name": f"Rajesh Kumar {unique_id}",
            "agency": f"Kumar Real Estate Agency {unique_id}",
            "phone_number": f"+9198765{unique_id[:5]}",
            "email": f"rajesh.kumar.{unique_id}@example.com"
        }
        
        print(f"📋 Broker Data: {broker_data}")
        
        success, response = self.run_test(
            "Broker Signup with Valid Data",
            "POST",
            "api/broker-signup",
            200,
            data=broker_data,
            headers={}  # No authentication required
        )
        
        if success:
            if 'message' in response and 'broker_id' in response:
                self.broker_id = response.get('broker_id')
                print(f"✅ Broker ID: {self.broker_id}")
                print(f"✅ Message: {response.get('message')}")
                print("✅ Response structure is correct")
                broker_signup_success = True
            else:
                print("❌ Response structure is incorrect")
                broker_signup_success = False
        else:
            print("❌ FAILURE: Broker registration failed")
            broker_signup_success = False
        
        # Test 2: Missing required fields
        print("\n⚠️ TEST 2: BROKER SIGNUP WITH MISSING FIELDS")
        print("-" * 50)
        
        incomplete_data = {
            "agency": "Test Agency",
            "phone_number": f"+9198765{uuid.uuid4().hex[:5]}",
            "email": f"test.{uuid.uuid4().hex[:8]}@example.com"
            # Missing 'name'
        }
        
        success, response = self.run_test(
            "Broker Signup - Missing Name",
            "POST",
            "api/broker-signup",
            [400, 422],
            data=incomplete_data,
            headers={}
        )
        
        if success:
            print("✅ PASS: Missing field validation working")
        else:
            print("❌ FAILURE: Missing field validation not working")
        
        print("\n" + "="*80)
        if broker_signup_success:
            print("🎉 BROKER SIGNUP API: WORKING!")
        else:
            print("❌ BROKER SIGNUP API: BROKEN!")
        print("="*80)
        
        return broker_signup_success

    def test_core_apis(self):
        """Test all three core APIs"""
        print("\n" + "="*100)
        print("🚨 COMPREHENSIVE TEST: CORE USER-REPORTED BROKEN APIs")
        print("Testing the three specific APIs that users report as not working:")
        print("1. POST /api/post-land (post your land)")
        print("2. GET /api/my-listings (my listings)")
        print("3. POST /api/broker-signup (register as broker)")
        print("="*100)
        
        results = {
            'post_land': self.test_post_land_api(),
            'my_listings': self.test_my_listings_api(),
            'broker_signup': self.test_broker_signup_api()
        }
        
        # Final Results
        print("\n" + "="*100)
        print("📊 FINAL RESULTS: CORE USER-REPORTED APIs")
        print("="*100)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        print(f"🏞️ POST /api/post-land (post your land): {'✅ WORKING' if results['post_land'] else '❌ BROKEN'}")
        print(f"📋 GET /api/my-listings (my listings): {'✅ WORKING' if results['my_listings'] else '❌ BROKEN'}")
        print(f"🏢 POST /api/broker-signup (register as broker): {'✅ WORKING' if results['broker_signup'] else '❌ BROKEN'}")
        
        print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} APIs working")
        print(f"📊 Total Tests: {self.tests_run}, Passed: {self.tests_passed}")
        
        if passed_tests == total_tests:
            print("🎉 SUCCESS: All core user-reported APIs are working correctly!")
        elif passed_tests > 0:
            print("⚠️ PARTIAL SUCCESS: Some APIs are working, but issues found")
        else:
            print("❌ CRITICAL FAILURE: All core user-reported APIs are broken!")
        
        print("="*100)
        
        return results

def main():
    backend_url = "https://547a6392-129c-42e0-badb-1a283db0eb37.preview.emergentagent.com"
    
    print(f"Testing OnlyLands Core APIs at: {backend_url}")
    print("=" * 50)
    
    tester = CoreAPITester(backend_url)
    results = tester.test_core_apis()
    
    # Return appropriate exit code
    if all(results.values()):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())