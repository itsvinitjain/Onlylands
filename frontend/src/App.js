import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    // Check if user is logged in
    if (token) {
      // Decode token to get user info (simplified)
      try {
        const tokenPayload = JSON.parse(atob(token.split('.')[1]));
        setUser({
          user_id: tokenPayload.user_id,
          user_type: tokenPayload.user_type
        });
      } catch (e) {
        localStorage.removeItem('token');
        setToken(null);
      }
    }
  }, [token]);

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentView('home');
  };

  const renderView = () => {
    switch (currentView) {
      case 'otp-login':
        return <OTPLogin setToken={setToken} setCurrentView={setCurrentView} />;
      case 'post-land':
        return <PostLandForm user={user} />;
      case 'broker-register':
        return <BrokerRegistration setCurrentView={setCurrentView} />;
      case 'broker-dashboard':
        return <BrokerDashboard user={user} />;
      case 'listings':
        return <ListingsView />;
      default:
        return <HomePage setCurrentView={setCurrentView} user={user} logout={logout} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {renderView()}
    </div>
  );
}

// Home Page Component
function HomePage({ setCurrentView, user, logout }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <header className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-green-800">🏞️ OnlyLands</h1>
            <p className="text-gray-600 mt-2">Agricultural & Residential Land Marketplace</p>
          </div>
          <nav className="flex space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  Welcome, {user.user_type === 'seller' ? 'Seller' : 'Broker'}
                </span>
                <button 
                  onClick={logout}
                  className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setCurrentView('listings')}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                View Listings
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Connect Land Owners with Trusted Brokers
          </h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            List your agricultural or residential land and reach 1000+ verified brokers instantly. 
            Premium listings get broadcast via WhatsApp to our broker network.
          </p>
          
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Seller Card */}
            <div className="bg-gradient-to-br from-green-100 to-green-200 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-green-800 mb-4">🌾 For Land Owners</h3>
              <ul className="text-green-700 mb-6 space-y-2">
                <li>• Post land with location & photos</li>
                <li>• Instant WhatsApp broadcast to 1000+ brokers</li>
                <li>• Premium listing for ₹299</li>
                <li>• OTP-based secure authentication</li>
              </ul>
              {user && user.user_type === 'seller' ? (
                <button 
                  onClick={() => setCurrentView('post-land')}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors w-full"
                >
                  Post Your Land
                </button>
              ) : (
                <button 
                  onClick={() => setCurrentView('otp-login')}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors w-full"
                >
                  Login as Seller
                </button>
              )}
            </div>

            {/* Broker Card */}
            <div className="bg-gradient-to-br from-blue-100 to-blue-200 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-blue-800 mb-4">🏢 For Brokers</h3>
              <ul className="text-blue-700 mb-6 space-y-2">
                <li>• Get instant notifications for new listings</li>
                <li>• Access to verified land owners</li>
                <li>• WhatsApp direct contact</li>
                <li>• Free registration</li>
              </ul>
              {user && user.user_type === 'broker' ? (
                <button 
                  onClick={() => setCurrentView('broker-dashboard')}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors w-full"
                >
                  View Dashboard
                </button>
              ) : (
                <button 
                  onClick={() => setCurrentView('broker-register')}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors w-full"
                >
                  Register as Broker
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      {stats && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">Platform Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.total_listings}</div>
              <div className="text-sm text-gray-600">Total Listings</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.active_listings}</div>
              <div className="text-sm text-gray-600">Active Listings</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.total_brokers}</div>
              <div className="text-sm text-gray-600">Total Brokers</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{stats.active_brokers}</div>
              <div className="text-sm text-gray-600">Active Brokers</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{stats.total_payments}</div>
              <div className="text-sm text-gray-600">Paid Listings</div>
            </div>
          </div>
        </div>
      )}

      {/* Featured Locations */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 text-center">Featured Locations</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-gray-800">Alibag</div>
            <div className="text-sm text-gray-600">Coastal Properties</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-gray-800">Nagpur</div>
            <div className="text-sm text-gray-600">Agricultural Land</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-gray-800">Lonavala</div>
            <div className="text-sm text-gray-600">Hill Station Plots</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold text-gray-800">Karjat</div>
            <div className="text-sm text-gray-600">Farmland & Villas</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// OTP Login Component
function OTPLogin({ setToken, setCurrentView }) {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sendOTP = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/auth/send-otp', { phone_number: phone });
      
      // Handle different response types
      if (response.data.status === 'demo_mode') {
        alert(`Demo Mode: Use OTP 123456 for testing\n\nNote: ${response.data.message}`);
      } else if (response.data.status === 'sent') {
        alert(`OTP sent successfully via ${response.data.channel.toUpperCase()}!`);
      }
      
      setStep(2);
    } catch (error) {
      alert('Failed to send OTP: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/auth/verify-otp', {
        phone_number: phone,
        otp_code: otp
      });
      
      if (response.data.verified) {
        localStorage.setItem('token', response.data.token);
        setToken(response.data.token);
        setCurrentView('home');
      } else {
        alert('Invalid OTP');
      }
    } catch (error) {
      alert('Verification failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Login with OTP</h2>
          <p className="text-gray-600 mt-2">Secure authentication for land owners</p>
        </div>

        {step === 1 ? (
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Phone Number
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 9876543210"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={sendOTP}
              disabled={loading || !phone}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg mt-4 hover:bg-blue-600 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Sending...' : 'Send OTP'}
            </button>
          </div>
        ) : (
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Enter OTP
            </label>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              placeholder="123456"
              maxLength="6"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={verifyOTP}
              disabled={loading || !otp}
              className="w-full bg-green-500 text-white py-2 px-4 rounded-lg mt-4 hover:bg-green-600 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>
          </div>
        )}

        <button
          onClick={() => setCurrentView('home')}
          className="w-full bg-gray-300 text-gray-700 py-2 px-4 rounded-lg mt-4 hover:bg-gray-400 transition-colors"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
}

// Post Land Form Component
function PostLandForm({ user }) {
  const [formData, setFormData] = useState({
    title: '',
    location: '',
    area: '',
    price: '',
    description: '',
    latitude: '',
    longitude: ''
  });
  const [loading, setLoading] = useState(false);
  const [listingCreated, setListingCreated] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create listing
      const response = await axios.post('/api/listings', {
        ...formData,
        latitude: formData.latitude ? parseFloat(formData.latitude) : null,
        longitude: formData.longitude ? parseFloat(formData.longitude) : null
      });

      setListingCreated(response.data.listing_id);
    } catch (error) {
      alert('Failed to create listing: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  if (listingCreated) {
    return <PaymentComponent listingId={listingCreated} />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Post Your Land</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              placeholder="e.g., 5 Acre Agricultural Land in Alibag"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Location
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              placeholder="e.g., Alibag, Raigad, Maharashtra"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Area
              </label>
              <input
                type="text"
                value={formData.area}
                onChange={(e) => setFormData({...formData, area: e.target.value})}
                placeholder="e.g., 5 Acres"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Price
              </label>
              <input
                type="text"
                value={formData.price}
                onChange={(e) => setFormData({...formData, price: e.target.value})}
                placeholder="e.g., 50 Lakhs"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Latitude (Optional)
              </label>
              <input
                type="number"
                step="any"
                value={formData.latitude}
                onChange={(e) => setFormData({...formData, latitude: e.target.value})}
                placeholder="e.g., 18.6414"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Longitude (Optional)
              </label>
              <input
                type="number"
                step="any"
                value={formData.longitude}
                onChange={(e) => setFormData({...formData, longitude: e.target.value})}
                placeholder="e.g., 72.9897"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Describe your land, nearby facilities, road access, etc."
              rows="4"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Creating Listing...' : 'Create Listing (₹299)'}
          </button>
        </form>
      </div>
    </div>
  );
}

// Payment Component
function PaymentComponent({ listingId }) {
  const [loading, setLoading] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);

  const handlePayment = async () => {
    setLoading(true);
    try {
      // Create payment order
      const orderResponse = await axios.post('/api/payments/create-order', {
        amount: 29900, // ₹299 in paise
        listing_id: listingId
      });

      const options = {
        key: orderResponse.data.key_id,
        amount: orderResponse.data.amount,
        currency: orderResponse.data.currency,
        order_id: orderResponse.data.order_id,
        name: 'OnlyLands',
        description: 'Premium Land Listing',
        handler: async function (response) {
          try {
            // Verify payment
            await axios.post('/api/payments/verify', {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });
            setPaymentSuccess(true);
          } catch (error) {
            alert('Payment verification failed');
          }
        },
        prefill: {
          name: 'Land Owner',
          email: 'owner@example.com',
          contact: '9999999999'
        },
        theme: {
          color: '#22c55e'
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      alert('Payment initialization failed');
    } finally {
      setLoading(false);
    }
  };

  if (paymentSuccess) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-600 mb-4">Payment Successful!</h2>
          <p className="text-gray-600 mb-6">
            Your land listing has been created and broadcast to 1000+ brokers via WhatsApp!
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Complete Payment</h2>
        
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <div className="flex justify-between items-center mb-2">
            <span>Premium Land Listing</span>
            <span className="font-bold">₹299</span>
          </div>
          <div className="text-sm text-gray-600">
            • Broadcast to 1000+ brokers
            • WhatsApp notifications
            • Priority listing
          </div>
        </div>

        <button
          onClick={handlePayment}
          disabled={loading}
          className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400"
        >
          {loading ? 'Initializing Payment...' : 'Pay ₹299'}
        </button>

        <p className="text-xs text-gray-500 text-center mt-4">
          Secure payment powered by Razorpay
        </p>
      </div>
    </div>
  );
}

// Broker Registration Component
function BrokerRegistration({ setCurrentView }) {
  const [formData, setFormData] = useState({
    name: '',
    agency: '',
    phone: '',
    email: '',
    location: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post('/api/brokers/register', formData);
      alert('Registration successful! You will now receive WhatsApp notifications for new listings.');
      setCurrentView('home');
    } catch (error) {
      alert('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Broker Registration</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Agency Name
            </label>
            <input
              type="text"
              value={formData.agency}
              onChange={(e) => setFormData({...formData, agency: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              WhatsApp Number
            </label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              placeholder="+91 9876543210"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Location
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              placeholder="e.g., Mumbai, Maharashtra"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Registering...' : 'Register as Broker'}
          </button>
        </form>

        <button
          onClick={() => setCurrentView('home')}
          className="w-full bg-gray-300 text-gray-700 py-2 px-4 rounded-lg mt-4 hover:bg-gray-400 transition-colors"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
}

// Broker Dashboard Component
function BrokerDashboard({ user }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`/api/brokers/${user.user_id}/leads`);
      setLeads(response.data.leads);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const contactOwner = (listing) => {
    const message = `Hi! I'm interested in your land listing: ${listing.title} in ${listing.location}. Can we discuss the details?`;
    const whatsappUrl = `https://wa.me/919876543210?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Broker Dashboard</h2>
        <p className="text-gray-600">Welcome to your lead management system</p>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading leads...</div>
      ) : (
        <div className="grid gap-6">
          {leads.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <h3 className="text-xl font-bold text-gray-800 mb-2">No leads yet</h3>
              <p className="text-gray-600">New land listings will appear here</p>
            </div>
          ) : (
            leads.map((listing) => (
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{listing.title}</h3>
                    <p className="text-gray-600">{listing.location}</p>
                  </div>
                  <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                    New Lead
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <span className="text-gray-500">Area:</span>
                    <span className="ml-2 font-semibold">{listing.area}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Price:</span>
                    <span className="ml-2 font-semibold">₹{listing.price}</span>
                  </div>
                </div>
                
                <p className="text-gray-700 mb-4">{listing.description}</p>
                
                <button
                  onClick={() => contactOwner(listing)}
                  className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
                >
                  Contact Owner via WhatsApp
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// Listings View Component
function ListingsView() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchListings();
  }, []);

  const fetchListings = async () => {
    try {
      const response = await axios.get('/api/listings');
      setListings(response.data.listings);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Active Land Listings</h2>
        <p className="text-gray-600">Browse available properties</p>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading listings...</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.length === 0 ? (
            <div className="col-span-full bg-white rounded-lg shadow-md p-8 text-center">
              <h3 className="text-xl font-bold text-gray-800 mb-2">No listings yet</h3>
              <p className="text-gray-600">New land listings will appear here</p>
            </div>
          ) : (
            listings.map((listing) => (
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="p-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-2">{listing.title}</h3>
                  <p className="text-gray-600 mb-2">{listing.location}</p>
                  
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    <div>
                      <span className="text-gray-500 text-sm">Area:</span>
                      <p className="font-semibold">{listing.area}</p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-sm">Price:</span>
                      <p className="font-semibold text-green-600">₹{listing.price}</p>
                    </div>
                  </div>
                  
                  <p className="text-gray-700 text-sm mb-4 line-clamp-3">{listing.description}</p>
                  
                  <button className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors">
                    Contact for Details
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default App;