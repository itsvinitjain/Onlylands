#!/usr/bin/env python3
"""
Twilio OTP Integration Test
Tests the actual Twilio integration for OTP login endpoints
"""

import requests
import os
import sys
import time
from datetime import datetime

class TwilioOTPTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "response": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"\n{status} - {test_name}")
        print(f"Message: {message}")
        if response_data:
            print(f"Response: {response_data}")
        return success

    def test_environment_variables(self):
        """Test that Twilio environment variables are loaded"""
        print("\n🔍 Testing Twilio Environment Variables...")
        
        # Check if environment variables are set in backend/.env
        env_file_path = "/app/backend/.env"
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            required_vars = [
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN', 
                'TWILIO_VERIFY_SERVICE_SID'
            ]
            
            missing_vars = []
            found_vars = {}
            
            for var in required_vars:
                if f"{var}=" in env_content:
                    # Extract the value
                    for line in env_content.split('\n'):
                        if line.startswith(f"{var}="):
                            value = line.split('=', 1)[1].strip()
                            found_vars[var] = value
                            if not value:
                                missing_vars.append(f"{var} (empty)")
                            break
                else:
                    missing_vars.append(f"{var} (not found)")
            
            if missing_vars:
                return self.log_test(
                    "Environment Variables Check",
                    False,
                    f"Missing or empty variables: {', '.join(missing_vars)}",
                    found_vars
                )
            else:
                return self.log_test(
                    "Environment Variables Check", 
                    True,
                    "All Twilio environment variables are present and configured",
                    {k: f"{v[:10]}..." if len(v) > 10 else v for k, v in found_vars.items()}
                )
                
        except Exception as e:
            return self.log_test(
                "Environment Variables Check",
                False,
                f"Error reading .env file: {str(e)}"
            )

    def test_send_otp_seller(self):
        """Test send OTP endpoint for seller with actual Twilio"""
        print("\n🔍 Testing Send OTP for Seller (Actual Twilio)...")
        
        url = f"{self.base_url}/api/send-otp"
        data = {
            "phone_number": "+917021758061",  # Test phone number
            "user_type": "seller"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if this is demo mode or actual Twilio
                if response_data.get('demo_mode'):
                    return self.log_test(
                        "Send OTP - Seller (Actual Twilio)",
                        False,
                        "API returned demo mode instead of actual Twilio integration",
                        response_data
                    )
                
                # Check for Twilio-specific response fields
                if 'status' in response_data and response_data.get('message') == 'OTP sent successfully':
                    return self.log_test(
                        "Send OTP - Seller (Actual Twilio)",
                        True,
                        f"OTP sent successfully via Twilio. Status: {response_data.get('status')}",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Seller (Actual Twilio)",
                        False,
                        "Unexpected response format from Twilio",
                        response_data
                    )
                    
            elif response.status_code == 500:
                response_data = response.json()
                if "Twilio OTP service not configured" in response_data.get('detail', ''):
                    return self.log_test(
                        "Send OTP - Seller (Actual Twilio)",
                        False,
                        "Twilio service is not configured - credentials may be invalid or missing",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Seller (Actual Twilio)",
                        False,
                        f"Server error: {response_data.get('detail', 'Unknown error')}",
                        response_data
                    )
            else:
                return self.log_test(
                    "Send OTP - Seller (Actual Twilio)",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Send OTP - Seller (Actual Twilio)",
                False,
                f"Request failed: {str(e)}"
            )

    def test_send_otp_broker(self):
        """Test send OTP endpoint for broker with actual Twilio"""
        print("\n🔍 Testing Send OTP for Broker (Actual Twilio)...")
        
        url = f"{self.base_url}/api/send-otp"
        data = {
            "phone_number": "+917021758061",  # Test phone number
            "user_type": "broker"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if this is demo mode or actual Twilio
                if response_data.get('demo_mode'):
                    return self.log_test(
                        "Send OTP - Broker (Actual Twilio)",
                        False,
                        "API returned demo mode instead of actual Twilio integration",
                        response_data
                    )
                
                # Check for Twilio-specific response fields
                if 'status' in response_data and response_data.get('message') == 'OTP sent successfully':
                    return self.log_test(
                        "Send OTP - Broker (Actual Twilio)",
                        True,
                        f"OTP sent successfully via Twilio. Status: {response_data.get('status')}",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Broker (Actual Twilio)",
                        False,
                        "Unexpected response format from Twilio",
                        response_data
                    )
                    
            elif response.status_code == 500:
                response_data = response.json()
                if "Twilio OTP service not configured" in response_data.get('detail', ''):
                    return self.log_test(
                        "Send OTP - Broker (Actual Twilio)",
                        False,
                        "Twilio service is not configured - credentials may be invalid or missing",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Broker (Actual Twilio)",
                        False,
                        f"Server error: {response_data.get('detail', 'Unknown error')}",
                        response_data
                    )
            else:
                return self.log_test(
                    "Send OTP - Broker (Actual Twilio)",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Send OTP - Broker (Actual Twilio)",
                False,
                f"Request failed: {str(e)}"
            )

    def test_send_otp_invalid_phone(self):
        """Test send OTP with invalid phone number format"""
        print("\n🔍 Testing Send OTP with Invalid Phone Number...")
        
        url = f"{self.base_url}/api/send-otp"
        data = {
            "phone_number": "invalid-phone",  # Invalid format
            "user_type": "seller"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 400:
                return self.log_test(
                    "Send OTP - Invalid Phone Number",
                    True,
                    "Correctly rejected invalid phone number format",
                    response.json()
                )
            elif response.status_code == 500:
                response_data = response.json()
                # Twilio might reject invalid phone numbers with 500 error
                if "Failed to send OTP" in response_data.get('detail', ''):
                    return self.log_test(
                        "Send OTP - Invalid Phone Number",
                        True,
                        "Twilio correctly rejected invalid phone number",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Invalid Phone Number",
                        False,
                        f"Unexpected server error: {response_data.get('detail')}",
                        response_data
                    )
            else:
                return self.log_test(
                    "Send OTP - Invalid Phone Number",
                    False,
                    f"Expected 400 or 500, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Send OTP - Invalid Phone Number",
                False,
                f"Request failed: {str(e)}"
            )

    def test_send_otp_missing_phone(self):
        """Test send OTP with missing phone number"""
        print("\n🔍 Testing Send OTP with Missing Phone Number...")
        
        url = f"{self.base_url}/api/send-otp"
        data = {
            "user_type": "seller"
            # Missing phone_number
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 400:
                response_data = response.json()
                if "Phone number is required" in response_data.get('detail', ''):
                    return self.log_test(
                        "Send OTP - Missing Phone Number",
                        True,
                        "Correctly rejected missing phone number",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Send OTP - Missing Phone Number",
                        False,
                        f"Unexpected error message: {response_data.get('detail')}",
                        response_data
                    )
            else:
                return self.log_test(
                    "Send OTP - Missing Phone Number",
                    False,
                    f"Expected 400, got {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Send OTP - Missing Phone Number",
                False,
                f"Request failed: {str(e)}"
            )

    def test_verify_otp_actual_twilio(self):
        """Test verify OTP endpoint with actual Twilio (will fail without real OTP)"""
        print("\n🔍 Testing Verify OTP with Actual Twilio...")
        
        url = f"{self.base_url}/api/verify-otp"
        data = {
            "phone_number": "+917021758061",
            "otp": "123456",  # This will fail with actual Twilio
            "user_type": "seller"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 400:
                response_data = response.json()
                if "Invalid OTP" in response_data.get('detail', ''):
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        True,
                        "Twilio correctly rejected invalid OTP (expected behavior)",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        False,
                        f"Unexpected error message: {response_data.get('detail')}",
                        response_data
                    )
            elif response.status_code == 500:
                response_data = response.json()
                if "Twilio OTP service not configured" in response_data.get('detail', ''):
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        False,
                        "Twilio service is not configured",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        False,
                        f"Server error: {response_data.get('detail')}",
                        response_data
                    )
            elif response.status_code == 200:
                response_data = response.json()
                if response_data.get('demo_mode'):
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        False,
                        "API returned demo mode instead of actual Twilio integration",
                        response_data
                    )
                else:
                    return self.log_test(
                        "Verify OTP - Actual Twilio",
                        False,
                        "Unexpected success - OTP should have been invalid",
                        response_data
                    )
            else:
                return self.log_test(
                    "Verify OTP - Actual Twilio",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Verify OTP - Actual Twilio",
                False,
                f"Request failed: {str(e)}"
            )

    def test_twilio_client_initialization(self):
        """Test if Twilio client is properly initialized by checking API root"""
        print("\n🔍 Testing Twilio Client Initialization...")
        
        url = f"{self.base_url}/api/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return self.log_test(
                    "Twilio Client Initialization",
                    True,
                    "API is running - Twilio client should be initialized if credentials are valid",
                    response.json()
                )
            else:
                return self.log_test(
                    "Twilio Client Initialization",
                    False,
                    f"API not responding properly: {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            return self.log_test(
                "Twilio Client Initialization",
                False,
                f"API request failed: {str(e)}"
            )

    def run_all_tests(self):
        """Run all Twilio OTP tests"""
        print("🚀 Starting Twilio OTP Integration Tests")
        print("=" * 60)
        
        # Test environment variables
        self.test_environment_variables()
        
        # Test Twilio client initialization
        self.test_twilio_client_initialization()
        
        # Test send OTP endpoints
        self.test_send_otp_seller()
        self.test_send_otp_broker()
        
        # Test error handling
        self.test_send_otp_invalid_phone()
        self.test_send_otp_missing_phone()
        
        # Test verify OTP (will fail with actual Twilio as expected)
        self.test_verify_otp_actual_twilio()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TWILIO OTP TESTS SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            print(f"   {result['message']}")
        
        return self.tests_passed, self.tests_run, self.test_results

def main():
    # Use the backend URL from frontend/.env
    backend_url = "https://547a6392-129c-42e0-badb-1a283db0eb37.preview.emergentagent.com"
    
    print(f"Testing Twilio OTP Integration at: {backend_url}")
    
    tester = TwilioOTPTester(backend_url)
    passed, total, results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())