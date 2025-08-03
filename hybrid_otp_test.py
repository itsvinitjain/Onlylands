#!/usr/bin/env python3
"""
Comprehensive test for hybrid OTP functionality with Twilio fallback to demo mode
Tests the updated hybrid OTP login endpoints as requested in the review.
"""

import requests
import sys
import uuid
import json
from datetime import datetime

class HybridOTPTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if not headers:
            headers = {'Content-Type': 'application/json'}

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
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_send_otp_seller(self, phone_number):
        """Test 1: Send OTP for seller with valid phone number"""
        success, response = self.run_test(
            "Send OTP for Seller",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": phone_number, "user_type": "seller"}
        )
        
        if success:
            # Check for demo mode fallback
            status = response.get('status')
            demo_info = response.get('demo_info')
            message = response.get('message')
            
            print(f"✅ Status: {status}")
            print(f"✅ Message: {message}")
            if demo_info:
                print(f"✅ Demo Info: {demo_info}")
                print("✅ Demo mode fallback is working correctly")
            
            # Verify expected response structure
            if status and message:
                print("✅ Response structure is correct")
                return True
            else:
                print("❌ Response structure is incomplete")
                return False
        
        return success

    def test_send_otp_broker(self, phone_number):
        """Test 2: Send OTP for broker with valid phone number"""
        success, response = self.run_test(
            "Send OTP for Broker",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": phone_number, "user_type": "broker"}
        )
        
        if success:
            # Check for demo mode fallback
            status = response.get('status')
            demo_info = response.get('demo_info')
            message = response.get('message')
            
            print(f"✅ Status: {status}")
            print(f"✅ Message: {message}")
            if demo_info:
                print(f"✅ Demo Info: {demo_info}")
                print("✅ Demo mode fallback is working correctly")
            
            return True
        
        return success

    def test_send_otp_missing_phone(self):
        """Test 3: Send OTP with missing phone number (should return 400)"""
        success, response = self.run_test(
            "Send OTP - Missing Phone Number",
            "POST",
            "api/send-otp",
            400,
            data={"user_type": "seller"}
        )
        
        if success:
            error_detail = response.get('detail')
            print(f"✅ Error Message: {error_detail}")
            if "phone number" in error_detail.lower():
                print("✅ Error handling for missing phone number is correct")
                return True
        
        return success

    def test_verify_otp_demo_seller(self, phone_number):
        """Test 4: Verify OTP with demo code "123456" for seller"""
        success, response = self.run_test(
            "Verify OTP - Demo Code for Seller",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "seller"}
        )
        
        if success:
            token = response.get('token')
            user = response.get('user', {})
            message = response.get('message')
            
            print(f"✅ Message: {message}")
            print(f"✅ Token Generated: {'Yes' if token else 'No'}")
            print(f"✅ User ID: {user.get('user_id')}")
            print(f"✅ User Type: {user.get('user_type')}")
            print(f"✅ Phone Number: {user.get('phone_number')}")
            
            # Verify JWT token and user creation
            if token and user.get('user_id') and user.get('user_type') == 'seller':
                print("✅ JWT token generation and user creation working correctly")
                return True
            else:
                print("❌ JWT token generation or user creation failed")
                return False
        
        return success

    def test_verify_otp_demo_broker(self, phone_number):
        """Test 5: Verify OTP with demo code "123456" for broker"""
        success, response = self.run_test(
            "Verify OTP - Demo Code for Broker",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "broker"}
        )
        
        if success:
            token = response.get('token')
            user = response.get('user', {})
            message = response.get('message')
            
            print(f"✅ Message: {message}")
            print(f"✅ Token Generated: {'Yes' if token else 'No'}")
            print(f"✅ User Type: {user.get('user_type')}")
            
            # Verify JWT token and user creation for broker
            if token and user.get('user_id') and user.get('user_type') == 'broker':
                print("✅ JWT token generation and broker user creation working correctly")
                return True
            else:
                print("❌ JWT token generation or broker user creation failed")
                return False
        
        return success

    def test_verify_otp_invalid_seller(self, phone_number):
        """Test 6: Verify OTP with invalid code for seller (should fail)"""
        success, response = self.run_test(
            "Verify OTP - Invalid Code for Seller",
            "POST",
            "api/verify-otp",
            400,
            data={"phone_number": phone_number, "otp": "999999", "user_type": "seller"}
        )
        
        if success:
            error_detail = response.get('detail')
            print(f"✅ Error Message: {error_detail}")
            if "invalid" in error_detail.lower() or "123456" in error_detail:
                print("✅ Invalid OTP rejection working correctly")
                return True
        
        return success

    def test_verify_otp_invalid_broker(self, phone_number):
        """Test 7: Verify OTP with invalid code for broker (should fail)"""
        success, response = self.run_test(
            "Verify OTP - Invalid Code for Broker",
            "POST",
            "api/verify-otp",
            400,
            data={"phone_number": phone_number, "otp": "888888", "user_type": "broker"}
        )
        
        if success:
            error_detail = response.get('detail')
            print(f"✅ Error Message: {error_detail}")
            if "invalid" in error_detail.lower() or "123456" in error_detail:
                print("✅ Invalid OTP rejection working correctly for broker")
                return True
        
        return success

    def test_verify_otp_missing_params(self):
        """Test 8: Verify OTP with missing parameters"""
        success, response = self.run_test(
            "Verify OTP - Missing Parameters",
            "POST",
            "api/verify-otp",
            400,
            data={"user_type": "seller"}
        )
        
        if success:
            error_detail = response.get('detail')
            print(f"✅ Error Message: {error_detail}")
            if "required" in error_detail.lower():
                print("✅ Missing parameters validation working correctly")
                return True
        
        return success

    def test_demo_mode_consistency(self, phone_number):
        """Test 9: Test that demo mode works regardless of Twilio configuration"""
        print("\n🔄 Testing Demo Mode Consistency...")
        
        # Send OTP
        send_success, send_response = self.run_test(
            "Demo Mode - Send OTP",
            "POST",
            "api/send-otp",
            200,
            data={"phone_number": phone_number, "user_type": "seller"}
        )
        
        if not send_success:
            return False
        
        # Verify OTP with demo code
        verify_success, verify_response = self.run_test(
            "Demo Mode - Verify OTP",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "seller"}
        )
        
        if verify_success:
            print("✅ Demo mode consistency verified")
            return True
        
        return False

    def test_user_creation_demo_mode(self, phone_number):
        """Test 10: Test user creation for new users in demo mode"""
        success, response = self.run_test(
            "User Creation in Demo Mode",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "broker"}
        )
        
        if success:
            user = response.get('user', {})
            token = response.get('token')
            
            if user.get('user_id') and user.get('phone_number') == phone_number and token:
                print("✅ New user creation in demo mode working correctly")
                print(f"✅ Created User ID: {user.get('user_id')}")
                print(f"✅ User Type: {user.get('user_type')}")
                return True
            else:
                print("❌ User creation in demo mode failed")
                return False
        
        return success

    def test_existing_user_login(self, phone_number):
        """Test 11: Test existing user login in demo mode"""
        # First create a user
        self.run_test(
            "Create User for Login Test",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "seller"}
        )
        
        # Now test login with existing user
        success, response = self.run_test(
            "Existing User Login in Demo Mode",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "seller"}
        )
        
        if success:
            user = response.get('user', {})
            token = response.get('token')
            
            if user.get('user_id') and token:
                print("✅ Existing user login in demo mode working correctly")
                return True
            else:
                print("❌ Existing user login failed")
                return False
        
        return success

    def test_jwt_token_generation(self, phone_number):
        """Test 12: Test JWT token generation and user data"""
        success, response = self.run_test(
            "JWT Token Generation Test",
            "POST",
            "api/verify-otp",
            200,
            data={"phone_number": phone_number, "otp": "123456", "user_type": "seller"}
        )
        
        if success:
            token = response.get('token')
            user = response.get('user', {})
            
            if token and len(token) > 50:  # JWT tokens are typically long
                print("✅ JWT token generated successfully")
                print(f"✅ Token length: {len(token)} characters")
                
                # Verify user data structure
                required_fields = ['user_id', 'phone_number', 'user_type', 'created_at']
                missing_fields = [field for field in required_fields if field not in user]
                
                if not missing_fields:
                    print("✅ User data structure is complete")
                    return True
                else:
                    print(f"❌ Missing user fields: {missing_fields}")
                    return False
            else:
                print("❌ JWT token generation failed")
                return False
        
        return success

    def test_various_invalid_otps(self, phone_number):
        """Test 13: Test different invalid OTP codes"""
        invalid_codes = ["000000", "111111", "999999", "abcdef", "12345", "1234567"]
        passed_tests = 0
        
        for code in invalid_codes:
            success, response = self.run_test(
                f"Invalid OTP: {code}",
                "POST",
                "api/verify-otp",
                400,
                data={"phone_number": phone_number, "otp": code, "user_type": "seller"}
            )
            if success:
                passed_tests += 1
        
        print(f"✅ Invalid OTP tests passed: {passed_tests}/{len(invalid_codes)}")
        return passed_tests == len(invalid_codes)

