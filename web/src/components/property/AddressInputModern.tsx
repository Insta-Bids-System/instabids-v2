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

interface AddressInputModernProps {
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
  }
}

const AddressInputModern: React.FC<AddressInputModernProps> = ({
  value,
  onChange,
  onEnrichmentData,
  onError,
  placeholder = "Enter property address",
  className = "",
  disabled = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const autocompleteElementRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  // Load Google Maps API with new approach
  useEffect(() => {
    const loadGoogleMaps = async () => {
      if (window.google?.maps) {
        setGoogleLoaded(true);
        return;
      }

      if (document.querySelector('script[src*="maps.googleapis.com"]')) {
        return;
      }

      try {
        const script = document.createElement('script');
        const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY || 'AIzaSyBacJk_H4rpExmLiG1g8-nAGZJbSgC3IaA';
        
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&loading=async`;
        script.async = true;
        script.defer = true;
        
        script.onload = () => {
          setGoogleLoaded(true);
        };
        
        document.head.appendChild(script);
      } catch (error) {
        console.error('Failed to load Google Maps:', error);
        onError?.('Failed to load address suggestions');
      }
    };

    loadGoogleMaps();
  }, [onError]);

  // Initialize the new PlaceAutocompleteElement
  useEffect(() => {
    if (!googleLoaded || !containerRef.current) return;

    const initializeAutocomplete = async () => {
      try {
        // Import the places library with new approach
        await window.google.maps.importLibrary("places");
        
        // Create the new autocomplete element
        const placeAutocomplete = new window.google.maps.places.PlaceAutocompleteElement();
        
        // Configure the autocomplete
        placeAutocomplete.setAttribute('placeholder', placeholder);
        if (value) {
          placeAutocomplete.value = value;
        }

        // Clear container and add the new element
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
          containerRef.current.appendChild(placeAutocomplete);
          autocompleteElementRef.current = placeAutocomplete;
        }

        // Handle place selection
        placeAutocomplete.addEventListener('gmp-select', async ({ placePrediction }: any) => {
          try {
            const place = placePrediction.toPlace();
            await place.fetchFields({ 
              fields: ['displayName', 'formattedAddress', 'location', 'addressComponents'] 
            });
            
            const placeData = place.toJSON();
            onChange(placeData.formattedAddress || placeData.displayName || '');
            
            // Call property enrichment API if available
            if (onEnrichmentData) {
              enrichPropertyData(placeData.formattedAddress, placeData);
            }
          } catch (error) {
            console.error('Error handling place selection:', error);
            onError?.('Error processing selected address');
          }
        });

      } catch (error) {
        console.error('Error initializing PlaceAutocompleteElement:', error);
        onError?.('Failed to initialize address suggestions');
      }
    };

    initializeAutocomplete();
  }, [googleLoaded, placeholder, value, onChange, onEnrichmentData, onError]);

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
          coordinates: place.location ? {
            lat: place.location.lat,
            lng: place.location.lng
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
      <div 
        ref={containerRef}
        className={`w-full min-h-[48px] ${className}`}
        style={{
          display: googleLoaded ? 'block' : 'none'
        }}
      />
      
      {/* Fallback input when Google isn't loaded */}
      {!googleLoaded && (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${className}`}
        />
      )}
      
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

export default AddressInputModern;