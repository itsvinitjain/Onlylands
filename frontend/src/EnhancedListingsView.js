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
  const [selectedListing, setSelectedListing] = useState(null);
  const [currentSlide, setCurrentSlide] = useState(0);

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

  const openWhatsApp = (phoneNumber) => {
    if (!phoneNumber) {
      alert('Contact information not available for this listing.');
      return;
    }
    
    // Clean phone number - remove all non-digits and ensure it starts with country code
    const cleanedNumber = phoneNumber.replace(/\D/g, '');
    let formattedNumber = cleanedNumber;
    
    // If number doesn't start with country code, add +91 for India
    if (!cleanedNumber.startsWith('91') && cleanedNumber.length === 10) {
      formattedNumber = '91' + cleanedNumber;
    }
    
    const message = encodeURIComponent("Hi, I'm interested in your land listing on OnlyLands. Could you please provide more details?");
    const whatsappUrl = `whatsapp://send?phone=${formattedNumber}&text=${message}`;
    
    // Try to open WhatsApp app first, fallback to web version
    const link = document.createElement('a');
    link.href = whatsappUrl;
    link.click();
    
    // If WhatsApp app doesn't open, provide fallback
    setTimeout(() => {
      const webFallback = `https://wa.me/${formattedNumber}?text=${message}`;
      if (!confirm('If WhatsApp app didn\'t open, click OK to open in browser:')) return;
      window.open(webFallback, '_blank');
    }, 1000);
  };

  const openDetailModal = (listing) => {
    setSelectedListing(listing);
    setCurrentSlide(0);
  };

  const closeDetailModal = () => {
    setSelectedListing(null);
    setCurrentSlide(0);
  };

  const nextSlide = () => {
    const totalMedia = (selectedListing?.photos?.length || 0) + (selectedListing?.videos?.length || 0);
    if (totalMedia > 0) {
      setCurrentSlide((prev) => (prev + 1) % totalMedia);
    }
  };

  const prevSlide = () => {
    const totalMedia = (selectedListing?.photos?.length || 0) + (selectedListing?.videos?.length || 0);
    if (totalMedia > 0) {
      setCurrentSlide((prev) => (prev - 1 + totalMedia) % totalMedia);
    }
  };

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
            <div key={listing.listing_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer" onClick={() => openDetailModal(listing)}>
              {/* Image Slider */}
              <div className="relative h-48 bg-gray-200 overflow-hidden">
                {listing.photos && listing.photos.length > 0 ? (
                  <div className="relative w-full h-full">
                    <img
                      src={getImageSrc(listing.photos[0])}
                      alt={listing.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = '/placeholder-land.jpg';
                      }}
                    />
                    {/* Media Counter */}
                    {(listing.photos?.length > 1 || listing.videos?.length > 0) && (
                      <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white px-2 py-1 rounded-full text-xs">
                        {(listing.photos?.length || 0) + (listing.videos?.length || 0)} media
                      </div>
                    )}
                    {/* Play icon for videos */}
                    {listing.videos && listing.videos.length > 0 && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="bg-black bg-opacity-50 text-white p-3 rounded-full">
                          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
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

                <div className="text-gray-600 text-sm mb-4">
                  <div 
                    className="line-clamp-3 whitespace-pre-wrap"
                    style={{
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      lineHeight: '1.5',
                      maxHeight: '4.5em'
                    }}
                  >
                    {listing.description}
                  </div>
                </div>

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
                  onClick={(e) => {
                    e.stopPropagation();
                    openWhatsApp(listing.phone_number);
                  }}
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

      {/* Detailed Modal */}
      {selectedListing && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-2xl font-bold text-gray-800">{selectedListing.title}</h2>
              <button
                onClick={closeDetailModal}
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
                        <span>{selectedListing.location || selectedListing.city || 'Location not specified'}</span>
                      </div>
                      {selectedListing.google_maps_link && (
                        <div className="flex items-center text-blue-600">
                          <span className="mr-3 text-lg">🗺️</span>
                          <a
                            href={selectedListing.google_maps_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            View on Google Maps
                          </a>
                        </div>
                      )}
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
                          {selectedListing.status === 'active' ? 'Available' : 'Pending'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">Description</h3>
                    <div 
                      className="text-gray-600 leading-relaxed whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500"
                      style={{
                        fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
                        fontSize: '14px',
                        lineHeight: '1.6',
                        maxHeight: '300px',
                        overflowY: 'auto'
                      }}
                    >
                      {selectedListing.description}
                    </div>
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

                  <div className="pt-4">
                    <button
                      onClick={() => openWhatsApp(selectedListing.phone_number)}
                      className="w-full bg-green-500 text-white py-3 px-6 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center text-lg font-semibold"
                    >
                      <span className="mr-3">📱</span>
                      Contact Owner via WhatsApp
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedListingsView;