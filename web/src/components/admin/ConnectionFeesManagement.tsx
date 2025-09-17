import React, { useEffect, useState } from 'react';
import ContractorDetailModal from './ContractorDetailModal';

interface ConnectionFee {
  fee_id: string;
  bid_card_id: string;
  bid_card_number: string;
  project_title: string;
  contractor_id: string;
  contractor_company: string;
  contractor_name: string | null;
  contractor_phone?: string;
  contractor_email?: string;
  contractor_license?: string;
  contractor_rating?: number;
  contractor_total_jobs?: number;
  contractor_years_experience?: number;
  contractor_specialties?: string[];
  winning_bid_amount: number;
  base_fee_amount: number;
  final_fee_amount: number;
  project_category?: string;
  calculation_method?: string;
  fee_status: 'calculated' | 'notified' | 'paid' | 'overdue';
  created_at: string;
  days_since_selection: number;
  homeowner_name: string | null;
  payment_processed_at?: string;
  // Referral tracking
  referral_code?: string;
  referrer_payout_amount?: number;
  referral_payout_status?: string;
}

const ConnectionFeesManagement: React.FC = () => {
  const [fees, setFees] = useState<ConnectionFee[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_fees_calculated: 0,
    total_fees_paid: 0,
    total_revenue: 0,
    pending_revenue: 0,
    payment_completion_rate: 0
  });
  const [overdueFees, setOverdueFees] = useState<ConnectionFee[]>([]);
  const [selectedContractor, setSelectedContractor] = useState<ConnectionFee | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchConnectionFees();
    fetchStats();
    fetchOverdueFees();
  }, []);

  const fetchConnectionFees = async () => {
    try {
      const response = await fetch('/api/admin/connection-fees');
      if (response.ok) {
        const data = await response.json();
        setFees(data);
      }
    } catch (error) {
      console.error('Error fetching connection fees:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/admin/connection-fees/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchOverdueFees = async () => {
    try {
      const response = await fetch('/api/admin/connection-fees/overdue');
      if (response.ok) {
        const data = await response.json();
        setOverdueFees(data.overdue_fees || []);
      }
    } catch (error) {
      console.error('Error fetching overdue fees:', error);
    }
  };

  const sendReminder = async (feeId: string) => {
    try {
      const response = await fetch(`/api/admin/connection-fees/${feeId}/remind`, {
        method: 'POST'
      });
      if (response.ok) {
        alert('Payment reminder sent successfully!');
        fetchConnectionFees(); // Refresh list
      } else {
        alert('Failed to send reminder');
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
      alert('Error sending reminder');
    }
  };

  const openContractorModal = (fee: ConnectionFee) => {
    setSelectedContractor(fee);
    setIsModalOpen(true);
  };

  const closeContractorModal = () => {
    setSelectedContractor(null);
    setIsModalOpen(false);
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      calculated: 'bg-blue-100 text-blue-800',
      notified: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-lg text-gray-600">Loading connection fees...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overdue Fees Alert */}
      {overdueFees.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <div className="text-red-400 text-2xl">⚠️</div>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {overdueFees.length} Overdue Payment{overdueFees.length > 1 ? 's' : ''}
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc pl-5 space-y-1">
                  {overdueFees.slice(0, 3).map(fee => (
                    <li key={fee.fee_id}>
                      <strong>{fee.contractor_company}</strong> - {fee.bid_card_number}: ${fee.final_fee_amount} 
                      ({fee.days_since_selection} days overdue)
                    </li>
                  ))}
                  {overdueFees.length > 3 && (
                    <li>... and {overdueFees.length - 3} more</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-blue-600">{stats.total_fees_calculated}</div>
          <div className="text-sm text-gray-600">Total Fees</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-green-600">{stats.total_fees_paid}</div>
          <div className="text-sm text-gray-600">Paid Fees</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-green-600">${stats.total_revenue.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Total Revenue</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-2xl font-bold text-yellow-600">${stats.pending_revenue.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Pending Revenue</div>
        </div>
      </div>

      {/* Connection Fees Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Connection Fee Tracking</h3>
          <p className="text-sm text-gray-600 mt-1">
            Track contractor payments after homeowner selection
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Project
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contractor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact Info
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bid Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Connection Fee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fees.map((fee) => (
                <tr key={fee.fee_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {fee.bid_card_number}
                      </div>
                      <div className="text-sm text-gray-500">{fee.project_title}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {fee.contractor_company}
                    </div>
                    <div className="text-sm text-gray-500">{fee.contractor_name || 'Contact TBD'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {fee.contractor_phone || 'Phone TBD'}
                    </div>
                    <div className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer">
                      {fee.contractor_email || 'Email TBD'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${fee.winning_bid_amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      ${fee.final_fee_amount}
                    </div>
                    <div className="text-xs text-gray-500">
                      Base: ${fee.base_fee_amount || fee.final_fee_amount}
                      {fee.project_category && (
                        <span className="block">Category: {fee.project_category}</span>
                      )}
                      {fee.referral_code && (
                        <span className="block text-purple-600">
                          Referral: {fee.referral_code} (-${fee.referrer_payout_amount || 0})
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(fee.fee_status)}`}>
                      {fee.fee_status}
                    </span>
                    {fee.days_since_selection > 7 && fee.fee_status === 'calculated' && (
                      <div className="text-xs text-red-600 mt-1">
                        {fee.days_since_selection} days since selection
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                    {fee.fee_status !== 'paid' && (
                      <button
                        onClick={() => sendReminder(fee.fee_id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Send Reminder
                      </button>
                    )}
                    <button
                      onClick={() => openContractorModal(fee)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details
                    </button>
                    {fee.contractor_email && (
                      <a 
                        href={`mailto:${fee.contractor_email}`}
                        className="text-green-600 hover:text-green-800 font-medium ml-2"
                      >
                        Email
                      </a>
                    )}
                    {fee.contractor_phone && (
                      <a 
                        href={`tel:${fee.contractor_phone}`}
                        className="text-purple-600 hover:text-purple-800 font-medium ml-2"
                      >
                        Call
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {fees.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">💳</div>
              <div className="text-lg font-medium text-gray-600 mb-2">No Connection Fees Yet</div>
              <div className="text-sm text-gray-500">
                When homeowners select winning contractors, connection fees will appear here for tracking and payment follow-up.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contractor Detail Modal */}
      <ContractorDetailModal
        contractor={selectedContractor}
        isOpen={isModalOpen}
        onClose={closeContractorModal}
        onSendReminder={sendReminder}
      />
    </div>
  );
};

export default ConnectionFeesManagement;