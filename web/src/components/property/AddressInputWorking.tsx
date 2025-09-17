import React, { useRef, useEffect, useState } from 'react';

interface AddressInputWorkingProps {
  value: string;
  onChange: (address: string) => void;
  placeholder?: string;
  className?: string;
}

declare global {
  interface Window {
    google: any;
    initGoogleMaps: () => void;
  }
}

const AddressInputWorking: React.FC<AddressInputWorkingProps> = ({
  value,
  onChange,
  placeholder = "Enter property address",
  className = ""
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<any>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('Initializing...');

  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY;
    
    if (!apiKey) {
      setLoadingStatus('❌ No API key found');
      return;
    }

    setLoadingStatus('🔄 Loading Google Maps...');

    // Set up global callback
    window.initGoogleMaps = () => {
      setLoadingStatus('⏳ Initializing Places...');
      
      // Wait a bit for places library to be ready
      setTimeout(() => {
        if (window.google?.maps?.places?.Autocomplete && inputRef.current) {
          try {
            // Use the legacy Autocomplete (which works with existing keys)
            autocompleteRef.current = new window.google.maps.places.Autocomplete(inputRef.current, {
              types: ['address']
            });

            autocompleteRef.current.addListener('place_changed', () => {
              const place = autocompleteRef.current.getPlace();
              if (place.formatted_address) {
                onChange(place.formatted_address);
                setLoadingStatus('✅ Address autocomplete ready');
              }
            });

            setIsLoaded(true);
            setLoadingStatus('✅ Google Places ready');
          } catch (error) {
            setLoadingStatus(`❌ Error: ${error}`);
          }
        } else {
          setLoadingStatus('❌ Places library not available');
        }
      }, 500);
    };

    // Load script
    const existingScript = document.getElementById('google-maps-script');
    if (!existingScript) {
      const script = document.createElement('script');
      script.id = 'google-maps-script';
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initGoogleMaps`;
      script.async = true;
      script.defer = true;
      
      script.onerror = () => setLoadingStatus('❌ Failed to load script');
      
      document.head.appendChild(script);
    } else if (window.google?.maps?.places) {
      // Already loaded
      window.initGoogleMaps();
    }

    return () => {
      if (autocompleteRef.current) {
        window.google?.maps?.event?.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [onChange]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        placeholder={placeholder}
        className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${className}`}
      />
      <div className="text-xs text-gray-600">
        Status: {loadingStatus}
      </div>
    </div>
  );
};

export default AddressInputWorking;