import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [listings, setListings] = useState([]);
  const [myListings, setMyListings] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  // Land form state
  const [landForm, setLandForm] = useState({
    title: '',
    area: '',
    price: '',
    description: '',
    latitude: '',
    longitude: '',
    photos: [],
    videos: []
  });

  // Broker form state
  const [brokerForm, setBrokerForm] = useState({
    name: '',
    agency: '',
    phone_number: '',
    email: '',
    photo: ''
  });

  useEffect(() => {
    if (token) {
      fetchUser();
      fetchListings();
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      // Decode token to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser(payload);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    }
  };

  const fetchListings = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/listings`);
      setListings(response.data.listings || []);
    } catch (error) {
      console.error('Error fetching listings:', error);
    }
  };

  const fetchMyListings = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/my-listings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyListings(response.data.listings || []);
    } catch (error) {
      console.error('Error fetching my listings:', error);
    }
  };

  const sendOtp = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/send-otp`, {
        phone_number: phoneNumber
      });
      setIsOtpSent(true);
      setError('');
    } catch (error) {
      setError('Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/verify-otp`, {
        phone_number: phoneNumber,
        otp: otp
      });
      
      if (response.data.token) {
        setToken(response.data.token);
        localStorage.setItem('token', response.data.token);
        setUser(response.data.user);
        setCurrentView('dashboard');
      }
    } catch (error) {
      setError('Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    setCurrentView('login');
    setPhoneNumber('');
    setOtp('');
    setIsOtpSent(false);
  };

  const handleFileUpload = (files, type) => {
    const uploadedFiles = Array.from(files).map(file => ({
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setLandForm(prev => ({
      ...prev,
      [type]: [...prev[type], ...uploadedFiles]
    }));
  };

  const removeFile = (index, type) => {
    setLandForm(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  const submitLandListing = async () => {
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('title', landForm.title);
      formData.append('area', landForm.area);
      formData.append('price', landForm.price);
      formData.append('description', landForm.description);
      formData.append('latitude', landForm.latitude);
      formData.append('longitude', landForm.longitude);
      
      landForm.photos.forEach(photo => {
        formData.append('photos', photo.file);
      });
      
      landForm.videos.forEach(video => {
        formData.append('videos', video.file);
      });
      
      const response = await axios.post(`${backendUrl}/api/post-land`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.listing_id) {
        setCurrentView('payment');
        setLandForm({
          title: '',
          area: '',
          price: '',
          description: '',
          latitude: '',
          longitude: '',
          photos: [],
          videos: []
        });
      }
    } catch (error) {
      setError('Failed to submit listing. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const submitBrokerSignup = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${backendUrl}/api/broker-signup`, brokerForm);
      setBrokers([...brokers, response.data]);
      setBrokerForm({
        name: '',
        agency: '',
        phone_number: '',
        email: '',
        photo: ''
      });
      setCurrentView('broker-dashboard');
    } catch (error) {
      setError('Failed to register broker. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchBrokerDashboard = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/broker-dashboard`);
      setListings(response.data.listings || []);
      setCurrentView('broker-dashboard');
    } catch (error) {
      console.error('Error fetching broker dashboard:', error);
    }
  };

  const getImageSrc = (imageData) => {
    if (!imageData) return null;
    if (imageData.startsWith('data:')) return imageData;
    if (imageData.startsWith('https://')) return imageData;
    return null;
  };

  const openWhatsApp = (phoneNumber) => {
    const message = encodeURIComponent("Hi, I'm interested in your land listing from OnlyLands.");
    window.open(`https://wa.me/${phoneNumber}?text=${message}`, '_blank');
  };

  // Login View
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">OnlyLands</h2>
          <p className="text-center text-gray-600 mb-8">Buy & Sell Agricultural Land</p>
          
          {!isOtpSent ? (
            <div className="space-y-4">
              <input
                type="tel"
                placeholder="Enter phone number (+91XXXXXXXXXX)"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={sendOtp}
                disabled={loading || !phoneNumber}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send OTP'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Enter OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={verifyOtp}
                disabled={loading || !otp}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
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
              onClick={() => setCurrentView('broker-signup')}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Register as Broker
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard View
  if (currentView === 'dashboard') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-2xl font-bold text-gray-800">OnlyLands Dashboard</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => setCurrentView('post-land')}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  Post Land
                </button>
                <button
                  onClick={() => {
                    fetchMyListings();
                    setCurrentView('my-listings');
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  My Listings
                </button>
                <button
                  onClick={logout}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 py-8">
          <h2 className="text-xl font-semibold mb-6">Available Land Listings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing) => (
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden">
                {listing.photos && listing.photos.length > 0 && (
                  <img
                    src={getImageSrc(listing.photos[0])}
                    alt={listing.title}
                    className="w-full h-48 object-cover"
                  />
                )}
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">{listing.title}</h3>
                  <p className="text-gray-600 mb-2">Area: {listing.area}</p>
                  <p className="text-green-600 font-bold mb-2">₹{listing.price}</p>
                  <p className="text-gray-600 mb-4">{listing.description}</p>
                  <button
                    onClick={() => openWhatsApp(listing.phone_number)}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
                  >
                    Contact Owner
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // My Listings View
  if (currentView === 'my-listings') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-2xl font-bold text-gray-800">My Listings</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => setCurrentView('dashboard')}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
                >
                  Back to Dashboard
                </button>
                <button
                  onClick={logout}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {myListings.map((listing) => (
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden">
                {listing.photos && listing.photos.length > 0 && (
                  <img
                    src={getImageSrc(listing.photos[0])}
                    alt={listing.title}
                    className="w-full h-48 object-cover"
                  />
                )}
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">{listing.title}</h3>
                  <p className="text-gray-600 mb-2">Area: {listing.area}</p>
                  <p className="text-green-600 font-bold mb-2">₹{listing.price}</p>
                  <p className="text-gray-600 mb-4">{listing.description}</p>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    listing.status === 'active' ? 'bg-green-100 text-green-800' : 
                    listing.status === 'pending_payment' ? 'bg-yellow-100 text-yellow-800' : 
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {listing.status === 'active' ? 'Active' : 
                     listing.status === 'pending_payment' ? 'Pending Payment' : 
                     listing.status}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Post Land View
  if (currentView === 'post-land') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-2xl font-bold text-gray-800">Post Land Listing</h1>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  type="text"
                  value={landForm.title}
                  onChange={(e) => setLandForm({...landForm, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Area</label>
                <input
                  type="text"
                  value={landForm.area}
                  onChange={(e) => setLandForm({...landForm, area: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price</label>
                <input
                  type="text"
                  value={landForm.price}
                  onChange={(e) => setLandForm({...landForm, price: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Latitude"
                    value={landForm.latitude}
                    onChange={(e) => setLandForm({...landForm, latitude: e.target.value})}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <input
                    type="text"
                    placeholder="Longitude"
                    value={landForm.longitude}
                    onChange={(e) => setLandForm({...landForm, longitude: e.target.value})}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={landForm.description}
                  onChange={(e) => setLandForm({...landForm, description: e.target.value})}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Photos (Max 5)</label>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => handleFileUpload(e.target.files, 'photos')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {landForm.photos.map((photo, index) => (
                    <div key={index} className="relative">
                      <img src={photo.preview} alt={`Preview ${index}`} className="w-full h-20 object-cover rounded" />
                      <button
                        onClick={() => removeFile(index, 'photos')}
                        className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Videos (Max 2)</label>
                <input
                  type="file"
                  multiple
                  accept="video/*"
                  onChange={(e) => handleFileUpload(e.target.files, 'videos')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <div className="mt-2">
                  {landForm.videos.map((video, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-100 rounded mb-2">
                      <span className="text-sm">{video.file.name}</span>
                      <button
                        onClick={() => removeFile(index, 'videos')}
                        className="bg-red-500 text-white rounded px-2 py-1 text-xs"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {error && (
              <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {error}
              </div>
            )}
            
            <div className="mt-6">
              <button
                onClick={submitLandListing}
                disabled={loading}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Submit Listing'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Broker Signup View
  if (currentView === 'broker-signup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">Broker Registration</h2>
          
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Full Name"
              value={brokerForm.name}
              onChange={(e) => setBrokerForm({...brokerForm, name: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            
            <input
              type="text"
              placeholder="Agency Name"
              value={brokerForm.agency}
              onChange={(e) => setBrokerForm({...brokerForm, agency: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            
            <input
              type="tel"
              placeholder="Phone Number"
              value={brokerForm.phone_number}
              onChange={(e) => setBrokerForm({...brokerForm, phone_number: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            
            <input
              type="email"
              placeholder="Email"
              value={brokerForm.email}
              onChange={(e) => setBrokerForm({...brokerForm, email: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            
            <button
              onClick={submitBrokerSignup}
              disabled={loading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Registering...' : 'Register as Broker'}
            </button>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}
          
          <div className="mt-4 text-center">
            <button
              onClick={() => setCurrentView('login')}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Broker Dashboard View
  if (currentView === 'broker-dashboard') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center py-4">
              <h1 className="text-2xl font-bold text-gray-800">Broker Dashboard</h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => setCurrentView('login')}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 py-8">
          <h2 className="text-xl font-semibold mb-6">Land Leads</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing) => (
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden">
                {listing.photos && listing.photos.length > 0 && (
                  <img
                    src={getImageSrc(listing.photos[0])}
                    alt={listing.title}
                    className="w-full h-48 object-cover"
                  />
                )}
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">{listing.title}</h3>
                  <p className="text-gray-600 mb-2">Area: {listing.area}</p>
                  <p className="text-green-600 font-bold mb-2">₹{listing.price}</p>
                  <p className="text-gray-600 mb-4">{listing.description}</p>
                  <button
                    onClick={() => openWhatsApp(listing.phone_number)}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
                  >
                    Contact Owner
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Payment View
  if (currentView === 'payment') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">Payment Required</h2>
          <p className="text-center text-gray-600 mb-8">
            Your land listing has been submitted successfully! 
            Please complete the payment to activate your listing.
          </p>
          
          <div className="space-y-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold text-green-800">Premium Listing</h3>
              <p className="text-green-600">₹500 - One-time payment</p>
            </div>
            
            <p className="text-sm text-gray-600 text-center">
              Your listing will be activated immediately after payment confirmation.
            </p>
            
            <button
              onClick={() => setCurrentView('dashboard')}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default App;