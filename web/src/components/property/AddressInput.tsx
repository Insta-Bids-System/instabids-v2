import React, { useRef, useEffect, useState } from 'react';

interface PropertyEnrichmentData {
  year_built?: number;
  square_feet?: number;
  property_type?: string;
  bedrooms?: number;
  bathrooms?: number;
  lot_size?: number;
  estimated_value?: number;
}

interface AddressInputProps {
  value: string;
  onChange: (address: string) => void;
  onEnrichmentData?: (data: PropertyEnrichmentData) => void;
  onError?: (error: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

declare global {
  interface Window {
    google: any;
    initGooglePlaces: () => void;
  }
}

const AddressInput: React.FC<AddressInputProps> = ({
  value,
  onChange,
  onEnrichmentData,
  onError,
  placeholder = "Enter property address",
  className = "",
  disabled = false
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  // Load Google Places API
  useEffect(() => {
    const loadGooglePlaces = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        setGoogleLoaded(true);
        return;
      }

      if (document.querySelector('script[src*="maps.googleapis.com"]')) {
        return;
      }

      const script = document.createElement('script');
      const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY || 'AIzaSyBacJk_H4rpExmLiG1g8-nAGZJbSgC3IaA';
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=initGooglePlaces`;
      script.async = true;
      script.defer = true;
      
      window.initGooglePlaces = () => {
        setGoogleLoaded(true);
      };

      document.head.appendChild(script);
    };

    loadGooglePlaces();
  }, []);

  // Initialize autocomplete when Google is loaded
  useEffect(() => {
    if (!googleLoaded || !inputRef.current) return;

    const autocomplete = new window.google.maps.places.Autocomplete(inputRef.current, {
      types: ['address'],
      componentRestrictions: { country: 'us' },
      fields: ['address_components', 'formatted_address', 'geometry', 'place_id']
    });

    autocompleteRef.current = autocomplete;

    const handlePlaceSelect = () => {
      const place = autocomplete.getPlace();
      
      if (!place.formatted_address) {
        onError?.('Please select a valid address from the dropdown');
        return;
      }

      onChange(place.formatted_address);
      
      // Call property enrichment API
      enrichPropertyData(place.formatted_address, place);
    };

    autocomplete.addListener('place_changed', handlePlaceSelect);

    return () => {
      if (autocompleteRef.current) {
        window.google.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [googleLoaded, onChange, onError]);

  const enrichPropertyData = async (address: string, place: any) => {
    if (!onEnrichmentData) return;

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/properties/enrich', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: address,
          place_id: place.place_id,
          coordinates: place.geometry?.location ? {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng()
          } : null
        }),
      });

      if (response.ok) {
        const enrichmentData = await response.json();
        onEnrichmentData(enrichmentData);
      } else {
        console.warn('Property enrichment failed, continuing without enriched data');
      }
    } catch (error) {
      console.warn('Property enrichment error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled || !googleLoaded}
        className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${className}`}
      />
      
      {!googleLoaded && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
        </div>
      )}
      
      {isLoading && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
        </div>
      )}
      
      <div className="text-xs text-gray-500 mt-1">
        {!googleLoaded ? 'Loading address suggestions...' : 'Start typing to search addresses'}
      </div>
    </div>
  );
};

export default AddressInput;