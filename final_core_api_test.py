#!/usr/bin/env python3

import requests
import sys
import uuid
import base64
import os
import jwt
from datetime import datetime, timedelta

class FinalCoreAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.listing_id = None
        self.broker_id = None

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
            return True
            
        except Exception as e:
            print(f"❌ FAILURE: Could not create test JWT token: {e}")
            return False

    def test_post_land_api(self):
        """Test POST /api/post-land endpoint"""
        print("\n" + "="*80)
        print("🏞️ TESTING: POST LAND API (/api/post-land)")
        print("="*80)
        
        # Test without authentication
        print("\n🔒 Testing without authentication...")
        test_image_path = '/tmp/test_land_image.jpg'
        
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        form_data = {
            'title': 'Test Land',
            'area': '5 Acres',
            'price': '50 Lakhs',
            'description': 'Test description',
            'latitude': '18.6414',
            'longitude': '72.9897'
        }
        
        files = [('photos', ('test.jpg', open(test_image_path, 'rb'), 'image/jpeg'))]
        
        try:
            response = requests.post(f"{self.base_url}/api/post-land", data=form_data, files=files)
            
            if response.status_code in [401, 403]:
                print("✅ PASS: Authentication required")
                auth_required = True
            else:
                print(f"❌ FAILURE: Expected 401/403, got {response.status_code}")
                auth_required = False
        finally:
            files[0][1][1].close()
            os.remove(test_image_path)
        
        if not auth_required:
            return False
        
        # Test with authentication
        print("\n🔐 Testing with authentication...")
        if not self.create_test_jwt_token():
            return False
        
        test_image_path = '/tmp/test_land_image_auth.jpg'
        with open(test_image_path, 'wb') as f:
            f.write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='))
        
        form_data = {
            'title': f'Test Land {uuid.uuid4().hex[:8]}',
            'area': '10 Acres',
            'price': '75 Lakhs',
            'description': 'Test land with authentication',
            'latitude': '18.6414',
            'longitude': '72.9897'
        }
        
        files = [('photos', ('test_auth.jpg', open(test_image_path, 'rb'), 'image/jpeg'))]
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.post(f"{self.base_url}/api/post-land", data=form_data, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.listing_id = result.get('listing_id')
                print(f"✅ SUCCESS: Land listing created")
                print(f"✅ Listing ID: {self.listing_id}")
                return True
            else:
                print(f"❌ FAILURE: Expected 200, got {response.status_code}")
                try:
                    print(f"Error: {response.json()}")
                except:
                    print(f"Error: {response.text}")
                return False
        finally:
            files[0][1][1].close()
            os.remove(test_image_path)

    def test_my_listings_api(self):
        """Test GET /api/my-listings endpoint"""
        print("\n" + "="*80)
        print("📋 TESTING: MY LISTINGS API (/api/my-listings)")
        print("="*80)
        
        # Test without authentication
        print("\n🔒 Testing without authentication...")
        response = requests.get(f"{self.base_url}/api/my-listings")
        
        if response.status_code in [401, 403]:
            print("✅ PASS: Authentication required")
            auth_required = True
        else:
            print(f"❌ FAILURE: Expected 401/403, got {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text}")
            auth_required = False
        
        if not auth_required:
            return False
        
        # Test with authentication
        print("\n📋 Testing with authentication...")
        if not self.token and not self.create_test_jwt_token():
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{self.base_url}/api/my-listings", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'listings' in result and isinstance(result['listings'], list):
                print(f"✅ SUCCESS: My listings retrieved")
                print(f"✅ Total listings: {len(result['listings'])}")
                return True
            else:
                print("❌ FAILURE: Invalid response structure")
                return False
        else:
            print(f"❌ FAILURE: Expected 200, got {response.status_code}")
            try:
                print(f"Error: {response.json()}")
            except:
                print(f"Error: {response.text}")
            return False

    def test_broker_signup_api(self):
        """Test POST /api/broker-signup endpoint"""
        print("\n" + "="*80)
        print("🏢 TESTING: BROKER SIGNUP API (/api/broker-signup)")
        print("="*80)
        
        # Test valid broker signup
        print("\n✅ Testing valid broker signup...")
        unique_id = uuid.uuid4().hex[:8]
        broker_data = {
            "name": f"Test Broker {unique_id}",
            "agency": f"Test Agency {unique_id}",
            "phone_number": f"+9198765{unique_id[:5]}",
            "email": f"test.broker.{unique_id}@example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/broker-signup", json=broker_data)
        
        if response.status_code == 200:
            result = response.json()
            if 'message' in result and 'broker_id' in result:
                self.broker_id = result.get('broker_id')
                print(f"✅ SUCCESS: Broker registered")
                print(f"✅ Broker ID: {self.broker_id}")
                return True
            else:
                print("❌ FAILURE: Invalid response structure")
                return False
        else:
            print(f"❌ FAILURE: Expected 200, got {response.status_code}")
            try:
                print(f"Error: {response.json()}")
            except:
                print(f"Error: {response.text}")
            return False

    def run_all_tests(self):
        """Run all core API tests"""
        print("🚨 FINAL COMPREHENSIVE TEST: CORE USER-REPORTED APIs")
        print("="*80)
        
        results = {
            'post_land': self.test_post_land_api(),
            'my_listings': self.test_my_listings_api(),
            'broker_signup': self.test_broker_signup_api()
        }
        
        # Final Results
        print("\n" + "="*80)
        print("📊 FINAL TEST RESULTS")
        print("="*80)
        
        print(f"🏞️ POST /api/post-land: {'✅ WORKING' if results['post_land'] else '❌ BROKEN'}")
        print(f"📋 GET /api/my-listings: {'✅ WORKING' if results['my_listings'] else '❌ BROKEN'}")
        print(f"🏢 POST /api/broker-signup: {'✅ WORKING' if results['broker_signup'] else '❌ BROKEN'}")
        
        working_count = sum(results.values())
        total_count = len(results)
        
        print(f"\n📊 SUMMARY: {working_count}/{total_count} APIs working correctly")
        
        if working_count == total_count:
            print("🎉 ALL CORE APIs ARE WORKING!")
            return True
        else:
            print("❌ SOME CORE APIs HAVE ISSUES!")
            return False

def main():
    backend_url = "https://agriplot-hub.preview.emergentagent.com"
    
    tester = FinalCoreAPITester(backend_url)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())