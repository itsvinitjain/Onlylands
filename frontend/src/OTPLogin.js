import React, { useState } from 'react';
import axios from 'axios';

const OTPLogin = ({ setToken, setCurrentView, userType = 'seller' }) => {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [demoInfo, setDemoInfo] = useState('');
  const [phoneError, setPhoneError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const validatePhone = (phoneNumber) => {
    const phoneRegex = /^\d{10}$/;
    return phoneRegex.test(phoneNumber);
  };

  const handlePhoneChange = (e) => {
    const value = e.target.value.replace(/\D/g, ''); // Remove non-digits
    if (value.length <= 10) {
      setPhone(value);
      setPhoneError('');
      setError(''); // Clear general errors when typing
    }
  };

  const changePhoneNumber = () => {
    setIsOtpSent(false);
    setOtp('');
    setError(''); // Clear OTP error when changing phone number
    setDemoInfo('');
    setPhoneError('');
  };

  const sendOTP = async () => {
    // Validate phone number
    if (!validatePhone(phone)) {
      setPhoneError('Please enter a valid 10-digit phone number');
      return;
    }

    setLoading(true);
    setError('');
    setPhoneError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/send-otp`, {
        phone_number: phone,
        user_type: userType
      });
      
      if (response.data.message) {
        setIsOtpSent(true);
        setError('');
        
        // Show appropriate message based on OTP mode
        if (response.data.status === 'demo_mode') {
          setDemoInfo(response.data.demo_info || 'Use OTP 123456 for testing.');
        } else {
          setDemoInfo(''); // Clear demo info for genuine OTP
        }
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Failed to send OTP. Please check your phone number and try again.';
      console.log('OTP Error:', errorDetail);
      setError(errorDetail);
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/verify-otp`, {
        phone_number: phone,
        otp: otp,
        user_type: userType
      });
      
      if (response.data.token) {
        setToken(response.data.token);
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // For brokers, redirect directly to broker dashboard for registration check
        if (userType === 'broker') {
          setCurrentView('broker-dashboard');
        } else {
          setCurrentView('home');
        }
      } else {
        setError('OTP verification failed');
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              {userType === 'seller' ? '🏞️ Seller Login' : '🤝 Broker Login'}
            </h2>
            <p className="text-gray-600">
              {userType === 'seller' ? 'Login to post and manage your land listings' : 'Login to browse and connect with land owners'}
            </p>
          </div>
          
          {!isOtpSent ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number <span className="text-red-500">*</span>
                </label>
                <div className="flex">
                  <span className="inline-flex items-center px-3 text-sm text-gray-900 bg-gray-200 border border-r-0 border-gray-300 rounded-l-md">
                    +91
                  </span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={handlePhoneChange}
                    className={`flex-1 px-3 py-2 border-l-0 border border-gray-300 rounded-r-lg focus:outline-none focus:border-blue-500 ${phoneError ? 'border-red-500' : ''}`}
                    placeholder="Enter 10-digit mobile number"
                    maxLength="10"
                  />
                </div>
                {phoneError && (
                  <p className="text-red-500 text-sm mt-1">{phoneError}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">📱 Enter your mobile number to receive OTP</p>
              </div>
              
              <button
                onClick={sendOTP}
                disabled={loading || !phone}
                className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400"
              >
                {loading ? 'Sending OTP...' : 'Send OTP'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter OTP
                </label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, ''); // Remove non-digits
                    if (value.length <= 6) {
                      setOtp(value);
                    }
                  }}
                  placeholder="Enter OTP from SMS"
                  maxLength="6"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
                {demoInfo && (
                  <p className="text-sm text-blue-600 mt-2 p-2 bg-blue-50 rounded">
                    ℹ️ {demoInfo}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  🔒 Enter the 6-digit OTP sent to your phone number
                </p>
              </div>
              
              <button
                onClick={verifyOTP}
                disabled={loading || !otp}
                className="w-full bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400"
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
              
              <button
                onClick={changePhoneNumber}
                className="w-full bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Change Phone Number
              </button>
            </div>
          )}
          
          {error && (
            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}
          
          <div className="mt-8 text-center">
            <button
              onClick={() => setCurrentView('login-choice')}
              className="text-gray-500 hover:text-gray-700 underline mr-4"
            >
              Back to Login Options
            </button>
            <button
              onClick={() => setCurrentView('home')}
              className="text-gray-500 hover:text-gray-700 underline"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OTPLogin;