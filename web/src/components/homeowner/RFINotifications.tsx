import React, { useEffect, useState } from 'react';
import { Bell, Camera, Ruler, HelpCircle, Settings, MapPin, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import RFIResponseForm from './RFIResponseForm';

interface RFIRequest {
  id: string;
  bid_card_id: string;
  contractor_id: string;
  request_type: 'pictures' | 'measurements' | 'clarification' | 'technical' | 'access';
  specific_items: string[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: string;
  custom_message?: string;
  created_at: string;
  metadata?: {
    contractor_name?: string;
    project_type?: string;
  };
  bid_card?: {
    project_type?: string;
    address?: string;
  };
}

interface RFINotificationsProps {
  homeownerId: string;
}

const RFINotifications: React.FC<RFINotificationsProps> = ({ homeownerId }) => {
  const [rfiRequests, setRfiRequests] = useState<RFIRequest[]>([]);
  const [loading, setLoading] = useState(false); // Start as false to prevent re-fetch
  const [unreadCount, setUnreadCount] = useState(0);
  const [showResponseForm, setShowResponseForm] = useState(false);
  const [selectedRFI, setSelectedRFI] = useState<RFIRequest | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Prevent duplicate API calls
    let mounted = true;
    let intervalId: NodeJS.Timeout | null = null;
    
    const loadRFIsIfMounted = async () => {
      if (mounted) {
        await loadRFIRequests();
      }
    };
    
    // Initial load
    loadRFIsIfMounted();
    
    // Poll for new RFIs every 30 seconds
    intervalId = setInterval(() => {
      if (mounted) {
        loadRFIsIfMounted();
      }
    }, 30000);
    
    // Cleanup function
    return () => {
      mounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [homeownerId]);

  const loadRFIRequests = async () => {
    // Prevent concurrent requests
    if (loading) return;
    
    try {
      setLoading(true);
      const response = await fetch(`/api/rfi/homeowner/${homeownerId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const rfiRequests = data.rfi_requests || [];
          
          // Fetch contractor info for each RFI
          const enrichedRFIs = await Promise.all(
            rfiRequests.map(async (rfi: RFIRequest) => {
              try {
                // Get contractor info separately
                const contractorResponse = await fetch(`/api/contractor-management/contractors/${rfi.contractor_id}`);
                if (contractorResponse.ok) {
                  const contractorData = await contractorResponse.json();
                  if (contractorData.success && contractorData.contractor) {
                    rfi.metadata = {
                      ...rfi.metadata,
                      contractor_name: contractorData.contractor.company_name || 'Unknown Contractor'
                    };
                  }
                }
              } catch (contractorError) {
                console.warn('Could not fetch contractor info for RFI:', rfi.id, contractorError);
                // Use fallback contractor name if available
                if (!rfi.metadata?.contractor_name) {
                  rfi.metadata = { ...rfi.metadata, contractor_name: 'Contractor' };
                }
              }
              return rfi;
            })
          );
          
          setRfiRequests(enrichedRFIs);
          // Count pending/notified as unread
          const unread = enrichedRFIs.filter(
            (r: RFIRequest) => r.status === 'pending' || r.status === 'homeowner_notified'
          ).length;
          setUnreadCount(unread);
        }
      }
    } catch (error) {
      console.error('Error loading RFI requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRequestIcon = (type: string) => {
    switch (type) {
      case 'pictures':
        return <Camera className="w-5 h-5" />;
      case 'measurements':
        return <Ruler className="w-5 h-5" />;
      case 'clarification':
        return <HelpCircle className="w-5 h-5" />;
      case 'technical':
        return <Settings className="w-5 h-5" />;
      case 'access':
        return <MapPin className="w-5 h-5" />;
      default:
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const handleRespondToRFI = async (rfi: RFIRequest) => {
    try {
      // Mark as acknowledged
      await fetch(`/api/rfi/${rfi.id}/acknowledge`, {
        method: 'POST'
      });

      // Route to CIA chat with RFI context instead of response form
      const rfiContext = {
        rfi_id: rfi.id,
        bid_card_id: rfi.bid_card_id,
        contractor_name: rfi.metadata?.contractor_name || 'Contractor',
        request_type: rfi.request_type,
        specific_items: rfi.specific_items,
        custom_message: rfi.custom_message,
        priority: rfi.priority,
        project_type: rfi.bid_card?.project_type || rfi.metadata?.project_type
      };
      
      // Navigate to chat with RFI context in state
      navigate('/homeowner', { 
        state: { 
          rfiContext,
          message: `I need help gathering ${rfi.request_type} that a contractor requested.`
        }
      });
      
      toast.success('Opening your assistant to help gather the requested information');
    } catch (error) {
      console.error('Error responding to RFI:', error);
      toast.error('Failed to open assistant');
    }
  };

  const handleResponseSuccess = () => {
    // Refresh RFI list after successful response
    loadRFIRequests();
    toast.success('Response sent successfully!');
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Information Requests from Contractors
            </h2>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-1">
                {unreadCount} NEW
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="p-6">
        {rfiRequests.length === 0 ? (
          <div className="text-center py-8">
            <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No information requests at this time</p>
            <p className="text-sm text-gray-400 mt-1">
              Contractors may request photos or details about your projects
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {rfiRequests.map((rfi) => (
              <div
                key={rfi.id}
                className={`border rounded-lg p-4 ${
                  rfi.status === 'pending' || rfi.status === 'homeowner_notified'
                    ? 'bg-blue-50 border-blue-200'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getRequestIcon(rfi.request_type)}
                      <span className="font-medium text-gray-900">
                        {rfi.metadata?.contractor_name || 'Contractor'} needs {rfi.request_type}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(rfi.priority)}`}>
                        {rfi.priority.toUpperCase()}
                      </span>
                    </div>

                    {rfi.bid_card?.project_type && (
                      <p className="text-sm text-gray-600 mb-2">
                        For your {rfi.bid_card.project_type} project
                        {rfi.bid_card.address && ` at ${rfi.bid_card.address}`}
                      </p>
                    )}

                    <div className="mb-3">
                      <p className="text-sm font-medium text-gray-700 mb-1">They need:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {rfi.specific_items.slice(0, 3).map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                        {rfi.specific_items.length > 3 && (
                          <li className="text-gray-500">
                            ... and {rfi.specific_items.length - 3} more items
                          </li>
                        )}
                      </ul>
                    </div>

                    {rfi.custom_message && (
                      <div className="bg-white rounded p-3 mb-3">
                        <p className="text-sm text-gray-700">
                          <span className="font-medium">Note:</span> {rfi.custom_message}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>
                        Requested {new Date(rfi.created_at).toLocaleDateString()}
                      </span>
                      {rfi.status === 'in_progress' && (
                        <span className="text-green-600 font-medium">• In Progress</span>
                      )}
                      {rfi.status === 'completed' && (
                        <span className="text-gray-600">• Completed</span>
                      )}
                    </div>
                  </div>

                  <div className="ml-4">
                    {(rfi.status === 'pending' || rfi.status === 'homeowner_notified') && (
                      <button
                        onClick={() => handleRespondToRFI(rfi)}
                        className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                      >
                        Add Photos & Respond
                      </button>
                    )}
                    {rfi.status === 'in_progress' && (
                      <button
                        onClick={() => handleRespondToRFI(rfi)}
                        className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium"
                      >
                        Continue Response
                      </button>
                    )}
                    {rfi.status === 'completed' && (
                      <span className="text-green-600 font-medium text-sm">
                        ✓ Responded
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RFI Response Form Modal */}
      {showResponseForm && selectedRFI && (
        <RFIResponseForm
          rfiId={selectedRFI.id}
          bidCardId={selectedRFI.bid_card_id}
          contractorName={selectedRFI.metadata?.contractor_name || 'Contractor'}
          requestedItems={selectedRFI.specific_items}
          onClose={() => {
            setShowResponseForm(false);
            setSelectedRFI(null);
          }}
          onSuccess={handleResponseSuccess}
        />
      )}
    </div>
  );
};

export default RFINotifications;