import React, { useState } from 'react';
import axios from 'axios';

const OTPLogin = ({ setToken, setCurrentView, userType = 'seller' }) => {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const sendOTP = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/send-otp`, {
        phone_number: phone,
        user_type: userType
      });
      
      if (response.data.message) {
        setIsOtpSent(true);
        setError('');
        
        // Show demo mode info if applicable
        if (response.data.status === 'demo_mode') {
          setError('Demo Mode: Use OTP 123456 for testing');
        }
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to send OTP. Please try again.');
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
        setCurrentView('home');
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
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 7021758061"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-2">
                  📱 Enter your mobile number to receive OTP
                </p>
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
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="Enter 6-digit OTP"
                  maxLength="6"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-2">
                  🔒 Enter the OTP sent to your phone number
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
                onClick={() => setIsOtpSent(false)}
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