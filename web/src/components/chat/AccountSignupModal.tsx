import { CheckCircle, Eye, EyeOff, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabase";

interface AccountSignupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (userData: { name: string; email: string; userId: string }) => void;
  projectInfo?: {
    projectType?: string;
    description?: string;
  };
}

export const AccountSignupModal: React.FC<AccountSignupModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  projectInfo,
}) => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      toast.error("Please enter your name");
      return false;
    }

    if (!formData.email.trim()) {
      toast.error("Please enter your email");
      return false;
    }

    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      toast.error("Please enter a valid email address");
      return false;
    }

    if (formData.password.length < 6) {
      toast.error("Password must be at least 6 characters long");
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return false;
    }

    return true;
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsLoading(true);

    try {
      // Create auth user with Supabase
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: {
            full_name: formData.name,
            user_type: "homeowner",
          },
        },
      });

      if (authError) {
        toast.error(`Signup failed: ${authError.message}`);
        return;
      }

      if (!authData.user) {
        toast.error("Signup failed: No user data returned");
        return;
      }

      // Create homeowner profile
      const { error: profileError } = await supabase.from("homeowners").insert({
        user_id: authData.user.id,
        name: formData.name,
        email: formData.email,
        location: "Austin, TX", // Default location - can be updated later
        created_at: new Date().toISOString(),
      });

      if (profileError) {
        console.error("Profile creation error:", profileError);
        // Don't fail the whole signup if profile creation fails
        toast.success("Account created successfully! You may need to complete your profile.");
      } else {
        toast.success("Account created successfully! Welcome to InstaBids!");
      }

      // Call success callback
      onSuccess({
        name: formData.name,
        email: formData.email,
        userId: authData.user.id,
      });

      // Close modal
      onClose();
    } catch (error) {
      console.error("Signup error:", error);
      toast.error("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Create Your InstaBids Account</h2>
              <p className="text-gray-600 mt-1">Start receiving contractor bids for your project</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Project Context */}
        {projectInfo && (
          <div className="p-4 bg-blue-50 border-b border-blue-100">
            <div className="flex items-center gap-2 text-blue-800">
              <CheckCircle className="w-4 h-4" />
              <span className="font-medium">
                Your {projectInfo.projectType || "home"} project is ready!
              </span>
            </div>
            <p className="text-blue-700 text-sm mt-1">
              Create your account to start receiving professional contractor bids.
            </p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSignup} className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="Enter your full name"
              required
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="Enter your email address"
              required
            />
            <p className="text-xs text-gray-500 mt-1">We'll send bid notifications to this email</p>
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                placeholder="Create a secure password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Confirm Password */}
          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Confirm Password
            </label>
            <input
              type={showPassword ? "text" : "password"}
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="Confirm your password"
              required
            />
          </div>

          {/* Terms */}
          <div className="text-xs text-gray-600">
            By creating an account, you agree to InstaBids' Terms of Service and Privacy Policy.
            Your information is secure and will never be shared with third parties.
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Creating Account...
              </div>
            ) : (
              "Create Account & Get Bids"
            )}
          </button>

          {/* Benefits */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="font-medium text-gray-900 mb-2">What happens next:</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Get 3-5 professional contractor bids
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Compare quotes and reviews in one place
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Choose the best contractor for your project
              </li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AccountSignupModal;
