import React, { useState } from 'react';
import {
  Calendar,
  DollarSign,
  MapPin,
  User,
  AlertCircle,
  CreditCard,
  CheckCircle,
  Clock,
  FileText
} from 'lucide-react';
import FeePaymentConfirmationModal from './FeePaymentConfirmationModal';
import toast from 'react-hot-toast';

interface ContractorProjectCardProps {
  project: {
    id: string;
    bidCardNumber: string;
    projectTitle: string;
    projectType: string;
    status: 'selected' | 'payment_pending' | 'active' | 'completed';
    homeownerName?: string;
    location: {
      city: string;
      state: string;
    };
    timeline: string;
    bidAmount: number;
    connectionFee?: {
      id: string;
      amount: number;
      status: 'calculated' | 'paid' | 'pending';
    };
    createdAt: string;
  };
  contractorId: string;
}

const ContractorProjectCard: React.FC<ContractorProjectCardProps> = ({
  project,
  contractorId
}) => {
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'selected':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'payment_pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'completed':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'selected':
        return <CheckCircle className="w-4 h-4" />;
      case 'payment_pending':
        return <CreditCard className="w-4 h-4" />;
      case 'active':
        return <Clock className="w-4 h-4" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const handlePaymentConfirm = async (feeId: string): Promise<boolean> => {
    setIsProcessingPayment(true);
    
    try {
      // In production, this would integrate with Stripe or payment processor
      // For now, simulate the API call to update payment status
      const response = await fetch(`/api/connection-fees/${feeId}/pay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contractor_id: contractorId,
          payment_method: 'card' // In production, this would come from Stripe
        }),
      });

      if (!response.ok) {
        throw new Error('Payment processing failed');
      }

      const result = await response.json();
      
      // Update local state to reflect payment
      toast.success('Payment successful! You can now proceed with the project.');
      
      // In a real app, you'd refresh the project data or update state
      return true;
      
    } catch (error) {
      console.error('Payment error:', error);
      toast.error('Payment failed. Please try again.');
      return false;
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const contractorReceives = project.bidAmount - (project.connectionFee?.amount || 0);

  return (
    <>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {project.projectTitle}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {project.bidCardNumber} • {project.projectType.replace('_', ' ')}
              </p>
            </div>
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}>
              {getStatusIcon(project.status)}
              <span className="ml-1">{project.status.replace('_', ' ').toUpperCase()}</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Project Details */}
          <div className="grid grid-cols-2 gap-4">
            {project.homeownerName && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User className="w-4 h-4" />
                <span>{project.homeownerName}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4" />
              <span>{project.location.city}, {project.location.state}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Calendar className="w-4 h-4" />
              <span>{project.timeline}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <DollarSign className="w-4 h-4" />
              <span>Bid: ${project.bidAmount.toLocaleString()}</span>
            </div>
          </div>

          {/* Connection Fee Info */}
          {project.connectionFee && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">Connection Fee</p>
                  <p className="text-sm text-gray-600">
                    Fee: ${project.connectionFee.amount} • You receive: ${contractorReceives.toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  {project.connectionFee.status === 'paid' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Paid
                    </span>
                  )}
                  {project.connectionFee.status !== 'paid' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      <CreditCard className="w-3 h-3 mr-1" />
                      Payment Required
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2">
              <FileText className="w-4 h-4" />
              View Details
            </button>
            
            {project.connectionFee && project.connectionFee.status !== 'paid' && (
              <button
                onClick={() => setShowPaymentModal(true)}
                disabled={isProcessingPayment}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <CreditCard className="w-4 h-4" />
                {isProcessingPayment ? 'Processing...' : 'Pay Connection Fee'}
              </button>
            )}
            
            {project.connectionFee?.status === 'paid' && project.status === 'active' && (
              <button className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 flex items-center justify-center gap-2">
                <User className="w-4 h-4" />
                Contact Homeowner
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && project.connectionFee && (
        <FeePaymentConfirmationModal
          isOpen={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          connectionFee={{
            id: project.connectionFee.id,
            amount: project.connectionFee.amount,
            bidAmount: project.bidAmount,
            projectTitle: project.projectTitle,
            homeownerName: project.homeownerName,
            contractorReceives: contractorReceives
          }}
          onPaymentConfirm={handlePaymentConfirm}
        />
      )}
    </>
  );
};

export default ContractorProjectCard;