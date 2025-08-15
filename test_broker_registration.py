#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import OnlyLandsAPITester

def main():
    # Get the backend URL from environment variable
    backend_url = "https://agriplot-hub.preview.emergentagent.com"
    
    print(f"Testing OnlyLands Broker Registration Flow at: {backend_url}")
    print("=" * 80)
    
    tester = OnlyLandsAPITester(backend_url)
    
    # CRITICAL TEST: Broker Registration Flow
    print("\n🚨 RUNNING BROKER REGISTRATION FLOW TEST")
    print("This test addresses the specific review request about new phone numbers")
    print("not showing the registration form for brokers")
    print("=" * 80)
    
    broker_registration_success = tester.test_broker_registration_flow()
    
    # Print final results
    print("\n" + "=" * 80)
    print("📊 BROKER REGISTRATION FLOW TEST RESULTS")
    print("=" * 80)
    print(f"🏢 CRITICAL: Broker Registration Flow: {'✅ PASSED' if broker_registration_success else '❌ FAILED'}")
    print(f"📊 Total Tests: {tester.tests_run}, Passed: {tester.tests_passed}")
    print("=" * 80)
    
    # Summary of findings
    print("\n📋 SUMMARY OF FINDINGS:")
    print("=" * 50)
    
    if broker_registration_success:
        print("🎉 SUCCESS: The broker registration flow is working correctly!")
        print("✅ New phone numbers can login as broker successfully")
        print("✅ /api/broker-profile correctly returns 404 for new brokers")
        print("✅ Broker registration works correctly")
        print("✅ After registration, broker profile is accessible")
        print("✅ Broker dashboard works after registration")
        print("✅ Flow is consistent for multiple new phone numbers")
        
        print("\n💡 CONCLUSION:")
        print("• The backend broker registration flow is working correctly")
        print("• If new brokers are not seeing the registration form, the issue is in the frontend")
        print("• Frontend should check /api/broker-profile and show registration form on 404 response")
        print("• The issue is NOT in the backend APIs")
        
        return 0
    else:
        print("❌ FAILURE: Issues found in the broker registration flow!")
        print("❌ Backend broker registration functionality has problems")
        print("❌ This explains why new brokers are not seeing the registration form")
        return 1

if __name__ == "__main__":
    sys.exit(main())