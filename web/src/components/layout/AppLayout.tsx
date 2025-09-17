import React from 'react';
import { Outlet } from 'react-router-dom';
import AuthStatus from '@/components/AuthStatus';

const AppLayout: React.FC = () => {
  console.log("[AppLayout] Rendering AppLayout component");
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Unified Header for App Pages */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Brand */}
            <div className="flex items-center">
              <div className="text-2xl font-bold text-primary-600">
                InstaBids
              </div>
            </div>

            {/* Right: Auth Status (Google profile/login) */}
            <div className="flex items-center">
              <AuthStatus />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area - renders child routes */}
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;