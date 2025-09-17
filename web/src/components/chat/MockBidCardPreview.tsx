import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  Clock, 
  Edit3, 
  MapPin, 
  Calendar,
  User,
  DollarSign,
  Wrench,
  Star,
  AlertCircle
} from 'lucide-react';

interface MockPotentialBidCard {
  id: string;
  status: string;
  completion_percentage: number;
  fields_collected: {
    project_type?: string;
    service_type?: string;
    project_description?: string;
    zip_code?: string;
    email_address?: string;
    timeline?: string;
    contractor_size?: string;
    budget_context?: string;
    materials?: string[];
    special_requirements?: string[];
    quality_expectations?: string;
  };
  missing_fields: string[];
  ready_for_conversion: boolean;
}

interface MockBidCardPreviewProps {
  conversationProgress: number; // 0-100 to simulate conversation progress
  onFieldEdit?: (fieldName: string, newValue: any) => void;
  className?: string;
}

export const MockBidCardPreview: React.FC<MockBidCardPreviewProps> = ({
  conversationProgress,
  onFieldEdit,
  className = ""
}) => {
  const [bidCard, setBidCard] = useState<MockPotentialBidCard | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Simulate progressive field filling based on conversation progress
  useEffect(() => {
    const mockData: MockPotentialBidCard = {
      id: "mock_bid_card_123",
      status: "draft",
      completion_percentage: 0,
      fields_collected: {},
      missing_fields: ["project_type", "project_description", "zip_code", "email_address", "timeline"],
      ready_for_conversion: false
    };

    // Simulate fields being filled in as conversation progresses
    if (conversationProgress >= 10) {
      mockData.fields_collected.project_type = "Kitchen Remodel";
      mockData.missing_fields = mockData.missing_fields.filter(f => f !== "project_type");
      mockData.completion_percentage = 20;
    }

    if (conversationProgress >= 25) {
      mockData.fields_collected.project_description = "Complete kitchen renovation including new cabinets, countertops, and appliances. Looking to modernize the space.";
      mockData.missing_fields = mockData.missing_fields.filter(f => f !== "project_description");
      mockData.completion_percentage = 40;
    }

    if (conversationProgress >= 40) {
      mockData.fields_collected.zip_code = "10001";
      mockData.missing_fields = mockData.missing_fields.filter(f => f !== "zip_code");
      mockData.completion_percentage = 60;
    }

    if (conversationProgress >= 55) {
      mockData.fields_collected.timeline = "Within 2-3 months";
      mockData.missing_fields = mockData.missing_fields.filter(f => f !== "timeline");
      mockData.completion_percentage = 70;
    }

    if (conversationProgress >= 70) {
      mockData.fields_collected.budget_context = "Have researched costs, expecting $25,000-40,000 range";
      mockData.completion_percentage = 85;
    }

    if (conversationProgress >= 85) {
      mockData.fields_collected.email_address = "homeowner@example.com";
      mockData.fields_collected.contractor_size = "Medium Regional Company";
      mockData.missing_fields = mockData.missing_fields.filter(f => f !== "email_address");
      mockData.completion_percentage = 100;
      mockData.ready_for_conversion = true;
      mockData.status = "ready";
    }

    setBidCard(mockData);
  }, [conversationProgress]);

  // Handle field editing
  const handleFieldEdit = (fieldName: string, currentValue: string) => {
    setEditingField(fieldName);
    setEditValue(currentValue || '');
  };

  const saveFieldEdit = () => {
    if (!bidCard || !editingField) return;

    setBidCard(prev => prev ? {
      ...prev,
      fields_collected: {
        ...prev.fields_collected,
        [editingField]: editValue
      }
    } : null);

    setEditingField(null);
    onFieldEdit?.(editingField, editValue);
  };

  const cancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  if (!bidCard) {
    return (
      <div className={`bg-gray-50 rounded-lg border border-gray-200 p-4 ${className}`}>
        <div className="text-center text-gray-500">
          <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-sm">Start describing your project to see your bid card preview</p>
        </div>
      </div>
    );
  }

  const completionColor = bidCard.completion_percentage >= 80 ? 'text-green-600' : 
                          bidCard.completion_percentage >= 50 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      {/* Header with completion status */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-t-lg border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center">
            <Wrench className="w-5 h-5 mr-2 text-blue-600" />
            Your Project Bid Card
          </h3>
          <div className="flex items-center space-x-2">
            <div className={`text-sm font-medium ${completionColor}`}>
              {bidCard.completion_percentage}% Complete
            </div>
            {bidCard.ready_for_conversion && (
              <CheckCircle className="w-5 h-5 text-green-500" />
            )}
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${bidCard.completion_percentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Bid card preview content */}
      <div className="p-4 space-y-4">
        
        {/* Project Title */}
        <div className="border-b border-gray-100 pb-3">
          <EditableField
            label="Project"
            value={bidCard.fields_collected.project_type || "New Project"}
            fieldName="project_type"
            icon={<Star className="w-4 h-4" />}
            isEditing={editingField === 'project_type'}
            editValue={editValue}
            onEdit={handleFieldEdit}
            onSave={saveFieldEdit}
            onCancel={cancelEdit}
            onEditValueChange={setEditValue}
          />
        </div>

        {/* Project Description */}
        <EditableField
          label="Description"
          value={bidCard.fields_collected.project_description}
          fieldName="project_description"
          icon={<User className="w-4 h-4" />}
          isEditing={editingField === 'project_description'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="Describe your project in detail..."
          multiline
        />

        {/* Location */}
        <EditableField
          label="Location"
          value={bidCard.fields_collected.zip_code}
          fieldName="zip_code"
          icon={<MapPin className="w-4 h-4" />}
          isEditing={editingField === 'zip_code'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="ZIP code"
        />

        {/* Timeline */}
        <EditableField
          label="Timeline"
          value={bidCard.fields_collected.timeline}
          fieldName="timeline"
          icon={<Calendar className="w-4 h-4" />}
          isEditing={editingField === 'timeline'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="e.g., Within 2 weeks, Flexible"
        />

        {/* Budget Context */}
        <EditableField
          label="Budget Understanding"
          value={bidCard.fields_collected.budget_context}
          fieldName="budget_context"
          icon={<DollarSign className="w-4 h-4" />}
          isEditing={editingField === 'budget_context'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="Have you researched costs? Any previous quotes?"
          multiline
        />

        {/* Contractor Size Preference */}
        <EditableField
          label="Contractor Preference"
          value={bidCard.fields_collected.contractor_size}
          fieldName="contractor_size"
          icon={<User className="w-4 h-4" />}
          isEditing={editingField === 'contractor_size'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="Size preference: Small Local, Medium Regional, Large Company, or No Preference"
        />

        {/* Contact Email */}
        <EditableField
          label="Contact Email"
          value={bidCard.fields_collected.email_address}
          fieldName="email_address"
          icon={<User className="w-4 h-4" />}
          isEditing={editingField === 'email_address'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="your@email.com"
        />

        {/* Missing Fields Alert */}
        {bidCard.missing_fields.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800">Still Need Information</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  Missing: {bidCard.missing_fields.map(field => field.replace('_', ' ')).join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Ready for conversion */}
        {bidCard.ready_for_conversion && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <h4 className="text-sm font-medium text-green-800">Ready to Find Contractors!</h4>
                <p className="text-sm text-green-700">Your bid card has all required information.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Reusable editable field component
interface EditableFieldProps {
  label: string;
  value?: string;
  fieldName: string;
  icon?: React.ReactNode;
  isEditing: boolean;
  editValue: string;
  onEdit: (fieldName: string, currentValue: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onEditValueChange: (value: string) => void;
  placeholder?: string;
  multiline?: boolean;
}

const EditableField: React.FC<EditableFieldProps> = ({
  label,
  value,
  fieldName,
  icon,
  isEditing,
  editValue,
  onEdit,
  onSave,
  onCancel,
  onEditValueChange,
  placeholder,
  multiline = false
}) => {
  const isEmpty = !value || value.trim() === '';
  
  if (isEditing) {
    return (
      <div className="space-y-2">
        <label className="flex items-center text-sm font-medium text-gray-700">
          {icon && <span className="mr-2">{icon}</span>}
          {label}
        </label>
        {multiline ? (
          <textarea
            className="w-full p-2 border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={editValue}
            onChange={(e) => onEditValueChange(e.target.value)}
            placeholder={placeholder}
            rows={3}
            autoFocus
          />
        ) : (
          <input
            type="text"
            className="w-full p-2 border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={editValue}
            onChange={(e) => onEditValueChange(e.target.value)}
            placeholder={placeholder}
            autoFocus
          />
        )}
        <div className="flex space-x-2">
          <button
            onClick={onSave}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
          >
            Save
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="group cursor-pointer" onClick={() => onEdit(fieldName, value || '')}>
      <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
        {icon && <span className="mr-2">{icon}</span>}
        {label}
        <Edit3 className="w-3 h-3 ml-2 opacity-0 group-hover:opacity-50 transition-opacity" />
      </label>
      <div className={`p-2 rounded-md border transition-colors ${
        isEmpty 
          ? 'border-dashed border-gray-300 bg-gray-50 text-gray-500' 
          : 'border-gray-200 bg-white text-gray-900 group-hover:border-blue-300'
      }`}>
        {isEmpty ? (
          <span className="italic">{placeholder || 'Click to add...'}</span>
        ) : (
          <span>{value}</span>
        )}
      </div>
    </div>
  );
};

export default MockBidCardPreview;