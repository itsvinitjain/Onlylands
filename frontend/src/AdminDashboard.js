import React, { useState, useEffect } from 'react';

const AdminDashboard = ({ onLogout }) => {
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [listings, setListings] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [activeTab, setActiveTab] = useState('stats');
  const [loading, setLoading] = useState(true);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordAction, setPasswordAction] = useState(null);
  const [adminPassword, setAdminPassword] = useState('');
  const [editingListing, setEditingListing] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('adminToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/stats`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchListings = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/listings`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setListings(data.listings);
      }
    } catch (error) {
      console.error('Error fetching listings:', error);
    }
  };

  const fetchBrokers = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/brokers`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setBrokers(data.brokers);
      }
    } catch (error) {
      console.error('Error fetching brokers:', error);
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/payments`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setPayments(data.payments);
      }
    } catch (error) {
      console.error('Error fetching payments:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStats(),
        fetchUsers(),
        fetchListings(),
        fetchBrokers(),
        fetchPayments()
      ]);
      setLoading(false);
    };
    loadData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    onLogout();
  };

  const handleDeleteListing = (listingId) => {
    setPasswordAction({ type: 'delete', listingId });
    setShowPasswordModal(true);
  };

  const handleEditListing = (listing) => {
    setPasswordAction({ type: 'edit', listing });
    setShowPasswordModal(true);
  };

  const executePasswordAction = async () => {
    // Verify admin password (using demo password for now)
    if (adminPassword !== 'admin123') {
      alert('Incorrect admin password!');
      return;
    }

    try {
      if (passwordAction.type === 'delete') {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/delete-listing/${passwordAction.listingId}`, {
          method: 'DELETE',
          headers: getAuthHeaders()
        });

        if (response.ok) {
          alert('Listing deleted successfully!');
          fetchListings(); // Refresh listings
        } else {
          alert('Failed to delete listing');
        }
      } else if (passwordAction.type === 'edit') {
        setEditingListing(passwordAction.listing);
        setShowEditModal(true);
      }
    } catch (error) {
      console.error('Error executing action:', error);
      alert('An error occurred');
    }

    setShowPasswordModal(false);
    setAdminPassword('');
    setPasswordAction(null);
  };

  const handleUpdateListing = async (updatedListing) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/update-listing/${updatedListing.listing_id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updatedListing)
      });

      if (response.ok) {
        alert('Listing updated successfully!');
        fetchListings(); // Refresh listings
        setShowEditModal(false);
        setEditingListing(null);
      } else {
        alert('Failed to update listing');
      }
    } catch (error) {
      console.error('Error updating listing:', error);
      alert('An error occurred while updating');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  const StatCard = ({ title, value, icon, color }) => (
    <div className={`bg-white rounded-lg shadow p-6 border-l-4 ${color}`}>
      <div className="flex items-center">
        <div className="text-3xl mr-4">{icon}</div>
        <div>
          <h3 className="text-lg font-semibold text-gray-700">{title}</h3>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  const DataTable = ({ data, columns, title }) => (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column, index) => (
                <th key={index} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50">
                {columns.map((column, colIndex) => (
                  <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item[column.toLowerCase().replace(' ', '_')] || 'N/A'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-2xl font-bold text-gray-900">OnlyLands Admin Dashboard</h1>
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white shadow">
        <div className="px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['stats', 'users', 'listings', 'brokers', 'payments'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'stats' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard
              title="Total Users"
              value={stats.total_users || 0}
              icon="👥"
              color="border-blue-500"
            />
            <StatCard
              title="Total Listings"
              value={stats.total_listings || 0}
              icon="🏞️"
              color="border-green-500"
            />
            <StatCard
              title="Active Listings"
              value={stats.active_listings || 0}
              icon="✅"
              color="border-green-500"
            />
            <StatCard
              title="Pending Listings"
              value={stats.pending_listings || 0}
              icon="⏳"
              color="border-yellow-500"
            />
            <StatCard
              title="Total Brokers"
              value={stats.total_brokers || 0}
              icon="🤝"
              color="border-purple-500"
            />
            <StatCard
              title="Total Payments"
              value={stats.total_payments || 0}
              icon="💰"
              color="border-green-500"
            />
          </div>
        )}

        {activeTab === 'users' && (
          <DataTable
            data={users}
            columns={['User ID', 'Phone Number', 'User Type', 'Created At']}
            title="All Users"
          />
        )}

        {activeTab === 'listings' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">All Listings</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Area</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {listings.map((listing, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{listing.title || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹{listing.price || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{listing.area || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          listing.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {listing.status || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{listing.created_at || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleEditListing(listing)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteListing(listing.listing_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'brokers' && (
          <DataTable
            data={brokers}
            columns={['Name', 'Agency', 'Phone Number', 'Email', 'Created At']}
            title="All Brokers"
          />
        )}

        {activeTab === 'payments' && (
          <DataTable
            data={payments}
            columns={['Amount', 'Currency', 'Status', 'Created At']}
            title="All Payments"
          />
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;