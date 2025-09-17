import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { Eye, EyeOff, Check, AlertCircle, Loader2 } from 'lucide-react';

interface SignupData {
  contractor_lead_id: string;
  profile: {
    company_name: string;
    contact_name: string;
    email: string;
    phone: string;
    primary_trade: string;
    years_in_business: number;
    service_areas: string[];
    specializations: string[];
    website: string;
    license_info: string;
    team_size: number;
    differentiators: string;
  };
  expires: string;
}

export default function ContractorSignup() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);
  
  const [signupData, setSignupData] = useState<SignupData | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [passwordStrength, setPasswordStrength] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  });

  useEffect(() => {
    loadSignupData();
  }, [searchParams]);

  useEffect(() => {
    // Check password strength
    setPasswordStrength({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*]/.test(password)
    });
  }, [password]);

  const loadSignupData = async () => {
    try {
      // Check for full data in URL
      const data = searchParams.get('data');
      const sig = searchParams.get('sig');
      
      if (data && sig) {
        // Decode the full data payload
        const decodedData = JSON.parse(atob(data));
        
        // Check expiration
        if (new Date(decodedData.expires) < new Date()) {
          setError('This signup link has expired. Please request a new one.');
          setLoading(false);
          return;
        }
        
        setSignupData(decodedData);
      } else {
        // Try short URL approach
        const id = searchParams.get('id');
        const email = searchParams.get('email');
        
        if (id && email) {
          // Load profile from backend using ID
          const response = await fetch(`/api/coia/landing/profile/${id}`);
          if (response.ok) {
            const profileData = await response.json();
            setSignupData(profileData);
          } else {
            setError('Invalid or expired signup link.');
          }
        } else {
          setError('Invalid signup link. Missing required parameters.');
        }
      }
    } catch (err) {
      console.error('Error loading signup data:', err);
      setError('Failed to load signup information. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!signupData) {
      setError('No signup data available');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!Object.values(passwordStrength).every(v => v)) {
      setError('Password does not meet all requirements');
      return;
    }
    
    setSubmitting(true);
    setError('');
    
    try {
      // Step 1: Create Supabase Auth user
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: signupData.profile.email,
        password: password,
        options: {
          data: {
            company_name: signupData.profile.company_name,
            contact_name: signupData.profile.contact_name,
            role: 'contractor',
            contractor_lead_id: signupData.contractor_lead_id
          }
        }
      });
      
      if (authError) throw authError;
      
      if (!authData.user) {
        throw new Error('Failed to create user account');
      }
      
      // Step 2: Create contractor profile
      const { error: profileError } = await supabase
        .from('contractors')
        .insert({
          user_id: authData.user.id,
          company_name: signupData.profile.company_name,
          contact_name: signupData.profile.contact_name,
          email: signupData.profile.email,
          phone: signupData.profile.phone,
          primary_trade: signupData.profile.primary_trade,
          years_in_business: signupData.profile.years_in_business,
          service_areas: signupData.profile.service_areas,
          specialties: signupData.profile.specializations,
          website: signupData.profile.website,
          license_info: signupData.profile.license_info,
          team_size: signupData.profile.team_size,
          tier: 1, // Default to tier 1 (internal contractor)
          verified: false, // Will be verified by admin
          availability_status: 'available',
          contractor_lead_id: signupData.contractor_lead_id // Link to conversation
        });
      
      if (profileError) throw profileError;
      
      // Step 3: Link conversation memory
      await fetch('/api/coia/link-memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contractor_lead_id: signupData.contractor_lead_id,
          user_id: authData.user.id,
          contractor_email: signupData.profile.email
        })
      });
      
      setSuccess(true);
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate('/contractor/dashboard');
      }, 3000);
      
    } catch (err) {
      console.error('Signup error:', err);
      setError(err instanceof Error ? err.message : 'Failed to create account');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading your signup information...</p>
        </div>
      </div>
    );
  }

  if (error && !signupData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Signup Link Error</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/contractor/contact')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Contact Support
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Account Created Successfully!</h2>
            <p className="text-gray-600 mb-6">
              Welcome to InstaBids, {signupData?.profile.company_name}!
            </p>
            <p className="text-sm text-gray-500">
              Redirecting to your dashboard...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Complete Your Contractor Account</h1>
          <p className="text-gray-600 mb-8">
            Welcome back! We've pre-filled your information from our conversation. 
            Just set your password to activate your account.
          </p>

          {signupData && (
            <div className="bg-blue-50 rounded-lg p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Profile Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Company Name</label>
                  <p className="font-medium">{signupData.profile.company_name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Contact Name</label>
                  <p className="font-medium">{signupData.profile.contact_name || 'Not provided'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Email</label>
                  <p className="font-medium">{signupData.profile.email}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Phone</label>
                  <p className="font-medium">{signupData.profile.phone || 'Not provided'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Primary Trade</label>
                  <p className="font-medium">{signupData.profile.primary_trade || 'Not specified'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Years in Business</label>
                  <p className="font-medium">{signupData.profile.years_in_business || 'Not specified'}</p>
                </div>
              </div>
              {signupData.profile.service_areas?.length > 0 && (
                <div className="mt-4">
                  <label className="text-sm text-gray-600">Service Areas</label>
                  <p className="font-medium">{signupData.profile.service_areas.join(', ')}</p>
                </div>
              )}
              {signupData.profile.specializations?.length > 0 && (
                <div className="mt-4">
                  <label className="text-sm text-gray-600">Specializations</label>
                  <p className="font-medium">{signupData.profile.specializations.join(', ')}</p>
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleSignup} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Create Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter a strong password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Re-enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Password Requirements:</p>
              <div className="space-y-1">
                <div className="flex items-center text-sm">
                  {passwordStrength.length ? (
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 mr-2" />
                  )}
                  <span className={passwordStrength.length ? 'text-green-700' : 'text-gray-600'}>
                    At least 8 characters
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  {passwordStrength.uppercase ? (
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 mr-2" />
                  )}
                  <span className={passwordStrength.uppercase ? 'text-green-700' : 'text-gray-600'}>
                    One uppercase letter
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  {passwordStrength.lowercase ? (
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 mr-2" />
                  )}
                  <span className={passwordStrength.lowercase ? 'text-green-700' : 'text-gray-600'}>
                    One lowercase letter
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  {passwordStrength.number ? (
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 mr-2" />
                  )}
                  <span className={passwordStrength.number ? 'text-green-700' : 'text-gray-600'}>
                    One number
                  </span>
                </div>
                <div className="flex items-center text-sm">
                  {passwordStrength.special ? (
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 mr-2" />
                  )}
                  <span className={passwordStrength.special ? 'text-green-700' : 'text-gray-600'}>
                    One special character (!@#$%^&*)
                  </span>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 text-red-700 p-4 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || !Object.values(passwordStrength).every(v => v) || password !== confirmPassword}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Creating Account...
                </>
              ) : (
                'Create My Account'
              )}
            </button>

            <p className="text-center text-sm text-gray-600">
              By creating an account, you agree to InstaBids' {' '}
              <a href="/terms" className="text-blue-600 hover:underline">Terms of Service</a>
              {' '} and {' '}
              <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}