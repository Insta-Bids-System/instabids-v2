import React, { useEffect, useState } from 'react';

// Function to wait for Google Maps places library to be ready
const waitForGooglePlaces = (maxWaitMs = 5000): Promise<void> => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const checkPlaces = () => {
      if (window.google?.maps?.places) {
        resolve();
        return;
      }
      
      if (Date.now() - startTime > maxWaitMs) {
        reject(new Error('Timeout waiting for Google Places library'));
        return;
      }
      
      setTimeout(checkPlaces, 100);
    };
    
    checkPlaces();
  });
};

// Simple function to load Google Maps script
const loadGoogleMapsScript = (apiKey: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (window.google?.maps?.places) {
      resolve();
      return;
    }

    // Check if script already exists
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"][src*="libraries=places"]');
    if (existingScript) {
      // Script exists, wait for places library
      waitForGooglePlaces().then(resolve).catch(reject);
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initGoogleMaps`;
    script.async = true;
    script.defer = true;
    
    // Create a global callback function
    (window as any).initGoogleMaps = () => {
      // Wait for places library to be ready
      waitForGooglePlaces().then(resolve).catch(reject);
    };
    
    script.onerror = () => reject(new Error('Failed to load Google Maps script'));
    
    document.head.appendChild(script);
  });
};

interface AddressInputDebugProps {
  value: string;
  onChange: (address: string) => void;
  placeholder?: string;
  className?: string;
}

const AddressInputDebug: React.FC<AddressInputDebugProps> = ({
  value,
  onChange,
  placeholder = "Enter property address",
  className = ""
}) => {
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [apiKeyStatus, setApiKeyStatus] = useState<string>('');

  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY;
    const logs: string[] = [];
    
    const updateLogs = (newLogs: string[]) => {
      setDebugInfo([...newLogs]);
    };
    
    // Check API key
    if (apiKey) {
      logs.push(`✅ API Key found: ${apiKey.substring(0, 10)}...`);
      setApiKeyStatus(apiKey);
    } else {
      logs.push('❌ API Key is undefined');
      setApiKeyStatus('UNDEFINED');
      updateLogs(logs);
      return;
    }
    
    updateLogs(logs);
    
    // Try to load Google Maps script
    const loadAndTest = async () => {
      logs.push('🔄 Starting Google Maps loading process...');
      updateLogs(logs);
      
      try {
        logs.push('⏳ Waiting for Google Places library to be ready...');
        updateLogs(logs);
        
        await loadGoogleMapsScript(apiKey);
        logs.push('✅ Google Maps and Places library loaded successfully');
        
        // Test what's available
        if (window.google) {
          logs.push('✅ window.google exists');
          
          if (window.google.maps) {
            logs.push('✅ window.google.maps exists');
            
            if (window.google.maps.places) {
              logs.push('✅ window.google.maps.places exists');
              
              if (window.google.maps.places.PlaceAutocompleteElement) {
                logs.push('✅ PlaceAutocompleteElement is available (NEW API)');
              } else {
                logs.push('❌ PlaceAutocompleteElement is NOT available');
              }
              
              if (window.google.maps.places.Autocomplete) {
                logs.push('✅ Legacy Autocomplete exists (OLD API - deprecated but works)');
              } else {
                logs.push('❌ Legacy Autocomplete does NOT exist');
              }
            } else {
              logs.push('❌ window.google.maps.places does NOT exist');
            }
            
            if (window.google.maps.importLibrary) {
              logs.push('✅ importLibrary function exists (NEW API)');
            } else {
              logs.push('❌ importLibrary function does NOT exist (OLD API)');
            }
          } else {
            logs.push('❌ window.google.maps does NOT exist');
          }
        } else {
          logs.push('❌ window.google does NOT exist');
        }
        
      } catch (error) {
        logs.push(`❌ Failed to load Google Maps: ${error}`);
      }
      
      // Check final script state
      const scripts = document.querySelectorAll('script[src*="maps.googleapis.com"]');
      if (scripts.length > 0) {
        logs.push(`📜 Found ${scripts.length} Google Maps script(s) in document`);
      } else {
        logs.push('❌ No Google Maps scripts found in document');
      }
      
      updateLogs(logs);
    };
    
    // Small delay to let the component mount
    setTimeout(loadAndTest, 100);
    
  }, []);

  return (
    <div className="space-y-4">
      <div className="bg-gray-100 p-4 rounded-lg">
        <h3 className="font-bold mb-2">Google Places Debug Info:</h3>
        <div className="text-xs space-y-1 font-mono">
          {debugInfo.map((log, index) => (
            <div key={index} className={log.includes('❌') ? 'text-red-600' : log.includes('⚠️') ? 'text-yellow-600' : 'text-green-600'}>
              {log}
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${className}`}
        />
        <div className="text-xs text-gray-500 mt-1">
          Simple input field (debug mode) - API Key Status: {apiKeyStatus || 'Checking...'}
        </div>
      </div>
    </div>
  );
};

export default AddressInputDebug;