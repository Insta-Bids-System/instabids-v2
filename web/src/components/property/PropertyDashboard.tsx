import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";
import PropertyCreator from "./PropertyCreator";
import PropertyView from "./PropertyView";
import FloatingIrisChat from "../unified/FloatingIrisChat";

export interface Property {
  id: string;
  user_id: string;
  name: string;
  address?: string;
  square_feet?: number;
  year_built?: number;
  property_type: string;
  cover_photo_url?: string;
  metadata: any;
  created_at: string;
  updated_at: string;
}

export interface PropertyRoom {
  id: string;
  property_id: string;
  name: string;
  room_type: string;
  floor_level: number;
  approximate_sqft?: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyAsset {
  id: string;
  property_id: string;
  room_id?: string;
  asset_type: string;
  category: string;
  name?: string;
  brand?: string;
  model_number?: string;
  color_finish?: string;
  status: string;
  created_at: string;
}

const PropertyDashboard: React.FC = () => {
  console.log("[PropertyDashboard] Component mounting/rendering");
  const { user } = useAuth();
  console.log("[PropertyDashboard] Auth user:", user);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPropertyCreator, setShowPropertyCreator] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);

  const loadProperties = async () => {
    console.log("[PropertyDashboard] loadProperties called");
    // Check for demo user if no authenticated user
    const demoUser = localStorage.getItem("DEMO_USER");
    const effectiveUserId = user?.id || (demoUser ? JSON.parse(demoUser).id : null);
    console.log("[PropertyDashboard] demoUser:", demoUser);
    console.log("[PropertyDashboard] effectiveUserId:", effectiveUserId);

    if (!effectiveUserId) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`/api/properties/user/${effectiveUserId}`);
      if (response.ok) {
        const data = await response.json();
        console.log("[PropertyDashboard] Loaded properties:", data);
        setProperties(data || []);
      } else {
        console.error("[PropertyDashboard] Failed to load properties");
        toast.error("Failed to load properties");
      }
    } catch (error) {
      console.error("Error loading properties:", error);
      toast.error("Failed to load properties");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProperties();
  }, [user]);

  const handleCreateProperty = async (propertyData: {
    name: string;
    address?: string;
    street_address?: string;
    city?: string;
    zip_code?: string;
    square_feet?: number;
    year_built?: number;
    property_type: string;
    ownership_status?: string;
    rooms?: {type: string; count: number}[];
  }) => {
    // Check for demo user if no authenticated user
    const demoUser = localStorage.getItem("DEMO_USER");
    const effectiveUserId = user?.id || (demoUser ? JSON.parse(demoUser).id : null);

    if (!effectiveUserId) return;

    try {
      // Separate rooms from property data
      const { rooms, ...propertyOnlyData } = propertyData;
      
      // Create the property first
      const response = await fetch(`/api/properties/create?user_id=${effectiveUserId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(propertyOnlyData),
      });

      if (response.ok) {
        const newProperty = await response.json();
        console.log("[PropertyDashboard] Created property:", newProperty);
        
        // Create rooms if any were selected
        if (rooms && rooms.length > 0) {
          console.log("[PropertyDashboard] Creating rooms:", rooms);
          for (const room of rooms) {
            // Create multiple rooms of the same type if count > 1
            for (let i = 0; i < room.count; i++) {
              const roomName = room.count > 1 ? 
                `${room.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} ${i + 1}` :
                room.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
              
              const roomData = {
                name: roomName,
                room_type: room.type,
                floor_level: 1,
              };
              
              try {
                const roomResponse = await fetch(`/api/properties/${newProperty.id}/rooms?user_id=${effectiveUserId}`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify(roomData),
                });
                
                if (roomResponse.ok) {
                  console.log(`[PropertyDashboard] Created room: ${roomName}`);
                } else {
                  console.error(`[PropertyDashboard] Failed to create room: ${roomName}`);
                }
              } catch (roomError) {
                console.error(`Error creating room ${roomName}:`, roomError);
              }
            }
          }
        }
        
        setProperties((prev) => [newProperty, ...prev]);
        setShowPropertyCreator(false);
        toast.success(`Property created successfully${rooms && rooms.length > 0 ? ' with rooms!' : '!'}`);
      } else {
        const error = await response.json();
        console.error("[PropertyDashboard] Failed to create property:", error);
        toast.error("Failed to create property");
      }
    } catch (error) {
      console.error("Error creating property:", error);
      toast.error("Failed to create property");
    }
  };

  const handleSelectProperty = (property: Property) => {
    setSelectedProperty(property);
  };

  const handleBackToList = () => {
    setSelectedProperty(null);
  };

  const handleDeleteProperty = async (propertyId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    
    if (!confirm('Are you sure you want to delete this property?')) {
      return;
    }

    try {
      const response = await fetch(`/api/properties/${propertyId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Reload properties after deletion
        await loadProperties();
        toast.success("Property deleted successfully");
      } else {
        console.error('Failed to delete property');
        toast.error('Failed to delete property. Please try again.');
      }
    } catch (error) {
      console.error('Error deleting property:', error);
      toast.error('Error deleting property. Please try again.');
    }
  };

  console.log("[PropertyDashboard] Render logic - loading:", loading, "selectedProperty:", selectedProperty, "showPropertyCreator:", showPropertyCreator, "properties:", properties);

  if (loading) {
    console.log("[PropertyDashboard] Rendering loading state");
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show individual property view
  if (selectedProperty) {
    console.log("[PropertyDashboard] Rendering property view for:", selectedProperty.name);
    return (
      <PropertyView
        property={selectedProperty}
        onBack={handleBackToList}
        onUpdate={loadProperties}
      />
    );
  }

  // Show property creator
  if (showPropertyCreator) {
    console.log("[PropertyDashboard] Rendering property creator");
    return (
      <PropertyCreator
        onSubmit={handleCreateProperty}
        onCancel={() => setShowPropertyCreator(false)}
      />
    );
  }

  // Show properties list
  console.log("[PropertyDashboard] Rendering properties list with", properties.length, "properties");
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Properties</h1>
          <p className="text-gray-600 mt-1">
            Document and manage your properties with AI assistance
          </p>
        </div>
        <button
          onClick={() => setShowPropertyCreator(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Property
        </button>
      </div>

      {properties.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏠</div>
          <h3 className="text-xl font-medium text-gray-900 mb-2">No properties yet</h3>
          <p className="text-gray-600">
            Get started by adding your first property to begin AI-powered documentation and maintenance tracking.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((property) => (
            <div
              key={property.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border"
              onClick={() => handleSelectProperty(property)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {property.name}
                    </h3>
                    {property.address && (
                      <p className="text-gray-600 text-sm mt-1">{property.address}</p>
                    )}
                  </div>
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                    {property.property_type.replace('_', ' ')}
                  </span>
                </div>

                <div className="space-y-2">
                  {property.square_feet && (
                    <div className="text-sm text-gray-600">
                      📐 {property.square_feet.toLocaleString()} sq ft
                    </div>
                  )}
                  {property.year_built && (
                    <div className="text-sm text-gray-600">
                      🏗️ Built in {property.year_built}
                    </div>
                  )}
                </div>

                <div className="flex justify-between items-center mt-4">
                  <span className="text-sm text-gray-500">Click to manage</span>
                  <button
                    onClick={(e) => handleDeleteProperty(property.id, e)}
                    className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                  >
                    Delete
                  </button>
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  Created: {new Date(property.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Floating IRIS Chat - available on property dashboard */}
      <FloatingIrisChat initialContext="maintenance" />
    </div>
  );
};

export default PropertyDashboard;