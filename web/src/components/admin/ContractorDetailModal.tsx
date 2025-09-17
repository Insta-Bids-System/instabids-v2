import React from 'react';

interface ContractorDetail {
  contractor_id: string;
  contractor_company: string;
  contractor_name: string | null;
  contractor_phone?: string;
  contractor_email?: string;
  license_number?: string;
  rating?: number;
  total_projects?: number;
  years_experience?: number;
  specialties?: string[];
  verified?: boolean;
  // Connection fee specific
  fee_id: string;
  bid_card_number: string;
  project_title: string;
  winning_bid_amount: number;
  final_fee_amount: number;
  base_fee_amount: number;
  project_category?: string;
  fee_status: string;
  created_at: string;
  days_since_selection: number;
  // Referral info
  referral_code?: string;
  referrer_payout_amount?: number;
}

interface ContractorDetailModalProps {
  contractor: ContractorDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onSendReminder: (feeId: string) => void;
}

const ContractorDetailModal: React.FC<ContractorDetailModalProps> = ({
  contractor,
  isOpen,
  onClose,
  onSendReminder
}) => {
  if (!isOpen || !contractor) return null;

  const getStatusBadge = (status: string) => {
    const colors = {
      calculated: 'bg-blue-100 text-blue-800',
      notified: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="bg-blue-100 p-3 rounded-full">
              <span className="text-blue-600 text-xl">👷</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {contractor.contractor_company}
              </h2>
              <p className="text-gray-600">
                {contractor.contractor_name || 'Contact Person TBD'}
              </p>
            </div>
            <div className="ml-auto">
              <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadge(contractor.fee_status)}`}>
                {contractor.fee_status}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
          {/* Contractor Information */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Contractor Details
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Company:</span>
                  <span className="font-medium">{contractor.contractor_company}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Contact:</span>
                  <span className="font-medium">{contractor.contractor_name || 'TBD'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Phone:</span>
                  <span className="font-medium">
                    {contractor.contractor_phone ? (
                      <a 
                        href={`tel:${contractor.contractor_phone}`}
                        className="text-purple-600 hover:text-purple-800"
                      >
                        {contractor.contractor_phone}
                      </a>
                    ) : 'TBD'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Email:</span>
                  <span className="font-medium">
                    {contractor.contractor_email ? (
                      <a 
                        href={`mailto:${contractor.contractor_email}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {contractor.contractor_email}
                      </a>
                    ) : 'TBD'}
                  </span>
                </div>
                {contractor.license_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">License:</span>
                    <span className="font-medium">{contractor.license_number}</span>
                  </div>
                )}
                {contractor.rating && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rating:</span>
                    <span className="font-medium">⭐ {contractor.rating}/5.0</span>
                  </div>
                )}
                {contractor.total_projects && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Projects:</span>
                    <span className="font-medium">{contractor.total_projects} completed</span>
                  </div>
                )}
                {contractor.years_experience && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Experience:</span>
                    <span className="font-medium">{contractor.years_experience} years</span>
                  </div>
                )}
              </div>

              {contractor.specialties && contractor.specialties.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Specialties</h4>
                  <div className="flex flex-wrap gap-2">
                    {contractor.specialties.map((specialty, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Project & Fee Information */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Project & Fee Details
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Project:</span>
                  <span className="font-medium text-right">{contractor.project_title}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Bid Card:</span>
                  <span className="font-medium">{contractor.bid_card_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Winning Bid:</span>
                  <span className="font-medium text-green-600">
                    ${contractor.winning_bid_amount.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Base Fee:</span>
                  <span className="font-medium">${contractor.base_fee_amount}</span>
                </div>
                {contractor.project_category && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Category:</span>
                    <span className="font-medium capitalize">{contractor.project_category.replace('_', ' ')}</span>
                  </div>
                )}
                <div className="flex justify-between font-semibold text-lg border-t pt-2">
                  <span className="text-gray-900">Connection Fee:</span>
                  <span className="text-blue-600">${contractor.final_fee_amount}</span>
                </div>
              </div>

              {contractor.referral_code && (
                <div className="bg-purple-50 rounded-lg p-4 mt-4">
                  <h4 className="text-sm font-semibold text-purple-800 mb-2">
                    Referral Information
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-purple-700">Referral Code:</span>
                      <span className="font-medium">{contractor.referral_code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-purple-700">Referrer Payout:</span>
                      <span className="font-medium">${contractor.referrer_payout_amount || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-yellow-50 rounded-lg p-4 mt-4">
                <h4 className="text-sm font-semibold text-yellow-800 mb-2">
                  Timeline
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-yellow-700">Selected:</span>
                    <span className="font-medium">{formatDate(contractor.created_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-yellow-700">Days Since:</span>
                    <span className="font-medium">
                      {contractor.days_since_selection} days
                      {contractor.days_since_selection > 7 && contractor.fee_status === 'calculated' && (
                        <span className="text-red-600 ml-2">(Overdue)</span>
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
          >
            Close
          </button>
          
          {contractor.contractor_email && (
            <a
              href={`mailto:${contractor.contractor_email}`}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              Send Email
            </a>
          )}
          
          {contractor.contractor_phone && (
            <a
              href={`tel:${contractor.contractor_phone}`}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
            >
              Call Contractor
            </a>
          )}
          
          {contractor.fee_status !== 'paid' && (
            <button
              onClick={() => onSendReminder(contractor.fee_id)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Send Payment Reminder
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ContractorDetailModal;