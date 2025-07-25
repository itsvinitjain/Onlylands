#!/usr/bin/env python3
"""
OTP Login Endpoints Test Suite
Tests the updated OTP login endpoints with demo mode functionality
"""

import requests
import sys
import json

class OTPTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            else:
                response = requests.get(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result = response.json()
                    return success, result
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_response = response.json()
                    print(f"Response: {error_response}")
                    return False, error_response
                except:
                    print(f"Response: {response.text}")
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

def main():
    """Comprehensive test of OTP login endpoints with demo mode functionality"""
    # Get the backend URL from frontend .env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=')[1].strip()
                    break
            else:
                backend_url = "http://localhost:8001"
    except:
        backend_url = "http://localhost:8001"
    
    print(f"Testing OnlyLands OTP Endpoints at: {backend_url}")
    print("=" * 60)
    
    tester = OTPTester(backend_url)
    
    # Test phone numbers
    test_phone = "+919876543210"
    
    print("\n🔍 TESTING OTP LOGIN ENDPOINTS WITH DEMO MODE")
    print("=" * 60)
    
    # 1. Test Send OTP Endpoint - POST /api/send-otp
    print("\n📱 1. TESTING SEND OTP ENDPOINT")
    print("-" * 40)
    
    # Test with valid phone number and user_type "seller"
    print("\n✅ Test: Valid phone number with user_type 'seller'")
    send_otp_seller_success, seller_response = tester.run_test(
        "Send OTP for seller",
        "POST",
        "api/send-otp",
        200,
        {"phone_number": test_phone, "user_type": "seller"}
    )
    if send_otp_seller_success:
        print(f"   Message: {seller_response.get('message')}")
        print(f"   Status: {seller_response.get('status')}")
        if seller_response.get('demo_info'):
            print(f"   Demo Info: {seller_response.get('demo_info')}")
    
    # Test with valid phone number and user_type "broker"
    print("\n✅ Test: Valid phone number with user_type 'broker'")
    send_otp_broker_success, broker_response = tester.run_test(
        "Send OTP for broker",
        "POST",
        "api/send-otp",
        200,
        {"phone_number": test_phone, "user_type": "broker"}
    )
    if send_otp_broker_success:
        print(f"   Message: {broker_response.get('message')}")
        print(f"   Status: {broker_response.get('status')}")
        if broker_response.get('demo_info'):
            print(f"   Demo Info: {broker_response.get('demo_info')}")
    
    # Test with missing phone number (should return 400 error)
    print("\n❌ Test: Missing phone number (should return 400)")
    send_otp_missing_success, missing_response = tester.run_test(
        "Send OTP - Missing Phone Number",
        "POST",
        "api/send-otp",
        400,
        {"user_type": "seller"}
    )
    if send_otp_missing_success:
        print(f"   Error Message: {missing_response.get('detail')}")
    
    # 2. Test Verify OTP Endpoint - POST /api/verify-otp
    print("\n🔐 2. TESTING VERIFY OTP ENDPOINT")
    print("-" * 40)
    
    # Test with valid phone number, demo OTP "123456", and user_type "seller"
    print("\n✅ Test: Valid phone, demo OTP '123456', user_type 'seller'")
    verify_otp_seller_success, verify_seller_response = tester.run_test(
        "Verify OTP for seller",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": test_phone, "otp": "123456", "user_type": "seller"}
    )
    if verify_otp_seller_success:
        print(f"   Message: {verify_seller_response.get('message')}")
        user_data = verify_seller_response.get('user', {})
        print(f"   User ID: {user_data.get('user_id')}")
        print(f"   User Type: {user_data.get('user_type')}")
        print(f"   Phone Number: {user_data.get('phone_number')}")
        print(f"   Token Generated: {'Yes' if verify_seller_response.get('token') else 'No'}")
    
    # Test with valid phone number, demo OTP "123456", and user_type "broker"
    print("\n✅ Test: Valid phone, demo OTP '123456', user_type 'broker'")
    verify_otp_broker_success, verify_broker_response = tester.run_test(
        "Verify OTP for broker",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": "+919876543211", "otp": "123456", "user_type": "broker"}
    )
    if verify_otp_broker_success:
        print(f"   Message: {verify_broker_response.get('message')}")
        user_data = verify_broker_response.get('user', {})
        print(f"   User ID: {user_data.get('user_id')}")
        print(f"   User Type: {user_data.get('user_type')}")
        print(f"   Phone Number: {user_data.get('phone_number')}")
        print(f"   Token Generated: {'Yes' if verify_broker_response.get('token') else 'No'}")
    
    # Test with invalid OTP (should return 400 error)
    print("\n❌ Test: Invalid OTP (should return 400)")
    verify_otp_invalid_success, invalid_response = tester.run_test(
        "Verify OTP - Invalid OTP",
        "POST",
        "api/verify-otp",
        400,
        {"phone_number": test_phone, "otp": "999999", "user_type": "seller"}
    )
    if verify_otp_invalid_success:
        print(f"   Error Message: {invalid_response.get('detail')}")
    
    # Test with missing parameters (should return 400 error)
    print("\n❌ Test: Missing parameters (should return 400)")
    verify_otp_missing_success, missing_params_response = tester.run_test(
        "Verify OTP - Missing Parameters",
        "POST",
        "api/verify-otp",
        400,
        {"user_type": "seller"}
    )
    if verify_otp_missing_success:
        print(f"   Error Message: {missing_params_response.get('detail')}")
    
    # 3. Test User Creation Flow
    print("\n👤 3. TESTING USER CREATION FLOW")
    print("-" * 40)
    
    # Test that new users are created with correct user_type
    new_phone = "+919876543212"
    print(f"\n✅ Test: New user creation with seller type")
    new_seller_success, new_seller_response = tester.run_test(
        "Create new seller user",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": new_phone, "otp": "123456", "user_type": "seller"}
    )
    if new_seller_success:
        user_data = new_seller_response.get('user', {})
        print(f"   New User Created: {user_data.get('user_id')}")
        print(f"   User Type: {user_data.get('user_type')}")
    
    new_phone_broker = "+919876543213"
    print(f"\n✅ Test: New user creation with broker type")
    new_broker_success, new_broker_response = tester.run_test(
        "Create new broker user",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": new_phone_broker, "otp": "123456", "user_type": "broker"}
    )
    if new_broker_success:
        user_data = new_broker_response.get('user', {})
        print(f"   New User Created: {user_data.get('user_id')}")
        print(f"   User Type: {user_data.get('user_type')}")
    
    # Test that existing users can login again
    print(f"\n✅ Test: Existing user login")
    existing_user_success, existing_response = tester.run_test(
        "Existing user login",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": test_phone, "otp": "123456", "user_type": "seller"}
    )
    if existing_user_success:
        user_data = existing_response.get('user', {})
        print(f"   Existing User Login: {user_data.get('user_id')}")
        print(f"   User Type: {user_data.get('user_type')}")
    
    # 4. Test Demo Mode Functionality
    print("\n🎭 4. TESTING DEMO MODE FUNCTIONALITY")
    print("-" * 40)
    
    # Verify send-otp returns demo_mode status when Twilio not configured
    print("\n✅ Test: Demo mode status in send-otp response")
    demo_phone = "+919876543214"
    demo_send_success, demo_send_response = tester.run_test(
        "Demo mode send OTP",
        "POST",
        "api/send-otp",
        200,
        {"phone_number": demo_phone, "user_type": "seller"}
    )
    if demo_send_success:
        print(f"   Demo Mode Status: {demo_send_response.get('status')}")
        print(f"   Demo Info: {demo_send_response.get('demo_info')}")
    
    # Verify verify-otp accepts "123456" as valid OTP in demo mode
    print("\n✅ Test: Demo OTP '123456' acceptance")
    demo_verify_success, demo_verify_response = tester.run_test(
        "Demo OTP verification",
        "POST",
        "api/verify-otp",
        200,
        {"phone_number": demo_phone, "otp": "123456", "user_type": "seller"}
    )
    if demo_verify_success:
        print(f"   Demo OTP Accepted: Yes")
        print(f"   Token Generated: {'Yes' if demo_verify_response.get('token') else 'No'}")
    
    # Test error handling for invalid demo OTP
    print("\n❌ Test: Invalid demo OTP rejection")
    demo_invalid_success, demo_invalid_response = tester.run_test(
        "Invalid demo OTP",
        "POST",
        "api/verify-otp",
        400,
        {"phone_number": demo_phone, "otp": "654321", "user_type": "seller"}
    )
    if demo_invalid_success:
        print(f"   Error Message: {demo_invalid_response.get('detail')}")
    
    # Print comprehensive results
    print("\n" + "=" * 60)
    print("📊 OTP ENDPOINTS TEST RESULTS")
    print("=" * 60)
    
    print(f"\n📱 SEND OTP TESTS:")
    print(f"   ✅ Valid phone + seller type: {'PASS' if send_otp_seller_success else 'FAIL'}")
    print(f"   ✅ Valid phone + broker type: {'PASS' if send_otp_broker_success else 'FAIL'}")
    print(f"   ❌ Missing phone number: {'PASS' if send_otp_missing_success else 'FAIL'}")
    
    print(f"\n🔐 VERIFY OTP TESTS:")
    print(f"   ✅ Valid demo OTP + seller: {'PASS' if verify_otp_seller_success else 'FAIL'}")
    print(f"   ✅ Valid demo OTP + broker: {'PASS' if verify_otp_broker_success else 'FAIL'}")
    print(f"   ❌ Invalid OTP: {'PASS' if verify_otp_invalid_success else 'FAIL'}")
    print(f"   ❌ Missing parameters: {'PASS' if verify_otp_missing_success else 'FAIL'}")
    
    print(f"\n👤 USER CREATION TESTS:")
    print(f"   ✅ New seller creation: {'PASS' if new_seller_success else 'FAIL'}")
    print(f"   ✅ New broker creation: {'PASS' if new_broker_success else 'FAIL'}")
    print(f"   ✅ Existing user login: {'PASS' if existing_user_success else 'FAIL'}")
    
    print(f"\n🎭 DEMO MODE TESTS:")
    print(f"   ✅ Demo mode status: {'PASS' if demo_send_success else 'FAIL'}")
    print(f"   ✅ Demo OTP acceptance: {'PASS' if demo_verify_success else 'FAIL'}")
    print(f"   ❌ Invalid demo OTP: {'PASS' if demo_invalid_success else 'FAIL'}")
    
    print(f"\n📊 OVERALL: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Determine if all critical tests passed
    critical_tests = [
        send_otp_seller_success,
        send_otp_broker_success,
        send_otp_missing_success,
        verify_otp_seller_success,
        verify_otp_broker_success,
        verify_otp_invalid_success,
        verify_otp_missing_success,
        new_seller_success,
        new_broker_success,
        existing_user_success,
        demo_send_success,
        demo_verify_success,
        demo_invalid_success
    ]
    
    all_passed = all(critical_tests)
    print(f"\n🎯 FINAL RESULT: {'ALL TESTS PASSED ✅' if all_passed else 'SOME TESTS FAILED ❌'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())