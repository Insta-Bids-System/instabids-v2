import type React from "react";
import { useState } from "react";
import AddressInputSimple from "./AddressInputSimple";

interface PropertyCreatorProps {
  onSubmit: (propertyData: {
    name: string;
    address?: string;
    street_address?: string;
    city?: string;
    zip_code?: string;
    square_feet?: number;
    year_built?: number;
    property_type: string;
    ownership_status?: string;
    rooms?: RoomSelection[];
  }) => void;
  onCancel: () => void;
}

interface RoomSelection {
  type: string;
  count: number;
}


const PropertyCreator: React.FC<PropertyCreatorProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: "",
    street_address: "",
    city: "",
    zip_code: "",
    square_feet: "",
    year_built: "",
    property_type: "single_family",
    ownership_status: "owned",
  });

  const [roomCounts, setRoomCounts] = useState({
    living_room: 0,
    dining_room: 0,
    kitchen: 0,
    bedroom: 0,
    bathroom: 0,
    garage: 0,
    basement: 0,
    laundry: 0,
    office: 0,
    front_yard: 0,
    backyard: 0,
    patio: 0,
    deck: 0,
    other: 0
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const parseAddress = (fullAddress: string) => {
    if (!fullAddress.trim()) {
      return {
        street_address: undefined,
        city: undefined,
        zip_code: undefined
      };
    }

    // Basic address parsing - looks for patterns like:
    // "123 Main St, City, State 12345" or "123 Main St City State 12345"
    const addressParts = fullAddress.split(',').map(part => part.trim());
    
    if (addressParts.length >= 3) {
      // Format: "123 Main St, City, State 12345"
      const street_address = addressParts[0];
      const city = addressParts[1];
      const stateZip = addressParts[2];
      
      // Extract zip code from state/zip part
      const zipMatch = stateZip.match(/\b\d{5}(-\d{4})?\b/);
      const zip_code = zipMatch ? zipMatch[0] : undefined;
      
      return { street_address, city, zip_code };
    } else if (addressParts.length === 2) {
      // Format: "123 Main St, City State 12345"
      const street_address = addressParts[0];
      const cityStateZip = addressParts[1];
      
      // Try to extract zip and work backwards
      const zipMatch = cityStateZip.match(/\b\d{5}(-\d{4})?\b/);
      if (zipMatch) {
        const zip_code = zipMatch[0];
        const beforeZip = cityStateZip.substring(0, zipMatch.index).trim();
        // Assume city is everything before the last word (state)
        const parts = beforeZip.split(' ');
        const city = parts.length > 1 ? parts.slice(0, -1).join(' ') : parts[0];
        
        return { street_address, city, zip_code };
      } else {
        return { street_address, city: cityStateZip, zip_code: undefined };
      }
    } else {
      // Single part - try to extract what we can
      const zipMatch = fullAddress.match(/\b\d{5}(-\d{4})?\b/);
      if (zipMatch) {
        const zip_code = zipMatch[0];
        const withoutZip = fullAddress.replace(zipMatch[0], '').trim();
        return { street_address: withoutZip, city: undefined, zip_code };
      } else {
        return { street_address: fullAddress, city: undefined, zip_code: undefined };
      }
    }
  };

  const handleRoomCountChange = (roomType: string, count: number) => {
    setRoomCounts(prev => ({
      ...prev,
      [roomType]: Math.max(0, count)
    }));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Property name is required";
    }

    if (formData.square_feet && isNaN(Number(formData.square_feet))) {
      newErrors.square_feet = "Square feet must be a number";
    }

    if (formData.year_built && (isNaN(Number(formData.year_built)) || Number(formData.year_built) < 1800 || Number(formData.year_built) > 2030)) {
      newErrors.year_built = "Year built must be between 1800 and 2030";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Convert room counts to room selections array
    const rooms: RoomSelection[] = Object.entries(roomCounts)
      .filter(([_, count]) => count > 0)
      .map(([type, count]) => ({ type, count }));

    // Build full address from components for backward compatibility
    const fullAddress = [formData.street_address, formData.city, formData.zip_code]
      .filter(Boolean)
      .join(", ");

    const propertyData = {
      name: formData.name.trim(),
      address: fullAddress || undefined,
      street_address: formData.street_address.trim() || undefined,
      city: formData.city.trim() || undefined,
      zip_code: formData.zip_code.trim() || undefined,
      square_feet: formData.square_feet ? Number(formData.square_feet) : undefined,
      year_built: formData.year_built ? Number(formData.year_built) : undefined,
      property_type: formData.property_type,
      ownership_status: formData.ownership_status,
      rooms: rooms.length > 0 ? rooms : undefined
    };

    onSubmit(propertyData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Add New Property</h2>
            <p className="text-gray-600 mt-1">
              Fill in your property details below
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Property Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Property Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="e.g., Main House, Rental Property #1"
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                errors.name ? "border-red-500" : "border-gray-300"
              }`}
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          {/* Address Components */}
          <div className="space-y-4">
            <div>
              <label htmlFor="street_address" className="block text-sm font-medium text-gray-700 mb-2">
                Street Address
              </label>
              <input
                type="text"
                id="street_address"
                name="street_address"
                value={formData.street_address || ""}
                onChange={handleInputChange}
                placeholder="e.g., 123 Main Street"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.street_address ? "border-red-500" : "border-gray-300"
                }`}
              />
              {errors.street_address && <p className="text-red-500 text-sm mt-1">{errors.street_address}</p>}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
                  City
                </label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={formData.city || ""}
                  onChange={handleInputChange}
                  placeholder="e.g., Miami"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    errors.city ? "border-red-500" : "border-gray-300"
                  }`}
                />
                {errors.city && <p className="text-red-500 text-sm mt-1">{errors.city}</p>}
              </div>
              
              <div>
                <label htmlFor="zip_code" className="block text-sm font-medium text-gray-700 mb-2">
                  ZIP Code
                </label>
                <input
                  type="text"
                  id="zip_code"
                  name="zip_code"
                  value={formData.zip_code || ""}
                  onChange={handleInputChange}
                  placeholder="e.g., 33101"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    errors.zip_code ? "border-red-500" : "border-gray-300"
                  }`}
                />
                {errors.zip_code && <p className="text-red-500 text-sm mt-1">{errors.zip_code}</p>}
              </div>
            </div>
          </div>

          {/* Property Type and Ownership Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="property_type" className="block text-sm font-medium text-gray-700 mb-2">
                Property Type
              </label>
              <select
                id="property_type"
                name="property_type"
                value={formData.property_type}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="single_family">Single Family Home</option>
                <option value="condo">Condominium</option>
                <option value="townhouse">Townhouse</option>
                <option value="duplex">Duplex</option>
                <option value="apartment">Apartment</option>
                <option value="commercial">Commercial Property</option>
              </select>
            </div>

            <div>
              <label htmlFor="ownership_status" className="block text-sm font-medium text-gray-700 mb-2">
                Ownership Status
              </label>
              <select
                id="ownership_status"
                name="ownership_status"
                value={formData.ownership_status}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="owned">Owned</option>
                <option value="rented">Rented</option>
                <option value="managed">Managed</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Square Feet */}
            <div>
              <label htmlFor="square_feet" className="block text-sm font-medium text-gray-700 mb-2">
                Square Feet
              </label>
              <input
                type="number"
                id="square_feet"
                name="square_feet"
                value={formData.square_feet}
                onChange={handleInputChange}
                placeholder="e.g., 2000"
                min="0"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.square_feet ? "border-red-500" : "border-gray-300"
                }`}
              />
              {errors.square_feet && <p className="text-red-500 text-sm mt-1">{errors.square_feet}</p>}
            </div>

            {/* Year Built */}
            <div>
              <label htmlFor="year_built" className="block text-sm font-medium text-gray-700 mb-2">
                Year Built
              </label>
              <input
                type="number"
                id="year_built"
                name="year_built"
                value={formData.year_built}
                onChange={handleInputChange}
                placeholder="e.g., 1995"
                min="1800"
                max="2030"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.year_built ? "border-red-500" : "border-gray-300"
                }`}
              />
              {errors.year_built && <p className="text-red-500 text-sm mt-1">{errors.year_built}</p>}
            </div>
          </div>

          {/* Room and Area Selection */}
          <div className="space-y-4">
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Room & Area Counts</h3>
              <p className="text-sm text-gray-600 mb-4">
                Specify the number of each room type in your property
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Object.entries(roomCounts).map(([roomType, count]) => (
                  <div key={roomType} className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 capitalize">
                      {roomType.replace('_', ' ')}
                    </label>
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => handleRoomCountChange(roomType, count - 1)}
                        className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={count <= 0}
                      >
                        -
                      </button>
                      <span className="w-8 text-center font-medium">{count}</span>
                      <button
                        type="button"
                        onClick={() => handleRoomCountChange(roomType, count + 1)}
                        className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        +
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Property
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PropertyCreator;