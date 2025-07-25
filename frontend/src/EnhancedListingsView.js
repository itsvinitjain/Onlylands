import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EnhancedListingsView = ({ setCurrentView }) => {
  const [listings, setListings] = useState([]);
  const [filteredListings, setFilteredListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [priceRange, setPriceRange] = useState('');
  const [locations, setLocations] = useState([]);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchListings();
  }, []);

  useEffect(() => {
    filterListings();
  }, [searchTerm, selectedLocation, priceRange, listings]);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${backendUrl}/api/listings`);
      const allListings = response.data.listings || [];
      setListings(allListings);
      
      // Extract unique locations for filter
      const uniqueLocations = [...new Set(allListings.map(listing => listing.location || listing.city || 'Unknown'))];
      setLocations(uniqueLocations.filter(loc => loc && loc !== 'Unknown'));
      
    } catch (error) {
      console.error('Error fetching listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterListings = () => {
    let filtered = listings;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(listing =>
        listing.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        listing.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        listing.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        listing.city?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Location filter
    if (selectedLocation) {
      filtered = filtered.filter(listing =>
        listing.location === selectedLocation || listing.city === selectedLocation
      );
    }

    // Price range filter
    if (priceRange) {
      filtered = filtered.filter(listing => {
        const price = parseInt(listing.price.replace(/[^\d]/g, ''));
        switch (priceRange) {
          case 'under-1lac':
            return price < 100000;
          case '1lac-5lac':
            return price >= 100000 && price <= 500000;
          case '5lac-10lac':
            return price >= 500000 && price <= 1000000;
          case 'above-10lac':
            return price > 1000000;
          default:
            return true;
        }
      });
    }

    setFilteredListings(filtered);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedLocation('');
    setPriceRange('');
  };

  const getImageSrc = (imageData) => {
    if (!imageData) return '/placeholder-land.jpg';
    if (typeof imageData === 'string' && imageData.startsWith('https://')) {
      return imageData;
    }
    if (typeof imageData === 'string' && imageData.startsWith('data:')) {
      return imageData;
    }
    if (imageData.s3_url) {
      return imageData.s3_url;
    }
    if (imageData.data) {
      return `data:${imageData.content_type};base64,${imageData.data}`;
    }
    return '/placeholder-land.jpg';
  };

  const openWhatsApp = (phoneNumber) => {
    const message = encodeURIComponent("Hi, I'm interested in your land listing from OnlyLands.");
    window.open(`https://wa.me/${phoneNumber}?text=${message}`, '_blank');
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading listings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Available Land Listings</h1>
            <p className="text-gray-600 mt-2">Browse and search through available properties</p>
          </div>
          <button
            onClick={() => setCurrentView('home')}
            className="mt-4 md:mt-0 bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Back to Home
          </button>
        </div>

        {/* Search and Filter Section */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            {/* Search Bar */}
            <div className="md:col-span-2">
              <input
                type="text"
                placeholder="Search by title, description, or location..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Location Filter */}
            <div>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="">All Locations</option>
                {locations.map((location, index) => (
                  <option key={index} value={location}>{location}</option>
                ))}
              </select>
            </div>

            {/* Price Range Filter */}
            <div>
              <select
                value={priceRange}
                onChange={(e) => setPriceRange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="">All Prices</option>
                <option value="under-1lac">Under ₹1 Lac</option>
                <option value="1lac-5lac">₹1 Lac - ₹5 Lac</option>
                <option value="5lac-10lac">₹5 Lac - ₹10 Lac</option>
                <option value="above-10lac">Above ₹10 Lac</option>
              </select>
            </div>
          </div>

          {/* Filter Summary */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-600">
              Showing {filteredListings.length} of {listings.length} listings
            </span>
            {(searchTerm || selectedLocation || priceRange) && (
              <button
                onClick={clearFilters}
                className="text-sm bg-red-500 text-white px-3 py-1 rounded-full hover:bg-red-600 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Listings Grid */}
      {filteredListings.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏞️</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No listings found</h3>
          <p className="text-gray-500">Try adjusting your search filters or check back later for new listings.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredListings.map((listing) => (
            <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              {/* Image */}
              <div className="h-48 bg-gray-200 overflow-hidden">
                {listing.photos && listing.photos.length > 0 ? (
                  <img
                    src={getImageSrc(listing.photos[0])}
                    alt={listing.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = '/placeholder-land.jpg';
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100">
                    <span className="text-gray-400 text-4xl">🏞️</span>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-lg text-gray-800 mb-2 truncate">{listing.title}</h3>
                
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="mr-2">📍</span>
                    <span>{listing.location || listing.city || 'Location not specified'}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="mr-2">📏</span>
                    <span>{listing.area}</span>
                  </div>
                  
                  <div className="flex items-center text-lg font-bold text-green-600">
                    <span className="mr-2">💰</span>
                    <span>₹{listing.price}</span>
                  </div>
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {listing.description}
                </p>

                {/* Status Badge */}
                <div className="mb-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    listing.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {listing.status === 'active' ? 'Available' : 'Pending'}
                  </span>
                </div>

                {/* Contact Button */}
                <button
                  onClick={() => openWhatsApp(listing.phone_number)}
                  className="w-full bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center"
                >
                  <span className="mr-2">📱</span>
                  Contact Owner
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EnhancedListingsView;