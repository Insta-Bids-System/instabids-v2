import React, { useEffect, useState } from 'react';

interface ConnectionFee {
  fee_id: string;
  bid_card_id: string;
  bid_card_number: string;
  project_type: string;
  contractor_id: string;
  contractor_company_name: string;
  contractor_contact_name: string;
  contractor_phone: string;
  contractor_email: string;
  bid_amount: number;
  final_fee_amount: number;
  base_fee: number;
  category_adjustment: number;
  referral_split?: number;
  fee_status: 'calculated' | 'notified' | 'paid' | 'overdue';
  calculated_at: string;
  due_date: string;
  payment_date?: string;
  days_overdue?: number;
}

const AdminConnectionFeesPage: React.FC = () => {
  const [fees, setFees] = useState<ConnectionFee[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_fees_calculated: 0,
    total_fees_paid: 0,
    total_revenue: 0,
    pending_revenue: 0,
    payment_completion_rate: 0
  });

  useEffect(() => {
    fetchConnectionFees();
    fetchStats();
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading connection fees...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Connection Fees Management</h1>
          <p className="text-gray-600">Track contractor selection fees and payment workflow</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
            <h2 className="text-lg font-semibold text-gray-900">Connection Fees</h2>
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
                    Contact
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
                        <div className="text-sm text-gray-500">{fee.project_type}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {fee.contractor_company_name}
                      </div>
                      <div className="text-sm text-gray-500">{fee.contractor_contact_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{fee.contractor_phone}</div>
                      <div className="text-sm text-gray-500">{fee.contractor_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${fee.bid_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        ${fee.final_fee_amount}
                      </div>
                      <div className="text-xs text-gray-500">
                        Base: ${fee.base_fee}
                        {fee.category_adjustment !== 0 && (
                          <span> + Adj: ${fee.category_adjustment}</span>
                        )}
                        {fee.referral_split && (
                          <span> - Ref: ${fee.referral_split}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(fee.fee_status)}`}>
                        {fee.fee_status}
                      </span>
                      {fee.days_overdue && fee.days_overdue > 0 && (
                        <div className="text-xs text-red-600 mt-1">
                          {fee.days_overdue} days overdue
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {fee.fee_status !== 'paid' && (
                        <button
                          onClick={() => sendReminder(fee.fee_id)}
                          className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                        >
                          Send Reminder
                        </button>
                      )}
                      <button className="text-gray-600 hover:text-gray-800 font-medium">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {fees.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No connection fees found. When homeowners select winning contractors, they'll appear here.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminConnectionFeesPage;