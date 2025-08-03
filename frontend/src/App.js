import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoginChoice from './LoginChoice';
import OTPLogin from './OTPLogin';
import EnhancedListingsView from './EnhancedListingsView';
import AdminLogin from './AdminLogin';
import AdminDashboard from './AdminDashboard';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

// Helper function to get image source (S3 URL or base64) - Global utility
const getImageSrc = (image) => {
  if (image.s3_url) {
    return image.s3_url;  // New S3 storage
  } else if (image.data) {
    return `data:${image.content_type};base64,${image.data}`;  // Legacy base64 storage
  }
  return null;
};

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [brokerRegistered, setBrokerRegistered] = useState(false);

  useEffect(() => {
    // Check URL for admin access
    const urlPath = window.location.pathname;
    if (urlPath === '/admin') {
      setCurrentView('admin');
    }

    // Check if user is logged in
    if (token) {
      // Decode token to get user info (simplified)
      try {
        const tokenPayload = JSON.parse(atob(token.split('.')[1]));
        const userData = {
          user_id: tokenPayload.user_id,
          user_type: tokenPayload.user_type,
          phone_number: tokenPayload.phone_number
        };
        setUser(userData);
        
        // If user is a broker, check if they're registered
        if (userData.user_type === 'broker') {
          checkBrokerRegistrationStatus();
        }
      } catch (e) {
        localStorage.removeItem('token');
        setToken(null);
      }
    }
  }, [token]);

  const checkBrokerRegistrationStatus = async () => {
    try {
      const response = await axios.get('/api/broker-profile', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.data && response.data.broker) {
        setBrokerRegistered(true);
      }
    } catch (error) {
      // 404 means not registered yet, which is fine
      setBrokerRegistered(false);
    }
  };

  const navigateToAdmin = () => {
    setCurrentView('admin');
    window.history.pushState(null, '', '/admin');
  };

  const updateToken = (newToken) => {
    setToken(newToken);
    if (newToken) {
      try {
        const tokenPayload = JSON.parse(atob(newToken.split('.')[1]));
        const userData = {
          user_id: tokenPayload.user_id,
          user_type: tokenPayload.user_type,
          phone_number: tokenPayload.phone_number
        };
        setUser(userData);
        
        // Note: Broker redirect is now handled in OTP verification
      } catch (e) {
        console.error('Failed to parse token:', e);
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } else {
      setUser(null);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setCurrentView('home');
  };

  const renderView = () => {
    switch (currentView) {
      case 'login-choice':
        return <LoginChoice setCurrentView={setCurrentView} />;
      case 'seller-login':
        return <OTPLogin setToken={updateToken} setCurrentView={setCurrentView} userType="seller" />;
      case 'broker-login':
        return <OTPLogin setToken={updateToken} setCurrentView={setCurrentView} userType="broker" />;
      case 'post-land':
        return <PostLandForm user={user} setCurrentView={setCurrentView} />;
      case 'my-listings':
        return <MyListings user={user} setCurrentView={setCurrentView} />;
      case 'broker-register':
        return <BrokerRegistration setCurrentView={setCurrentView} />;
      case 'broker-dashboard':
        return <BrokerDashboard user={user} />;
      case 'admin':
        return <AdminInterface />;
      case 'listings':
        return <EnhancedListingsView setCurrentView={setCurrentView} />;
      default:
        return <HomePage setCurrentView={setCurrentView} user={user} logout={logout} brokerRegistered={brokerRegistered} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {renderView()}
    </div>
  );
}

// Home Page Component
function HomePage({ setCurrentView, user, logout, brokerRegistered }) {
  const [stats, setStats] = useState(null);
  const [logoClickCount, setLogoClickCount] = useState(0);

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

  const handleLogoClick = () => {
    setLogoClickCount(prev => {
      const newCount = prev + 1;
      if (newCount === 5) {
        // Secret admin access - click logo 5 times
        setCurrentView('admin');
        window.history.pushState(null, '', '/admin');
        return 0;
      }
      return newCount;
    });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <header className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center">
          <div className="mb-4 md:mb-0">
            <h1 
              className="text-2xl md:text-4xl font-bold text-green-800 cursor-pointer" 
              onClick={handleLogoClick}
              title="🏞️ OnlyLands"
            >
              🏞️ OnlyLands
            </h1>
            <p className="text-sm md:text-base text-gray-600 mt-1 md:mt-2">Comprehensive Land Listing Platform</p>
          </div>
          <nav className="flex flex-wrap gap-2 md:gap-4">
            {user ? (
              <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                <div className="text-xs md:text-sm text-gray-600">
                  <span className="font-semibold">Welcome, {user.user_type === 'seller' ? 'Seller' : 'Broker'}</span>
                  <br className="md:hidden" />
                  <span className="text-gray-500"> ({user.phone_number})</span>
                </div>
                <button 
                  onClick={logout}
                  className="bg-red-500 text-white px-3 py-2 md:px-4 md:py-2 rounded-lg hover:bg-red-600 transition-colors text-sm md:text-base"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={() => setCurrentView('listings')}
                  className="bg-blue-500 text-white px-3 py-2 md:px-4 md:py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm md:text-base"
                >
                  View Listings
                </button>
                <button 
                  onClick={() => setCurrentView('login-choice')}
                  className="bg-green-500 text-white px-3 py-2 md:px-4 md:py-2 rounded-lg hover:bg-green-600 transition-colors text-sm md:text-base"
                >
                  Login
                </button>
              </div>
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
                <div className="space-y-3">
                  <button 
                    onClick={() => setCurrentView('post-land')}
                    className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors w-full"
                  >
                    Post Your Land
                  </button>
                  <button 
                    onClick={() => setCurrentView('my-listings')}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors w-full"
                  >
                    My Listings
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => setCurrentView('login-choice')}
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
              {user && user.user_type === 'broker' && brokerRegistered ? (
                <button 
                  onClick={() => setCurrentView('broker-dashboard')}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors w-full"
                >
                  View Dashboard
                </button>
              ) : (
                <button 
                  onClick={() => setCurrentView('login-choice')}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors w-full"
                >
                  {user && user.user_type === 'broker' ? 'Complete Registration' : 'Register as Broker'}
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



// Payment Success Modal Component
function PaymentSuccessModal({ isOpen, onClose, onViewListings }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="mb-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">🎉 Payment Successful!</h3>
            <p className="text-gray-600 mb-6">
              Your land listing has been activated and is now live on our platform. Brokers will be able to see your listing and contact you via WhatsApp.
            </p>
          </div>
          
          <div className="space-y-3">
            <button
              onClick={onViewListings}
              className="w-full bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors font-semibold"
            >
              📋 View My Listings
            </button>
            <button
              onClick={onClose}
              className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200 transition-colors"
            >
              🏠 Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
function PostLandForm({ user, setCurrentView }) {
  // Load saved data from localStorage or use defaults
  const getSavedFormData = () => {
    const saved = localStorage.getItem('postLandFormData');
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      title: '',
      location: '',
      area: '',
      price: '',
      description: '',
      googleMapsLink: ''
    };
  };

  const [formData, setFormData] = useState(getSavedFormData);
  const [images, setImages] = useState([]);
  const [videos, setVideos] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [videoPreviews, setVideoPreviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listingCreated, setListingCreated] = useState(null);

  // Save form data to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('postLandFormData', JSON.stringify(formData));
  }, [formData]);

  // Clear form data after successful submission
  const clearFormData = () => {
    localStorage.removeItem('postLandFormData');
    setFormData({
      title: '',
      location: '',
      area: '',
      price: '',
      description: '',
      googleMapsLink: ''
    });
  };
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false);

  const handleImageChange = (e) => {
    const newFiles = Array.from(e.target.files);
    
    // Check if adding new files would exceed limit
    const totalFiles = images.length + newFiles.length;
    if (totalFiles > 5) {
      alert(`Maximum 5 photos allowed. You can add ${5 - images.length} more photos.`);
      return;
    }
    
    // Append new files to existing images
    const updatedImages = [...images, ...newFiles];
    setImages(updatedImages);
    
    // Create previews for new files
    const newPreviews = newFiles.map(file => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    
    // Append new previews to existing previews
    const updatedPreviews = [...imagePreviews, ...newPreviews];
    setImagePreviews(updatedPreviews);
    
    // Reset file input to allow selecting same files again if needed
    e.target.value = '';
  };

  const handleVideoChange = (e) => {
    const newFiles = Array.from(e.target.files);
    
    // Check if adding new files would exceed limit
    const totalFiles = videos.length + newFiles.length;
    if (totalFiles > 2) {
      alert(`Maximum 2 videos allowed. You can add ${2 - videos.length} more videos.`);
      return;
    }
    
    // Append new files to existing videos
    const updatedVideos = [...videos, ...newFiles];
    setVideos(updatedVideos);
    
    // Create previews for new files
    const newPreviews = newFiles.map(file => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    
    // Append new previews to existing previews
    const updatedPreviews = [...videoPreviews, ...newPreviews];
    setVideoPreviews(updatedPreviews);
    
    // Reset file input to allow selecting same files again if needed
    e.target.value = '';
  };

  const removeImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    const newPreviews = imagePreviews.filter((_, i) => i !== index);
    setImages(newImages);
    setImagePreviews(newPreviews);
  };

  const removeVideo = (index) => {
    const newVideos = videos.filter((_, i) => i !== index);
    const newPreviews = videoPreviews.filter((_, i) => i !== index);
    setVideos(newVideos);
    setVideoPreviews(newPreviews);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create FormData for file upload
      const formDataToSend = new FormData();
      
      // Add form fields to FormData
      formDataToSend.append('title', formData.title);
      formDataToSend.append('location', formData.location);
      formDataToSend.append('area', formData.area);
      formDataToSend.append('price', formData.price);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('google_maps_link', formData.googleMapsLink || ''); // Google Maps location link
      formDataToSend.append('latitude', '18.6414'); // Default latitude
      formDataToSend.append('longitude', '72.9897'); // Default longitude
      
      // Add images
      images.forEach(image => {
        formDataToSend.append('photos', image);
      });
      
      // Add videos
      videos.forEach(video => {
        formDataToSend.append('videos', video);
      });

      const response = await axios.post('/api/post-land', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      setListingCreated(response.data.listing_id);
      clearFormData(); // Clear saved form data after successful submission
    } catch (error) {
      alert('Failed to create listing: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  if (listingCreated) {
    return <PaymentComponent listingId={listingCreated} user={user} setCurrentView={setCurrentView} />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Post Your Land</h2>
          <button
            type="button"
            onClick={() => window.history.back()}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="e.g., 5 Acre Agricultural Land in Alibag"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
              <p className="text-xs text-gray-500 mt-1">Max 100 characters</p>
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Location <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                list="location-suggestions"
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                placeholder="Select or type location"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
              <datalist id="location-suggestions">
                <option value="Alibag, Raigad, Maharashtra" />
                <option value="Karjat, Raigad, Maharashtra" />
                <option value="Nagpur, Maharashtra" />
                <option value="Lonavala, Pune, Maharashtra" />
              </datalist>
              <p className="text-xs text-gray-500 mt-1">Popular locations: Alibag, Karjat, Nagpur, Lonavala</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Area <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.area}
                onChange={(e) => setFormData({...formData, area: e.target.value})}
                placeholder="e.g., 5 Acres or 2000 Sq.ft"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                required
              />
              <p className="text-xs text-gray-500 mt-1">Specify unit (Acres, Sq.ft, Gunthas, etc.)</p>
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Price <span className="text-red-500">*</span>
              </label>
              <div className="flex">
                <span className="inline-flex items-center px-3 text-sm text-gray-900 bg-gray-200 border border-r-0 border-gray-300 rounded-l-md">
                  ₹
                </span>
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: e.target.value})}
                  placeholder="e.g., 5000000"
                  min="1"
                  step="1"
                  className="flex-1 px-3 py-2 border-l-0 border border-gray-300 rounded-r-lg focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">Enter amount in Rupees (numbers only, e.g., 5000000)</p>
            </div>
          </div>

          <div>
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Google Maps Location Link
              </label>
              <input
                type="url"
                value={formData.googleMapsLink}
                onChange={(e) => setFormData({...formData, googleMapsLink: e.target.value})}
                placeholder="e.g., https://maps.google.com/..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">📍 Paste Google Maps link for precise location</p>
            </div>
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Describe your land, nearby facilities, road access, soil type, water availability, etc."
              rows="4"
              maxLength="500"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">{formData.description.length}/500 characters</p>
          </div>

          {/* Photo Upload Section - Enhanced */}
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              📷 Upload Photos
            </label>
            
            {/* Photo Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
                id="photo-upload"
              />
              <label htmlFor="photo-upload" className="cursor-pointer">
                <div className="mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="text-center">
                  <p className="text-lg text-gray-600 font-semibold mb-1">Click to upload photos</p>
                  <p className="text-sm text-gray-500">or drag and drop</p>
                  <p className="text-xs text-gray-400 mt-2">PNG, JPG, WebP up to 10MB each (Max 5 photos)</p>
                </div>
              </label>
            </div>
            
            {/* Image Previews */}
            {imagePreviews.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-gray-700">Photos ({imagePreviews.length}/5)</p>
                  <button
                    type="button"
                    onClick={() => setImagePreviews([])}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove All
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {imagePreviews.map((preview, index) => (
                    <div key={index} className="relative group">
                      <div className="aspect-square rounded-lg overflow-hidden border-2 border-gray-200">
                        <img
                          src={preview.url}
                          alt={preview.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                      <p className="text-xs text-gray-600 mt-1 truncate text-center">{preview.name}</p>
                    </div>
                  ))}
                  
                  {/* Add more photos button */}
                  {imagePreviews.length < 5 && (
                    <div className="aspect-square rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                      <label htmlFor="photo-upload" className="cursor-pointer flex flex-col items-center text-gray-400 hover:text-gray-600">
                        <svg className="w-8 h-8 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <span className="text-xs">Add More</span>
                      </label>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Video Upload Section - Enhanced */}
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">
              🎥 Upload Videos
            </label>
            
            {/* Video Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                multiple
                accept="video/*"
                onChange={handleVideoChange}
                className="hidden"
                id="video-upload"
              />
              <label htmlFor="video-upload" className="cursor-pointer">
                <div className="mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="text-center">
                  <p className="text-lg text-gray-600 font-semibold mb-1">Click to upload videos</p>
                  <p className="text-sm text-gray-500">or drag and drop</p>
                  <p className="text-xs text-gray-400 mt-2">MP4, WebM, MOV up to 50MB each (Max 2 videos)</p>
                </div>
              </label>
            </div>
            
            {/* Video Previews */}
            {videoPreviews.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-gray-700">Videos ({videoPreviews.length}/2)</p>
                  <button
                    type="button"
                    onClick={() => setVideoPreviews([])}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove All
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {videoPreviews.map((preview, index) => (
                    <div key={index} className="relative group">
                      <div className="rounded-lg overflow-hidden border-2 border-gray-200">
                        <video
                          src={preview.url}
                          controls
                          className="w-full h-48 object-cover"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => removeVideo(index)}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                      <p className="text-xs text-gray-600 mt-1 truncate text-center">{preview.name}</p>
                    </div>
                  ))}
                  
                  {/* Add more videos button */}
                  {videoPreviews.length < 2 && (
                    <div className="rounded-lg border-2 border-dashed border-gray-300 h-48 flex items-center justify-center">
                      <label htmlFor="video-upload" className="cursor-pointer flex flex-col items-center text-gray-400 hover:text-gray-600">
                        <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        <span className="text-sm">Add More Videos</span>
                      </label>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">📋 Listing Summary</h3>
            <div className="text-sm text-blue-700">
              <p>• Photos: {images.length} selected</p>
              <p>• Videos: {videos.length} selected</p>
              <p>• Premium listing with WhatsApp broadcast</p>
              <p>• Instant activation after payment</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Creating Listing...' : '🚀 Create Listing (₹299)'}
          </button>

          <p className="text-xs text-gray-500 text-center mt-2">
            💡 Payment required to activate your listing
          </p>
        </form>
      </div>
    </div>
  );
}

// Payment Component
function PaymentComponent({ listingId, user, setCurrentView }) {
  const [loading, setLoading] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);

  // Generate Terms and Conditions PDF content
  const generateTermsPDF = () => {
    const termsContent = `
      ONLYLANDS - TERMS AND CONDITIONS
      
      1. PAYMENT POLICY
      - All payments are non-refundable once processed
      - Premium listing fee: ₹299 (inclusive of all taxes)
      - Payment must be completed to activate listings
      
      2. LISTING POLICY  
      - Listings are valid for 30 days from activation
      - OnlyLands reserves the right to remove inappropriate content
      - Users must provide accurate property information
      
      3. BROKER NETWORK
      - Listings are shared with 1000+ verified brokers
      - WhatsApp notifications sent to interested brokers
      - OnlyLands is not responsible for broker communications
      
      4. PRIVACY POLICY
      - User data is protected and not shared with third parties
      - Phone numbers are used only for authentication and notifications
      - Property details are visible to registered brokers only
      
      5. LIABILITY
      - OnlyLands acts as a platform facilitator only
      - Users are responsible for property verification
      - All transactions between users and brokers are independent
      
      6. REFUND POLICY
      - No refunds for premium listing fees
      - In case of technical issues, contact support within 24 hours
      - Refunds processed only for technical failures on our end
      
      7. CONTACT
      - Support: support@onlylands.in
      - Technical Issues: tech@onlylands.in
      
      By proceeding with payment, you agree to these terms and conditions.
    `;
    
    const blob = new Blob([termsContent], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  const handlePayment = async () => {
    setLoading(true);
    try {
      // Create payment order
      const orderResponse = await axios.post('/api/create-payment-order', {
        amount: 299, // ₹299 
        listing_id: listingId
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      const { order, demo_mode } = orderResponse.data;

      if (demo_mode) {
        // Create a Razorpay-like demo interface
        console.log('Demo payment mode active - showing Razorpay-like interface');
        
        // Create demo payment modal
        const demoModal = document.createElement('div');
        demoModal.id = 'razorpay-demo-modal';
        demoModal.innerHTML = `
          <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 8px; padding: 0; width: 400px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
              <!-- Razorpay Header -->
              <div style="background: #528FF0; color: white; padding: 16px 20px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                  <div style="width: 24px; height: 24px; background: white; border-radius: 4px; margin-right: 10px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: #528FF0; font-weight: bold; font-size: 14px;">R</span>
                  </div>
                  <span style="font-weight: 500;">Razorpay Secure (Demo)</span>
                </div>
                <button onclick="document.getElementById('razorpay-demo-modal').remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
              </div>
              
              <!-- Payment Details -->
              <div style="padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                  <h3 style="margin: 0 0 5px 0; color: #333;">Pay OnlyLands</h3>
                  <p style="margin: 0; color: #666; font-size: 14px;">Premium Listing Payment</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #666;">Amount:</span>
                    <span style="font-weight: bold; color: #333;">₹${order.amount / 100}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #666;">Order ID:</span>
                    <span style="font-size: 12px; color: #666;">${order.id}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #666;">Currency:</span>
                    <span style="color: #333;">INR</span>
                  </div>
                </div>
                
                <!-- Demo Test Cards -->
                <div style="margin-bottom: 20px;">
                  <h4 style="margin: 0 0 10px 0; color: #333; font-size: 14px;">Demo Test Payment</h4>
                  <div style="background: #e3f2fd; padding: 10px; border-radius: 4px; font-size: 12px; color: #1565c0;">
                    💳 This is a demo payment. Click "Pay Now" to simulate successful payment.
                  </div>
                </div>
                
                <!-- Payment Buttons -->
                <div style="display: flex; gap: 10px;">
                  <button onclick="document.getElementById('razorpay-demo-modal').remove()" style="flex: 1; padding: 12px; border: 1px solid #ddd; background: white; color: #666; border-radius: 4px; cursor: pointer;">Cancel</button>
                  <button id="demo-pay-button" style="flex: 2; padding: 12px; background: #528FF0; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">Pay ₹${order.amount / 100}</button>
                </div>
                
                <!-- Security Info -->
                <div style="text-align: center; margin-top: 15px; font-size: 11px; color: #999;">
                  🔒 Demo payments are secure and for testing only
                </div>
              </div>
            </div>
          </div>
        `;
        
        document.body.appendChild(demoModal);
        
        // Handle demo payment
        document.getElementById('demo-pay-button').onclick = async () => {
          try {
            // Show processing state
            document.getElementById('demo-pay-button').innerHTML = 'Processing...';
            document.getElementById('demo-pay-button').disabled = true;
            
            // Simulate payment processing delay
            setTimeout(async () => {
              try {
                // Simulate successful payment with demo data
                const demoResponse = {
                  razorpay_order_id: order.id,
                  razorpay_payment_id: `pay_demo_${Date.now()}`,
                  razorpay_signature: `demo_signature_${Date.now()}`
                };

                // Verify the demo payment
                await axios.post('/api/verify-payment', demoResponse, {
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                  }
                });

                // Remove modal
                document.getElementById('razorpay-demo-modal').remove();
                
                // Show success modal instead of alert
                setShowPaymentSuccess(true);
                setPaymentSuccess(true);
                
              } catch (error) {
                document.getElementById('razorpay-demo-modal').remove();
                alert('Payment verification failed: ' + (error.response?.data?.detail || 'Unknown error'));
              }
            }, 2000); // 2 second delay to simulate processing
            
          } catch (error) {
            document.getElementById('razorpay-demo-modal').remove();
            alert('Payment processing failed: ' + error.message);
          }
        };
        
      } else {
        // Handle real Razorpay payment
        const options = {
          key: process.env.REACT_APP_RAZORPAY_KEY_ID,
          amount: order.amount,
          currency: order.currency,
          name: 'OnlyLands',
          description: 'Premium Listing Payment',
          order_id: order.id,
          handler: async function (response) {
            try {
              // Verify payment
              await axios.post('/api/verify-payment', {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              }, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
              });
              setShowPaymentSuccess(true);
              setPaymentSuccess(true);
            } catch (error) {
              alert('Payment verification failed: ' + (error.response?.data?.detail || 'Unknown error'));
            }
          },
          prefill: {
            name: user?.name || '',
            email: user?.email || '',
            contact: user?.phone_number || ''
          },
          theme: {
            color: '#10B981'
          }
        };

        const razorpay = new window.Razorpay(options);
        razorpay.open();
      }
    } catch (error) {
      alert('Payment processing failed: ' + (error.response?.data?.detail || 'Unknown error'));
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
          <div className="bg-green-50 p-4 rounded-lg mb-6">
            <p className="text-green-800 font-semibold mb-2">🎉 Payment Completed Successfully</p>
            <p className="text-gray-600 text-sm mb-2">
              Your land listing has been activated and is now live!
            </p>
            <p className="text-gray-600 text-sm">
              📢 WhatsApp broadcast sent to 1000+ brokers automatically
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => setCurrentView('home')}
              className="bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 transition-colors"
            >
              🏠 Back to Home
            </button>
            <button
              onClick={() => setCurrentView('my-listings')}
              className="bg-green-500 text-white px-4 py-3 rounded-lg hover:bg-green-600 transition-colors"
            >
              📋 View My Listings
            </button>
          </div>
          <p className="text-xs text-gray-500">
            💡 Your listing is now active and visible to brokers
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Complete Payment</h2>
          <button
            onClick={() => setCurrentView('post-land')}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
            Back to Post Land Form
          </button>
        </div>
        
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-6 rounded-lg mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Premium Land Listing</h3>
            <span className="text-2xl font-bold text-blue-600">₹299</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-700">
            <div className="flex items-center">
              <span className="text-green-500 mr-2">📢</span>
              <span>Shared with 1000+ brokers</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">📱</span>
              <span>WhatsApp notifications</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">⭐</span>
              <span>Priority placement in listings</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">⚡</span>
              <span>Instant activation</span>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg mb-6">
          <div className="flex items-center mb-2">
            <span className="text-green-600 mr-2">🔒</span>
            <span className="font-semibold text-green-800">Secure Payment</span>
          </div>
          <p className="text-green-700 text-sm">
            Powered by Razorpay - India's most trusted payment gateway
          </p>
        </div>

        {/* Terms and Conditions */}
        <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-4">
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="acceptTerms"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="acceptTerms" className="text-sm text-gray-700 flex-1">
              I accept the{' '}
              <button
                type="button"
                onClick={generateTermsPDF}
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                Terms and Conditions
              </button>
              {' '}including the no-refund policy and website policies.
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            📋 Click on "Terms and Conditions" to view the complete policy document.
          </p>
        </div>

        <button
          onClick={handlePayment}
          disabled={loading || !acceptTerms}
          className={`w-full py-3 px-4 rounded-lg transition-colors mb-4 ${
            acceptTerms && !loading
              ? 'bg-green-500 text-white hover:bg-green-600'
              : 'bg-gray-400 text-gray-200 cursor-not-allowed'
          }`}
        >
          {loading ? 'Processing Payment...' : acceptTerms ? '✅ Complete Payment (₹299)' : '⚠️ Accept Terms to Continue'}
        </button>

        <p className="text-xs text-gray-500 text-center">
          🔒 Secure payment processing via Razorpay
        </p>
      </div>

      {/* Payment Success Modal */}
      <PaymentSuccessModal
        isOpen={showPaymentSuccess}
        onClose={() => {
          setShowPaymentSuccess(false);
          setCurrentView('home');
        }}
        onViewListings={() => {
          setShowPaymentSuccess(false);
          setCurrentView('my-listings');
        }}
      />
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
    location: []
  });
  const [loading, setLoading] = useState(false);
  const [whatsappAvailable, setWhatsappAvailable] = useState(true);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  
  // Populate phone number from logged-in user
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const tokenPayload = JSON.parse(atob(token.split('.')[1]));
        setFormData(prev => ({
          ...prev,
          phone: tokenPayload.phone_number || ''
        }));
      } catch (e) {
        console.error('Failed to parse token:', e);
      }
    }
  }, []);

  const locationOptions = [
    'Mumbai, Maharashtra',
    'Pune, Maharashtra', 
    'Nagpur, Maharashtra',
    'Nashik, Maharashtra',
    'Alibag, Raigad',
    'Karjat, Raigad',
    'Lonavala, Pune',
    'Kolhapur, Maharashtra',
    'Aurangabad, Maharashtra',
    'Satara, Maharashtra'
  ];

  const handleLocationChange = (location) => {
    setFormData(prev => ({
      ...prev,
      location: prev.location.includes(location)
        ? prev.location.filter(l => l !== location)
        : [...prev.location, location]
    }));
  };

  const addCustomLocation = (customLocation) => {
    if (customLocation && !formData.location.includes(customLocation)) {
      setFormData(prev => ({
        ...prev,
        location: [...prev.location, customLocation]
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Map frontend form fields to backend expected field names
      const brokerData = {
        name: formData.name,
        agency: formData.agency,
        phone_number: formData.phone, // Backend expects phone_number
        email: formData.email,
        location: formData.location.join(', ') // Convert array to string
      };

      await axios.post('/api/broker-signup', brokerData);
      setShowSuccessModal(true);
    } catch (error) {
      alert('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false);
    setCurrentView('home');
  };

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Complete Broker Registration</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Full Name <span className="text-red-500">*</span>
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
                Agency Name <span className="text-red-500">*</span>
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed"
                disabled
              />
              <div className="mt-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={whatsappAvailable}
                    onChange={(e) => setWhatsappAvailable(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-600">This number is available on WhatsApp</span>
                </label>
                {!whatsappAvailable && (
                  <p className="text-sm text-orange-600 mt-1">
                    📱 Please login with your WhatsApp number to receive listing notifications
                  </p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Email <span className="text-red-500">*</span>
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
                Broker Dealer Location (Where you deal in land) <span className="text-red-500">*</span>
              </label>
              <div className="border border-gray-300 rounded-lg p-3 max-h-32 overflow-y-auto">
                {locationOptions.map((location) => (
                  <label key={location} className="flex items-center mb-2 last:mb-0">
                    <input
                      type="checkbox"
                      checked={formData.location.includes(location)}
                      onChange={() => handleLocationChange(location)}
                      className="mr-2"
                    />
                    <span className="text-sm">{location}</span>
                  </label>
                ))}
              </div>
              <div className="mt-2">
                <input
                  type="text"
                  placeholder="Add custom location..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addCustomLocation(e.target.value);
                      e.target.value = '';
                    }
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">Press Enter to add custom location</p>
              </div>
              {formData.location.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-600">Selected: {formData.location.join(', ')}</p>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || formData.location.length === 0}
              className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Registering...' : 'Complete Registration'}
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

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="text-center">
              <div className="mb-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">🎉 Registration successful!</h3>
                <p className="text-gray-600 mb-6">
                  You can now access the broker dashboard and receive notifications for new listings.
                </p>
              </div>
              
              <button
                onClick={handleSuccessModalClose}
                className="w-full bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors font-semibold"
              >
                Continue to Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Broker Dashboard Component
function BrokerDashboard({ user }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRegistered, setIsRegistered] = useState(false);
  const [registrationData, setRegistrationData] = useState({
    name: '',
    agency: '',
    email: '',
    location: ''
  });

  useEffect(() => {
    checkBrokerRegistration();
  }, []);

  const checkBrokerRegistration = async () => {
    console.log('🔍 Starting broker registration check...');
    try {
      // Try to fetch broker profile to see if they're registered
      const response = await axios.get('/api/broker-profile', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      console.log('✅ Broker profile found:', response.data);
      if (response.data && response.data.broker) {
        // Broker is registered, fetch dashboard data
        console.log('Broker is registered, fetching dashboard data...');
        const dashboardResponse = await axios.get('/api/broker-dashboard', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        setLeads(dashboardResponse.data.listings);
        setIsRegistered(true);
        console.log('✅ Dashboard data loaded, broker is registered');
      } else {
        // Broker profile not found, show registration form
        console.log('❌ No broker data in response, showing registration form...');
        setIsRegistered(false);
      }
    } catch (error) {
      console.log('❌ Broker profile check error:', error.response?.status, error.response?.data);
      if (error.response?.status === 404) {
        // Broker not registered, show registration form
        console.log('✅ 404 error - broker not registered, showing registration form');
        setIsRegistered(false);
      } else if (error.response?.status === 403) {
        // User is not a broker
        console.log('❌ 403 error - user is not a broker');
        setIsRegistered(false);
      } else {
        console.error('❌ Failed to check broker registration:', error);
        // For any other error, assume not registered and show form
        console.log('❌ Unknown error, showing registration form as fallback');
        setIsRegistered(false);
      }
    } finally {
      console.log('📋 Setting loading to false, isRegistered state:', !localStorage.getItem('broker-registration-checked'));
      setLoading(false);
    }
  };

  const handleBrokerRegistration = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('🔍 Starting broker registration...');
      console.log('User data:', user);
      console.log('Registration data:', registrationData);
      
      if (!user?.phone_number) {
        throw new Error('Phone number not available. Please login again.');
      }

      const brokerData = {
        name: registrationData.name,
        agency: registrationData.agency,
        phone_number: user.phone_number, // Use phone from authenticated user
        email: registrationData.email,
        location: registrationData.location
      };

      console.log('Sending broker data:', brokerData);

      const response = await axios.post('/api/broker-signup', brokerData);
      console.log('✅ Registration response:', response.data);
      
      alert('Registration successful! You can now access the broker dashboard.');
      setIsRegistered(true);
      checkBrokerRegistration(); // Refresh data
    } catch (error) {
      console.error('❌ Registration error:', error);
      console.error('Error response:', error.response?.data);
      
      let errorMessage = 'Registration failed: ';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage += error.response.data.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
        } else {
          errorMessage += error.response.data.detail;
        }
      } else if (error.message) {
        errorMessage += error.message;
      } else {
        errorMessage += 'Unknown error';
      }
      
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Show registration form if broker is not registered
  if (!isRegistered && !loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Complete Broker Registration</h2>
          <p className="text-gray-600 mb-6">You are logged in as a broker. Please complete your registration to access the dashboard.</p>
          
          <form onSubmit={handleBrokerRegistration} className="space-y-4">
            <div>
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={registrationData.name}
                onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
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
                value={registrationData.agency}
                onChange={(e) => setRegistrationData({...registrationData, agency: e.target.value})}
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
                value={registrationData.email}
                onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
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
                value={registrationData.location}
                onChange={(e) => setRegistrationData({...registrationData, location: e.target.value})}
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
              {loading ? 'Registering...' : 'Complete Registration'}
            </button>
          </form>
        </div>
      </div>
    );
  }

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
                
                <div className="flex gap-3">
                  <button
                    onClick={() => viewListingDetails(listing)}
                    className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => contactOwner(listing)}
                    className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    Contact Owner via WhatsApp
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );

  const viewListingDetails = (listing) => {
    // Create a detailed view modal or navigate to a detailed view
    const detailWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
    detailWindow.document.write(`
      <html>
        <head>
          <title>${listing.title} - Details</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            .header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .detail-row { margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 4px; }
            .label { font-weight: bold; color: #333; }
            .value { color: #666; }
            .description { background: white; padding: 15px; border: 1px solid #ddd; border-radius: 4px; margin: 15px 0; }
            .photos { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0; }
            .photo { width: 100%; height: 200px; object-fit: cover; border-radius: 4px; }
            .maps-link { color: #007bff; text-decoration: none; }
            .maps-link:hover { text-decoration: underline; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>${listing.title}</h1>
            <p><strong>Location:</strong> ${listing.location}</p>
          </div>
          
          <div class="detail-row">
            <span class="label">Area:</span> <span class="value">${listing.area}</span>
          </div>
          
          <div class="detail-row">
            <span class="label">Price:</span> <span class="value">₹${listing.price}</span>
          </div>
          
          <div class="detail-row">
            <span class="label">Status:</span> <span class="value">${listing.status}</span>
          </div>
          
          ${listing.google_maps_link ? `
            <div class="detail-row">
              <span class="label">Location on Maps:</span> 
              <a href="${listing.google_maps_link}" target="_blank" class="maps-link">View on Google Maps</a>
            </div>
          ` : ''}
          
          <div class="description">
            <h3>Description</h3>
            <p>${listing.description}</p>
          </div>
          
          ${listing.photos && listing.photos.length > 0 ? `
            <div>
              <h3>Photos</h3>
              <div class="photos">
                ${listing.photos.map(photo => `<img src="${photo}" alt="Property photo" class="photo" onerror="this.style.display='none'">`).join('')}
              </div>
            </div>
          ` : ''}
          
          ${listing.videos && listing.videos.length > 0 ? `
            <div>
              <h3>Videos</h3>
              ${listing.videos.map(video => `<video src="${video}" controls style="width: 100%; max-width: 400px; height: 300px; margin: 10px 0;"></video>`).join('')}
            </div>
          ` : ''}
          
          <div style="margin-top: 30px; padding: 20px; background: #e3f2fd; border-radius: 8px;">
            <h3>Contact Information</h3>
            <p>To contact the owner, use the WhatsApp button in the main dashboard.</p>
          </div>
        </body>
      </html>
    `);
  };

  const contactOwner = (listing) => {
    const message = `Hi! I'm interested in your land listing: ${listing.title} in ${listing.location}. Can we discuss the details?`;
    const whatsappUrl = `https://wa.me/919876543210?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };
}

// Listings View Component
function ListingsView() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedListing, setSelectedListing] = useState(null);

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

  const openListingModal = (listing) => {
    setSelectedListing(listing);
  };

  const closeModal = () => {
    setSelectedListing(null);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Active Land Listings</h2>
        <p className="text-gray-600">Browse available properties with photos and videos</p>
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
              <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                {/* Main Image */}
                {listing.images && listing.images.length > 0 ? (
                  <div className="relative h-48 bg-gray-200">
                    <img
                      src={getImageSrc(listing.images[0])}
                      alt={listing.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                      📷 {listing.images.length} {listing.videos?.length > 0 && `🎥 ${listing.videos.length}`}
                    </div>
                  </div>
                ) : (
                  <div className="h-48 bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-500">🏞️ No Image</span>
                  </div>
                )}
                
                <div className="p-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2">{listing.title}</h3>
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
                  
                  <p className="text-gray-700 text-sm mb-4 line-clamp-2">{listing.description}</p>
                  
                  <div className="flex justify-between items-center">
                    <button 
                      onClick={() => openListingModal(listing)}
                      className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm"
                    >
                      View Details
                    </button>
                    <div className="text-xs text-gray-500">
                      {listing.images?.length > 0 && `${listing.images.length} photos`}
                      {listing.videos?.length > 0 && ` • ${listing.videos.length} videos`}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Listing Detail Modal */}
      {selectedListing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold text-gray-800">{selectedListing.title}</h2>
                <button
                  onClick={closeModal}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              {/* Images Gallery */}
              {selectedListing.images && selectedListing.images.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">📷 Photos ({selectedListing.images.length})</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {selectedListing.images.map((image, index) => (
                      <img
                        key={index}
                        src={getImageSrc(image)}
                        alt={`${selectedListing.title} - Photo ${index + 1}`}
                        className="w-full h-32 md:h-40 object-cover rounded-lg border"
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Videos Gallery */}
              {selectedListing.videos && selectedListing.videos.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">🎥 Videos ({selectedListing.videos.length})</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedListing.videos.map((video, index) => (
                      <video
                        key={index}
                        src={getImageSrc(video)}
                        controls
                        className="w-full h-48 object-cover rounded-lg border"
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Property Details */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-semibold mb-3">Property Details</h3>
                  <div className="space-y-2">
                    <p><span className="font-semibold">Location:</span> {selectedListing.location}</p>
                    <p><span className="font-semibold">Area:</span> {selectedListing.area}</p>
                    <p><span className="font-semibold">Price:</span> <span className="text-green-600 font-bold">₹{selectedListing.price}</span></p>
                    {selectedListing.latitude && selectedListing.longitude && (
                      <p><span className="font-semibold">Coordinates:</span> {selectedListing.latitude}, {selectedListing.longitude}</p>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-3">Description</h3>
                  <p className="text-gray-700">{selectedListing.description}</p>
                </div>
              </div>

              {/* Contact Section */}
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-green-800 mb-2">Interested in this property?</h3>
                <p className="text-green-700 mb-3">Connect with verified brokers or contact the owner directly</p>
                <div className="flex space-x-4">
                  <button className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors">
                    Contact via WhatsApp
                  </button>
                  <button className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                    Get Broker Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// My Listings Component (Preview Mode)
function MyListings({ user, setCurrentView }) {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedListing, setSelectedListing] = useState(null);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    fetchMyListings();
  }, [user]);

  const getAllMedia = (listing) => {
    const media = [];
    if (listing?.photos) {
      listing.photos.forEach((photo, index) => {
        media.push({ type: 'image', src: photo, index });
      });
    }
    if (listing?.videos) {
      listing.videos.forEach((video, index) => {
        media.push({ type: 'video', src: video, index });
      });
    }
    return media;
  };

  const nextSlide = () => {
    const totalMedia = getAllMedia(selectedListing).length;
    if (totalMedia > 0) {
      setCurrentSlide((prev) => (prev + 1) % totalMedia);
    }
  };

  const prevSlide = () => {
    const totalMedia = getAllMedia(selectedListing).length;
    if (totalMedia > 0) {
      setCurrentSlide((prev) => (prev - 1 + totalMedia) % totalMedia);
    }
  };

  const openListingModal = (listing) => {
    setSelectedListing(listing);
    setCurrentSlide(0);
  };

  const closeModal = () => {
    setSelectedListing(null);
    setCurrentSlide(0);
  };

  const initiatePayment = async (listingId) => {
    setPaymentLoading(true);
    try {
      // Create payment order
      const orderResponse = await axios.post('/api/create-payment-order', {
        amount: 299, // ₹299 
        listing_id: listingId
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      const { order, demo_mode } = orderResponse.data;

      if (demo_mode) {
        // Create a Razorpay-like demo interface
        const demoModal = document.createElement('div');
        demoModal.id = 'razorpay-demo-modal';
        demoModal.innerHTML = `
          <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 8px; padding: 0; width: 400px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
              <div style="background: #528FF0; color: white; padding: 16px 20px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                  <div style="width: 24px; height: 24px; background: white; border-radius: 4px; margin-right: 10px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: #528FF0; font-weight: bold; font-size: 14px;">R</span>
                  </div>
                  <span style="font-weight: 500;">Razorpay Secure (Demo)</span>
                </div>
                <button onclick="document.getElementById('razorpay-demo-modal').remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
              </div>
              <div style="padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                  <h3 style="margin: 0 0 10px 0; color: #333;">Complete Payment</h3>
                  <p style="margin: 0; color: #666; font-size: 14px;">OnlyLands Premium Listing</p>
                </div>
                <div style="display: flex; gap: 10px;">
                  <button onclick="document.getElementById('razorpay-demo-modal').remove()" style="flex: 1; padding: 12px; border: 1px solid #ddd; background: white; color: #666; border-radius: 4px; cursor: pointer;">Cancel</button>
                  <button id="demo-pay-button" style="flex: 2; padding: 12px; background: #528FF0; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">Pay ₹${order.amount / 100}</button>
                </div>
              </div>
            </div>
          </div>
        `;
        
        document.body.appendChild(demoModal);
        
        document.getElementById('demo-pay-button').onclick = async () => {
          try {
            // Simulate payment processing delay
            document.getElementById('demo-pay-button').innerHTML = 'Processing...';
            
            setTimeout(async () => {
              try {
                const demoResponse = {
                  razorpay_order_id: order.id,
                  razorpay_payment_id: `pay_demo_${Date.now()}`,
                  razorpay_signature: `demo_signature_${Date.now()}`
                };

                await axios.post('/api/verify-payment', demoResponse, {
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                  }
                });

                document.getElementById('razorpay-demo-modal').remove();
                alert('Payment Successful! Your listing has been activated.');
                fetchMyListings(); // Refresh listings
                
              } catch (error) {
                document.getElementById('razorpay-demo-modal').remove();
                alert('Payment verification failed: ' + (error.response?.data?.detail || 'Unknown error'));
              }
            }, 2000);
            
          } catch (error) {
            document.getElementById('razorpay-demo-modal').remove();
            alert('Payment processing failed: ' + error.message);
          }
        };
      } else {
        // Handle real Razorpay payment
        const options = {
          key: process.env.REACT_APP_RAZORPAY_KEY_ID,
          amount: order.amount,
          currency: order.currency,
          name: 'OnlyLands',
          description: 'Premium Listing Payment',
          order_id: order.id,
          handler: async function (response) {
            try {
              await axios.post('/api/verify-payment', {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              }, {
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
              });
              
              alert('Payment Successful! Your listing has been activated.');
              fetchMyListings(); // Refresh listings
            } catch (error) {
              alert('Payment verification failed: ' + (error.response?.data?.detail || 'Unknown error'));
            }
          },
          prefill: {
            name: user?.name || '',
            email: user?.email || '',
            contact: user?.phone_number || ''
          },
          theme: {
            color: '#10B981'
          }
        };

        const razorpay = new window.Razorpay(options);
        razorpay.open();
      }
    } catch (error) {
      alert('Payment processing failed: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setPaymentLoading(false);
    }
  };

  const getImageSrc = (imageData) => {
    // Handle local file URLs (starts with /api/uploads/)
    if (typeof imageData === 'string' && imageData.startsWith('/api/uploads/')) {
      return `${process.env.REACT_APP_BACKEND_URL}${imageData}`;
    }
    
    // Handle S3 URLs (string format with https://)
    if (typeof imageData === 'string' && imageData.startsWith('https://')) {
      return imageData;
    }
    
    // Handle base64 format (legacy format)
    if (imageData && imageData.data) {
      return `data:${imageData.content_type};base64,${imageData.data}`;
    }
    
    // Fallback placeholder
    return '/placeholder-land.jpg';
  };

  const fetchMyListings = async () => {
    try {
      const response = await axios.get('/api/my-listings', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setListings(response.data.listings);
    } catch (error) {
      console.error('Failed to fetch my listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'active') {
      return <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">🟢 Active</span>;
    } else if (status === 'pending_payment') {
      return <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">⏳ Pending Payment</span>;
    }
    return <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">{status}</span>;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">My Listings</h1>
              <p className="text-gray-600">View and manage your property listings</p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentView('post-land')}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                + Post New Land
              </button>
              <button
                onClick={() => setCurrentView('home')}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Back to Home
              </button>
            </div>
          </div>
        </div>

        {/* Listings Grid */}
        {loading ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="text-2xl mb-4">⏳</div>
            <p className="text-gray-600">Loading your listings...</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.length === 0 ? (
              <div className="col-span-full bg-white rounded-lg shadow-md p-8 text-center">
                <h3 className="text-xl font-bold text-gray-800 mb-2">No listings yet</h3>
                <p className="text-gray-600 mb-4">Create your first land listing to get started</p>
                <button
                  onClick={() => setCurrentView('post-land')}
                  className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors"
                >
                  Post Your First Land
                </button>
              </div>
            ) : (
              listings.map((listing) => (
                <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                  {/* Status Badge */}
                  <div className="p-4 pb-2">
                    {getStatusBadge(listing.status)}
                  </div>
                  
                  {/* Main Image */}
                  {listing.photos && listing.photos.length > 0 ? (
                    <div className="relative h-48 bg-gray-200">
                      <img
                        src={getImageSrc(listing.photos[0])}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.src = '/placeholder-land.jpg';
                        }}
                      />
                      <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                        📷 {listing.photos.length} {listing.videos?.length > 0 && `🎥 ${listing.videos.length}`}
                      </div>
                    </div>
                  ) : (
                    <div className="h-48 bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-500">🏞️ No Image</span>
                    </div>
                  )}
                  
                  <div className="p-6">
                    <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2">{listing.title}</h3>
                    <div className="space-y-2 text-sm text-gray-600 mb-4">
                      <p>📍 {listing.location}</p>
                      <p>📐 {listing.area}</p>
                      <p className="font-semibold text-green-600 text-lg">💰 ₹{listing.price}</p>
                    </div>
                    
                    <p className="text-gray-700 text-sm mb-4 line-clamp-2">{listing.description}</p>
                    
                    <div className="flex justify-between items-center">
                      <button 
                        onClick={() => openListingModal(listing)}
                        className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm"
                      >
                        View Details
                      </button>
                      <div className="text-xs text-gray-500">
                        {listing.photos?.length > 0 && `${listing.photos.length} photos`}
                        {listing.videos?.length > 0 && ` • ${listing.videos.length} videos`}
                      </div>
                    </div>
                    
                    {/* Payment Notice */}
                    {listing.status === 'pending_payment' && (
                      <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                        <p className="text-yellow-800 text-sm font-semibold">⚠️ Payment Required</p>
                        <p className="text-yellow-700 text-xs mb-3">Complete payment to activate this listing and reach brokers</p>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            initiatePayment(listing.listing_id);
                          }}
                          className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors text-sm font-semibold"
                        >
                          💳 Complete Payment ₹299
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Enhanced Listing Detail Modal */}
        {selectedListing && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex justify-between items-center p-4 border-b">
                <h2 className="text-2xl font-bold text-gray-800">{selectedListing.title}</h2>
                <button
                  onClick={closeModal}
                  className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6">
                {/* Media Slider */}
                <div className="mb-6">
                  {getAllMedia(selectedListing).length > 0 ? (
                    <div className="relative">
                      <div className="relative h-64 md:h-96 bg-gray-200 rounded-lg overflow-hidden">
                        {(() => {
                          const allMedia = getAllMedia(selectedListing);
                          const currentMedia = allMedia[currentSlide];
                          
                          if (!currentMedia) return null;

                          if (currentMedia.type === 'image') {
                            return (
                              <img
                                src={getImageSrc(currentMedia.src)}
                                alt={selectedListing.title}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  e.target.src = '/placeholder-land.jpg';
                                }}
                              />
                            );
                          } else {
                            return (
                              <video
                                src={getImageSrc(currentMedia.src)}
                                controls
                                className="w-full h-full object-cover"
                              >
                                Your browser does not support the video tag.
                              </video>
                            );
                          }
                        })()}
                      </div>

                      {/* Navigation Arrows */}
                      {getAllMedia(selectedListing).length > 1 && (
                        <>
                          <button
                            onClick={prevSlide}
                            className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                          </button>
                          <button
                            onClick={nextSlide}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        </>
                      )}

                      {/* Media Counter */}
                      <div className="absolute bottom-4 right-4 bg-black bg-opacity-60 text-white px-3 py-1 rounded-full text-sm">
                        {currentSlide + 1} / {getAllMedia(selectedListing).length}
                      </div>
                    </div>
                  ) : (
                    <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                      <span className="text-gray-400 text-6xl">🏞️</span>
                    </div>
                  )}
                </div>

                {/* Property Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">Property Details</h3>
                      <div className="space-y-2">
                        <div className="flex items-center text-gray-600">
                          <span className="mr-3 text-lg">📍</span>
                          <span>{selectedListing.location || 'Location not specified'}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="mr-3 text-lg">📏</span>
                          <span>{selectedListing.area}</span>
                        </div>
                        <div className="flex items-center text-green-600 font-bold text-xl">
                          <span className="mr-3 text-lg">💰</span>
                          <span>₹{selectedListing.price}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="mr-3 text-lg">📋</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            selectedListing.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {selectedListing.status === 'active' ? 'Active' : 'Pending Payment'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">Description</h3>
                      <p className="text-gray-600 leading-relaxed">{selectedListing.description}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 mb-2">Media Gallery</h3>
                      <div className="grid grid-cols-3 gap-2">
                        {getAllMedia(selectedListing).map((media, index) => (
                          <div
                            key={index}
                            className={`relative cursor-pointer rounded-lg overflow-hidden ${
                              index === currentSlide ? 'ring-2 ring-blue-500' : ''
                            }`}
                            onClick={() => setCurrentSlide(index)}
                          >
                            {media.type === 'image' ? (
                              <img
                                src={getImageSrc(media.src)}
                                alt={`${selectedListing.title} ${index + 1}`}
                                className="w-full h-16 object-cover"
                              />
                            ) : (
                              <div className="w-full h-16 bg-gray-300 flex items-center justify-center">
                                <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                                </svg>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Payment Status */}
                    {selectedListing.status === 'pending_payment' && (
                      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                        <h3 className="font-semibold text-yellow-800 mb-2">💳 Payment Required</h3>
                        <p className="text-yellow-700 text-sm mb-3">
                          Complete the payment to activate this listing and broadcast it to 1000+ brokers via WhatsApp.
                        </p>
                        <p className="text-yellow-600 text-xs mb-4">
                          Once payment is completed, your listing will be visible to all users and brokers in the marketplace.
                        </p>
                        <button
                          onClick={() => initiatePayment(selectedListing.listing_id)}
                          className="bg-yellow-600 text-white px-6 py-2 rounded-lg hover:bg-yellow-700 transition-colors font-semibold"
                        >
                          💳 Complete Payment - ₹299
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Admin Interface Component
function AdminInterface() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if admin is already logged in
    const token = localStorage.getItem('adminToken');
    if (token) {
      // Verify token is still valid
      verifyToken(token);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (token) => {
    try {
      const response = await axios.get('/api/admin/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 200) {
        setIsAuthenticated(true);
      } else {
        localStorage.removeItem('adminToken');
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('adminToken');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (token) => {
    localStorage.setItem('adminToken', token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-lg">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {isAuthenticated ? (
        <AdminDashboard onLogout={handleLogout} />
      ) : (
        <AdminLogin onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;