import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Building2, MapPin, Briefcase, Clock, Shield, 
  Search, CheckCircle, AlertCircle, ChevronRight 
} from 'lucide-react';
import { useSupabase } from '@/contexts/SupabaseContext';
import { api } from '@/services/api';

interface ProfileStep {
  id: string;
  title: string;
  icon: React.ReactNode;
  component: React.ReactNode;
  required: boolean;
}

export const ContractorProfileBuilder: React.FC = () => {
  const { user } = useSupabase();
  const [currentStep, setCurrentStep] = useState(0);
  const [profileData, setProfileData] = useState<any>({});
  const [isResearching, setIsResearching] = useState(false);
  const [researchResults, setResearchResults] = useState<any>(null);
  const [completeness, setCompleteness] = useState(0);

  // Auto-research when company name and location are provided
  const triggerResearch = async (companyName: string, location: string) => {
    setIsResearching(true);
    try {
      const response = await api.request('/api/coia/research', {
        method: 'POST',
        body: JSON.stringify({ company_name: companyName, location })
      });
      
      if (response.data) {
        setResearchResults(response.data);
        // Auto-fill profile with researched data
        setProfileData(prev => ({
          ...prev,
          website: response.data.website,
          phone: response.data.phone,
          address: response.data.address,
          google_rating: response.data.rating,
          google_reviews_count: response.data.reviews_count
        }));
      }
    } catch (error) {
      console.error('Research failed:', error);
    } finally {
      setIsResearching(false);
    }
  };

  // Business Verification Step
  const BusinessVerification = () => {
    const [companyName, setCompanyName] = useState(profileData.company_name || '');
    const [location, setLocation] = useState(profileData.location || '');

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold mb-4">Let's verify your business</h3>
          <p className="text-gray-600 mb-6">
            I'll search for your business information to speed up the process
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Turf Grass Artificial Solutions"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., South Florida"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={() => triggerResearch(companyName, location)}
            disabled={!companyName || !location || isResearching}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isResearching ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                Searching for your business...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Search & Verify Business
              </>
            )}
          </button>
        </div>

        {researchResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg"
          >
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
              <div className="flex-1">
                <h4 className="font-semibold text-green-900">Found your business!</h4>
                <div className="mt-2 space-y-2 text-sm">
                  {researchResults.website && (
                    <div>Website: <a href={`https://${researchResults.website}`} target="_blank" className="text-blue-600 hover:underline">{researchResults.website}</a></div>
                  )}
                  {researchResults.phone && <div>Phone: {researchResults.phone}</div>}
                  {researchResults.address && <div>Address: {researchResults.address}</div>}
                  {researchResults.rating && (
                    <div>Google Rating: {researchResults.rating} ⭐ ({researchResults.reviews_count} reviews)</div>
                  )}
                </div>
                <button
                  onClick={() => {
                    setProfileData(prev => ({ ...prev, ...researchResults, company_name: companyName, location }));
                    setCurrentStep(1);
                  }}
                  className="mt-3 text-green-700 font-medium hover:underline"
                >
                  Looks good, continue →
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    );
  };

  // Service Area Configuration Step
  const ServiceAreaConfig = () => {
    const [radius, setRadius] = useState(profileData.service_radius_miles || 25);
    const [zipCodes, setZipCodes] = useState(profileData.zip_codes || []);
    const [newZipCode, setNewZipCode] = useState('');

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold mb-4">Define your service area</h3>
          <p className="text-gray-600 mb-6">
            Where do you provide services? This helps us match you with the right projects.
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Service Radius (miles from {profileData.location || 'your location'})
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="5"
                max="100"
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="flex-1"
              />
              <span className="w-16 text-center font-semibold">{radius} mi</span>
            </div>
            <div className="mt-2 flex gap-2">
              {[10, 25, 50, 100].map(r => (
                <button
                  key={r}
                  onClick={() => setRadius(r)}
                  className={`px-3 py-1 text-sm rounded ${
                    radius === r ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {r} miles
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Specific Zip Codes (optional)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newZipCode}
                onChange={(e) => setNewZipCode(e.target.value)}
                placeholder="Enter zip code"
                className="flex-1 px-4 py-2 border rounded-lg"
                maxLength={5}
              />
              <button
                onClick={() => {
                  if (newZipCode && newZipCode.length === 5) {
                    setZipCodes([...zipCodes, newZipCode]);
                    setNewZipCode('');
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {zipCodes.map((zip, idx) => (
                <span key={idx} className="px-3 py-1 bg-gray-100 rounded-full text-sm flex items-center gap-1">
                  {zip}
                  <button
                    onClick={() => setZipCodes(zipCodes.filter((_, i) => i !== idx))}
                    className="text-gray-500 hover:text-red-500"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm text-blue-900">
            💡 <strong>Smart tip:</strong> Most contractors in {profileData.location || 'your area'} service a 25-30 mile radius. 
            Consider your travel time and fuel costs when setting your range.
          </p>
        </div>
      </div>
    );
  };

  // Service Expertise Step - Focused on capabilities, not pricing
  const ServiceExpertise = () => {
    const mainCategories = {
      'Artificial Turf': [
        'Residential lawns',
        'Pet-friendly installations',
        'Putting greens',
        'Sports fields',
        'Commercial properties',
        'Playground surfaces'
      ],
      'Landscaping': [
        'Xeriscaping',
        'Tropical landscapes',
        'Modern/minimalist',
        'Native plants',
        'Water features',
        'Rock gardens'
      ],
      'Specialized Services': [
        'Drainage solutions',
        'Erosion control',
        'Outdoor lighting',
        'Irrigation systems',
        'Hardscaping',
        'Retaining walls'
      ]
    };

    const [selectedMain, setSelectedMain] = useState<string[]>(profileData.main_services || []);
    const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>(profileData.specialties || []);
    const [certifications, setCertifications] = useState(profileData.certifications || []);
    const [newCert, setNewCert] = useState('');

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold mb-4">What's your expertise?</h3>
          <p className="text-gray-600 mb-6">
            Help us understand your specializations so we can match you with the right projects.
          </p>
        </div>

        {/* Main Services */}
        <div>
          <label className="block text-sm font-medium mb-3">Primary Services</label>
          <div className="space-y-4">
            {Object.entries(mainCategories).map(([category, specialties]) => (
              <div key={category} className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <input
                    type="checkbox"
                    checked={selectedMain.includes(category)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMain([...selectedMain, category]);
                      } else {
                        setSelectedMain(selectedMain.filter(s => s !== category));
                        // Also remove specialties if main category unchecked
                        setSelectedSpecialties(selectedSpecialties.filter(s => !specialties.includes(s)));
                      }
                    }}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="font-medium">{category}</span>
                </div>
                
                {selectedMain.includes(category) && (
                  <div className="ml-6 grid grid-cols-2 gap-2">
                    {specialties.map(specialty => (
                      <label key={specialty} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={selectedSpecialties.includes(specialty)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSpecialties([...selectedSpecialties, specialty]);
                            } else {
                              setSelectedSpecialties(selectedSpecialties.filter(s => s !== specialty));
                            }
                          }}
                          className="w-3 h-3"
                        />
                        <span>{specialty}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Certifications & Training */}
        <div>
          <label className="block text-sm font-medium mb-3">
            Certifications & Special Training
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newCert}
              onChange={(e) => setNewCert(e.target.value)}
              placeholder="e.g., SynLawn Certified Installer"
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            <button
              onClick={() => {
                if (newCert) {
                  setCertifications([...certifications, newCert]);
                  setNewCert('');
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {certifications.map((cert, idx) => (
              <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                {cert}
                <button
                  onClick={() => setCertifications(certifications.filter((_, i) => i !== idx))}
                  className="text-green-600 hover:text-red-500 ml-1"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Team Capabilities */}
        <div>
          <label className="block text-sm font-medium mb-3">Team Capabilities</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-600">Crew Size</label>
              <select className="w-full px-4 py-2 border rounded-lg">
                <option>Solo operator</option>
                <option>2-3 person crew</option>
                <option>4-6 person crew</option>
                <option>7-10 person crew</option>
                <option>10+ person crew</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-600">Typical Project Duration</label>
              <select className="w-full px-4 py-2 border rounded-lg">
                <option>Same day</option>
                <option>1-2 days</option>
                <option>3-5 days</option>
                <option>1-2 weeks</option>
                <option>2+ weeks</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Define profile steps
  const steps: ProfileStep[] = [
    {
      id: 'business',
      title: 'Business Verification',
      icon: <Building2 className="w-5 h-5" />,
      component: <BusinessVerification />,
      required: true
    },
    {
      id: 'service_area',
      title: 'Service Area',
      icon: <MapPin className="w-5 h-5" />,
      component: <ServiceAreaConfig />,
      required: true
    },
    {
      id: 'expertise',
      title: 'Expertise & Capabilities',
      icon: <Briefcase className="w-5 h-5" />,
      component: <ServiceExpertise />,
      required: true
    }
  ];

  // Calculate profile completeness
  useEffect(() => {
    const fields = [
      'company_name', 'location', 'website', 'phone',
      'service_radius_miles', 'specialties'
    ];
    const filled = fields.filter(f => profileData[f]).length;
    setCompleteness(Math.round((filled / fields.length) * 100));
  }, [profileData]);

  // Save profile data
  const saveProfile = async () => {
    try {
      await api.request('/api/coia/profile/progressive', {
        method: 'POST',
        body: JSON.stringify({
          contractor_id: user?.id,
          step: steps[currentStep].id,
          data: profileData
        })
      });
    } catch (error) {
      console.error('Failed to save profile:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Complete Your Contractor Profile</h2>
          <div className="text-sm text-gray-600">
            {completeness}% Complete
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${completeness}%` }}
          />
        </div>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, idx) => (
          <div key={step.id} className="flex items-center">
            <div className={`
              flex items-center justify-center w-10 h-10 rounded-full
              ${idx <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
            `}>
              {idx < currentStep ? <CheckCircle className="w-5 h-5" /> : step.icon}
            </div>
            <span className={`ml-2 text-sm ${idx <= currentStep ? 'text-gray-900' : 'text-gray-500'}`}>
              {step.title}
            </span>
            {idx < steps.length - 1 && (
              <ChevronRight className="mx-2 text-gray-400" />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {steps[currentStep].component}
          </motion.div>
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="mt-8 flex justify-between">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="px-6 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => {
              saveProfile();
              if (currentStep < steps.length - 1) {
                setCurrentStep(currentStep + 1);
              }
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {currentStep === steps.length - 1 ? 'Complete Profile' : 'Next Step'}
          </button>
        </div>
      </div>

      {/* COIA Helper */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white font-bold">IA</span>
          </div>
          <div className="flex-1">
            <p className="text-sm text-blue-900">
              <strong>Intelligent Assistant:</strong> {' '}
              {currentStep === 0 && "I'll search for your business information to save you time!"}
              {currentStep === 1 && `Based on your location in ${profileData.location || 'your area'}, most contractors service a 25-30 mile radius.`}
              {currentStep === 2 && "Select all services you offer. The more specific, the better matches you'll receive."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};