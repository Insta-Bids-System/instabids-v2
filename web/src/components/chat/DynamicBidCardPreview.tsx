import React, { useEffect, useState } from 'react';
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

interface PotentialBidCard {
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
  conversation_id?: string;
  photo_ids?: Array<{
    id: string;
    content: string; // base64 encoded image
    filename?: string;
    content_type?: string;
  }>;
  bid_card_preview: {
    title: string;
    project_type?: string;
    description?: string;
    location?: string;
    timeline?: string;
    contractor_preference?: string;
    special_notes?: string[];
    uploaded_photos?: Array<{
      id: string;
      content: string;
      filename?: string;
      content_type?: string;
    }>;
  };
}

interface DynamicBidCardPreviewProps {
  conversationId: string;
  onFieldEdit?: (fieldName: string, newValue: any) => void;
  className?: string;
}

export const DynamicBidCardPreview: React.FC<DynamicBidCardPreviewProps> = ({
  conversationId,
  onFieldEdit,
  className = ""
}) => {
  const [bidCard, setBidCard] = useState<PotentialBidCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Fetch potential bid card data
  const fetchBidCard = async () => {
    try {
      const response = await fetch(`/api/cia/conversation/${conversationId}/potential-bid-card`);
      if (response.ok) {
        const data = await response.json();
        setBidCard(data);
      }
    } catch (error) {
      console.log('No potential bid card found yet:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch bid card ONCE on conversation change - NO MORE FUCKING POLLING
  useEffect(() => {
    fetchBidCard();
  }, [conversationId]);

  // Handle field editing
  const handleFieldEdit = (fieldName: string, currentValue: string) => {
    setEditingField(fieldName);
    setEditValue(currentValue || '');
  };

  const saveFieldEdit = async () => {
    if (!bidCard || !editingField) return;

    try {
      const response = await fetch(`/api/cia/potential-bid-cards/${bidCard.id}/field`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          field_name: editingField,
          field_value: editValue,
          source: 'manual'
        })
      });

      if (response.ok) {
        await fetchBidCard(); // Refresh data
        setEditingField(null);
        onFieldEdit?.(editingField, editValue);
      }
    } catch (error) {
      console.error('Error updating field:', error);
    }
  };

  const cancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Clock className="w-5 h-5 text-blue-500 animate-spin" />
          <h3 className="text-lg font-semibold text-gray-800">Analyzing Your Project...</h3>
        </div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2"></div>
        </div>
      </div>
    );
  }

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
              className="bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
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
            value={bidCard.bid_card_preview.title}
            fieldName="title"
            icon={<Star className="w-4 h-4" />}
            isEditing={editingField === 'title'}
            editValue={editValue}
            onEdit={handleFieldEdit}
            onSave={saveFieldEdit}
            onCancel={cancelEdit}
            onEditValueChange={setEditValue}
          />
        </div>

        {/* Project Type */}
        <EditableField
          label="Project Type"
          value={bidCard.fields_collected.project_type}
          fieldName="project_type"
          icon={<Wrench className="w-4 h-4" />}
          isEditing={editingField === 'project_type'}
          editValue={editValue}
          onEdit={handleFieldEdit}
          onSave={saveFieldEdit}
          onCancel={cancelEdit}
          onEditValueChange={setEditValue}
          placeholder="e.g., Kitchen Remodel, Bathroom Renovation"
        />

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

        {/* Uploaded Photos Section */}
        {(bidCard.photo_ids?.length > 0 || bidCard.bid_card_preview.uploaded_photos?.length > 0) && (
          <div className="border-t border-gray-100 pt-4 mt-4">
            <div className="flex items-center space-x-2 mb-3">
              <User className="w-4 h-4 text-gray-600" />
              <h4 className="text-sm font-medium text-gray-700">Project Photos</h4>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {/* Display photos from photo_ids first */}
              {bidCard.photo_ids?.map((photo, index) => (
                <div key={photo.id || index} className="relative">
                  <img
                    src={`data:${photo.content_type || 'image/jpeg'};base64,${photo.content}`}
                    alt={photo.filename || `Project photo ${index + 1}`}
                    className="w-full h-24 object-cover rounded-lg border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                    onClick={() => {
                      // Open image in new tab for full view
                      const newWindow = window.open('', '_blank');
                      if (newWindow) {
                        newWindow.document.write(`
                          <html>
                            <head><title>${photo.filename || 'Project Photo'}</title></head>
                            <body style="margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#f0f0f0;">
                              <img src="data:${photo.content_type || 'image/jpeg'};base64,${photo.content}" style="max-width:90vw;max-height:90vh;object-fit:contain;" />
                            </body>
                          </html>
                        `);
                      }
                    }}
                  />
                  {photo.filename && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-1 rounded-b-lg truncate">
                      {photo.filename}
                    </div>
                  )}
                </div>
              ))}
              
              {/* Display photos from bid_card_preview.uploaded_photos if different */}
              {bidCard.bid_card_preview.uploaded_photos?.map((photo, index) => (
                <div key={`preview-${photo.id || index}`} className="relative">
                  <img
                    src={`data:${photo.content_type || 'image/jpeg'};base64,${photo.content}`}
                    alt={photo.filename || `Preview photo ${index + 1}`}
                    className="w-full h-24 object-cover rounded-lg border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                    onClick={() => {
                      // Open image in new tab for full view
                      const newWindow = window.open('', '_blank');
                      if (newWindow) {
                        newWindow.document.write(`
                          <html>
                            <head><title>${photo.filename || 'Preview Photo'}</title></head>
                            <body style="margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#f0f0f0;">
                              <img src="data:${photo.content_type || 'image/jpeg'};base64,${photo.content}" style="max-width:90vw;max-height:90vh;object-fit:contain;" />
                            </body>
                          </html>
                        `);
                      }
                    }}
                  />
                  {photo.filename && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-1 rounded-b-lg truncate">
                      {photo.filename}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <p className="text-xs text-gray-500 mt-2">
              Click any photo to view full size
            </p>
          </div>
        )}

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
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <h4 className="text-sm font-medium text-green-800">Ready to Find Contractors!</h4>
                  <p className="text-sm text-green-700">Your bid card has all required information.</p>
                </div>
              </div>
              <button
                onClick={() => window.dispatchEvent(new CustomEvent('triggerSignup', { 
                  detail: { bidCardId: bidCard.id, conversationId: conversationId } 
                }))}
                className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Get Contractors
              </button>
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

export default DynamicBidCardPreview;