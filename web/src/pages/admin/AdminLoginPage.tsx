import type React from "react";
import AdminLogin from "../../components/admin/AdminLogin";

const AdminLoginPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            InstaBids Admin Portal
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            System administration and monitoring
          </p>
        </div>
        <AdminLogin />
      </div>
    </div>
  );
};

export default AdminLoginPage;
