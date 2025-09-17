import type React from "react";
import { useEffect, useState } from "react";
import LoadingSpinner from "../ui/LoadingSpinner";

interface BidSubmission {
  id: string;
  bid_card_id: string;
  contractor_id: string;
  contractor_name: string;
  contractor_company?: string;
  bid_amount: number;
  timeline_days: number;
  proposal_text: string;
  attachments: any[];
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  updated_at: string;
}

interface BidSubmissionsDetailProps {
  bidCardId: string;
  bidCardNumber?: string;
  onClose?: () => void;
}

const BidSubmissionsDetail: React.FC<BidSubmissionsDetailProps> = ({
  bidCardId,
  bidCardNumber,
  onClose,
}) => {
  const [submissions, setSubmissions] = useState<BidSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBidSubmissions();
  }, [bidCardId]);

  const fetchBidSubmissions = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/contractor-proposals/bid-card/${bidCardId}`
      );

      if (response.ok) {
        const data = await response.json();
        setSubmissions(data);
      } else {
        setError("Failed to load bid submissions");
      }
    } catch (err) {
      setError("Error connecting to backend");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "accepted":
        return "bg-green-100 text-green-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toLocaleString()}`;
  };

  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const handleUpdateStatus = async (submissionId: string, newStatus: 'accepted' | 'rejected') => {
    try {
      const response = await fetch(
        `/api/contractor-proposals/${submissionId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status: newStatus,
            user_id: '11111111-1111-1111-1111-111111111111' // Test homeowner ID
          }),
        }
      );

      if (response.ok) {
        // Refresh submissions
        fetchBidSubmissions();
      } else {
        alert('Failed to update bid status');
      }
    } catch (error) {
      alert('Error updating bid status');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading bid submissions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex">
          <div className="text-red-400 text-xl mr-3">⚠️</div>
          <div>
            <h3 className="text-red-800 font-medium">Error Loading Bid Submissions</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <button
              onClick={fetchBidSubmissions}
              className="mt-3 text-sm bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium text-gray-900">
            Bid Submissions - {bidCardNumber}
          </h2>
          <p className="text-sm text-gray-600">
            {submissions.length} bid{submissions.length !== 1 ? 's' : ''} received
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-bold"
          >
            ×
          </button>
        )}
      </div>

      {/* Submissions List */}
      {submissions.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">📄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Bids Submitted</h3>
          <p className="text-gray-600">No contractors have submitted bids for this project yet.</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {submissions.map((submission, index) => (
            <div key={submission.id} className="p-6">
              {/* Submission Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded">
                    #{index + 1}
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {submission.contractor_name}
                    </h3>
                    {submission.contractor_company && (
                      <p className="text-sm text-gray-600">{submission.contractor_company}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(submission.bid_amount)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {submission.timeline_days} day timeline
                  </div>
                </div>
              </div>

              {/* Status and Actions */}
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center space-x-4">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(submission.status)}`}
                  >
                    {submission.status.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-500">
                    Submitted {formatTimeAgo(submission.created_at)}
                  </span>
                </div>
                
                {/* Action Buttons */}
                {submission.status === 'pending' && (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleUpdateStatus(submission.id, 'accepted')}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(submission.id, 'rejected')}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>

              {/* Proposal Text */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Proposal:</h4>
                <p className="text-sm text-gray-900">{submission.proposal_text}</p>
              </div>

              {/* Attachments */}
              {submission.attachments && submission.attachments.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Attachments:</h4>
                  <div className="flex flex-wrap gap-2">
                    {submission.attachments.map((attachment, attIndex) => (
                      <span
                        key={attIndex}
                        className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs"
                      >
                        📎 {attachment.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="mt-4 text-xs text-gray-500 grid grid-cols-2 gap-4">
                <div>
                  <span className="font-medium">Contractor ID:</span> {submission.contractor_id}
                </div>
                <div>
                  <span className="font-medium">Submission ID:</span> {submission.id}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BidSubmissionsDetail;