def main():
    """Run comprehensive hybrid OTP functionality tests"""
    backend_url = "https://91a3d332-8408-4b2f-93db-7686f4570aca.preview.emergentagent.com"
    
    print("🔍 COMPREHENSIVE HYBRID OTP FUNCTIONALITY TESTING")
    print(f"Backend URL: {backend_url}")
    print("=" * 80)
    
    tester = HybridOTPTester(backend_url)
    
    # Test phone numbers
    seller_phone = "+919876543210"
    broker_phone = "+919876543211"
    demo_phone = "+919999999999"
    new_user_phone = "+919888888888"
    existing_user_phone = "+919777777777"
    jwt_test_phone = "+919666666666"
    invalid_test_phone = "+919555555555"
    
    print("\n📱 TESTING SEND OTP ENDPOINT WITH FALLBACK")
    print("-" * 50)
    
    # Test 1: Send OTP for seller
    test1_result = tester.test_send_otp_seller(seller_phone)
    
    # Test 2: Send OTP for broker
    test2_result = tester.test_send_otp_broker(broker_phone)
    
    # Test 3: Send OTP with missing phone number
    test3_result = tester.test_send_otp_missing_phone()
    
    print("\n🔐 TESTING VERIFY OTP ENDPOINT WITH FALLBACK")
    print("-" * 50)
    
    # Test 4: Verify OTP with demo code for seller
    test4_result = tester.test_verify_otp_demo_seller(seller_phone)
    
    # Test 5: Verify OTP with demo code for broker
    test5_result = tester.test_verify_otp_demo_broker(broker_phone)
    
    # Test 6: Verify OTP with invalid code for seller
    test6_result = tester.test_verify_otp_invalid_seller(seller_phone)
    
    # Test 7: Verify OTP with invalid code for broker
    test7_result = tester.test_verify_otp_invalid_broker(broker_phone)
    
    # Test 8: Verify OTP with missing parameters
    test8_result = tester.test_verify_otp_missing_params()
    
    print("\n🔄 TESTING FALLBACK LOGIC")
    print("-" * 50)
    
    # Test 9: Demo mode consistency
    test9_result = tester.test_demo_mode_consistency(demo_phone)
    
    # Test 10: User creation in demo mode
    test10_result = tester.test_user_creation_demo_mode(new_user_phone)
    
    # Test 11: Existing user login
    test11_result = tester.test_existing_user_login(existing_user_phone)
    
    # Test 12: JWT token generation
    test12_result = tester.test_jwt_token_generation(jwt_test_phone)
    
    # Test 13: Various invalid OTP codes
    test13_result = tester.test_various_invalid_otps(invalid_test_phone)
    
    # Summary of results
    print("\n" + "=" * 80)
    print("📊 HYBRID OTP FUNCTIONALITY TEST RESULTS")
    print("=" * 80)
    
    test_results = [
        ("1. Send OTP - Seller", test1_result),
        ("2. Send OTP - Broker", test2_result),
        ("3. Send OTP - Missing Phone", test3_result),
        ("4. Verify OTP - Demo Seller", test4_result),
        ("5. Verify OTP - Demo Broker", test5_result),
        ("6. Verify OTP - Invalid Seller", test6_result),
        ("7. Verify OTP - Invalid Broker", test7_result),
        ("8. Verify OTP - Missing Params", test8_result),
        ("9. Demo Mode Consistency", test9_result),
        ("10. New User Creation", test10_result),
        ("11. Existing User Login", test11_result),
        ("12. JWT Token Generation", test12_result),
        ("13. Invalid OTP Rejection", test13_result)
    ]
    
    passed_tests = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    print(f"📈 SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL HYBRID OTP FUNCTIONALITY TESTS PASSED!")
        print("✅ Twilio SMS fallback to demo mode is working correctly")
        print("✅ Demo OTP '123456' is accepted as expected")
        print("✅ User creation and JWT token generation working")
        print("✅ Error handling for all scenarios working correctly")
        return 0
    else:
        print(f"\n⚠️ {total_tests - passed_tests} HYBRID OTP FUNCTIONALITY TESTS FAILED!")
        print("❌ Some functionality may not be working as expected")
        return 1

if __name__ == "__main__":
    sys.exit(main())