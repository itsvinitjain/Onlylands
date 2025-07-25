import React from 'react';

const LoginChoice = ({ setCurrentView }) => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Choose Login Type</h2>
            <p className="text-gray-600">Select your role to continue</p>
          </div>
          
          <div className="space-y-4">
            <button
              onClick={() => setCurrentView('seller-login')}
              className="w-full bg-green-500 text-white py-4 px-6 rounded-lg hover:bg-green-600 transition-colors text-lg font-semibold"
            >
              🏞️ Login as Seller
              <p className="text-sm font-normal mt-1 opacity-90">Post and manage your land listings</p>
            </button>
            
            <button
              onClick={() => setCurrentView('broker-login')}
              className="w-full bg-blue-500 text-white py-4 px-6 rounded-lg hover:bg-blue-600 transition-colors text-lg font-semibold"
            >
              🤝 Login as Broker
              <p className="text-sm font-normal mt-1 opacity-90">Browse and connect with land owners</p>
            </button>
          </div>
          
          <div className="mt-8 text-center">
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

export default LoginChoice;