import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  CreditCard,
  DollarSign,
  FileText,
  X,
  Info,
  ExternalLink
} from 'lucide-react';
import toast from 'react-hot-toast';

interface FeePaymentConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  connectionFee: {
    id: string;
    amount: number;
    bidAmount: number;
    projectTitle: string;
    homeownerName?: string;
    contractorReceives: number;
  };
  onPaymentConfirm: (feeId: string) => Promise<boolean>;
}

const FeePaymentConfirmationModal: React.FC<FeePaymentConfirmationModalProps> = ({
  isOpen,
  onClose,
  connectionFee,
  onPaymentConfirm
}) => {
  const [paymentStep, setPaymentStep] = useState<'confirm' | 'processing' | 'success' | 'error'>('confirm');
  const [errorMessage, setErrorMessage] = useState<string>('');

  if (!isOpen) return null;

  const handleConfirmPayment = async () => {
    setPaymentStep('processing');
    setErrorMessage('');

    try {
      const success = await onPaymentConfirm(connectionFee.id);
      
      if (success) {
        setPaymentStep('success');
        toast.success('Payment confirmed! You can now proceed with the project.');
        // Auto close after 3 seconds
        setTimeout(() => {
          onClose();
          setPaymentStep('confirm');
        }, 3000);
      } else {
        throw new Error('Payment processing failed');
      }
    } catch (error) {
      setPaymentStep('error');
      setErrorMessage(error instanceof Error ? error.message : 'Payment failed');
      toast.error('Payment failed. Please try again.');
    }
  };

  const handleClose = () => {
    if (paymentStep !== 'processing') {
      onClose();
      setPaymentStep('confirm');
      setErrorMessage('');
    }
  };

  const renderConfirmStep = () => (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-blue-600" />
          Connection Fee Payment
        </h2>
        <button
          onClick={handleClose}
          className="text-gray-400 hover:text-gray-600"
          disabled={paymentStep === 'processing'}
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Project Information */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900">Project Selected</h3>
            <p className="text-blue-700">{connectionFee.projectTitle}</p>
            {connectionFee.homeownerName && (
              <p className="text-sm text-blue-600">Client: {connectionFee.homeownerName}</p>
            )}
          </div>
        </div>
      </div>

      {/* Payment Breakdown */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <DollarSign className="w-4 h-4" />
          Payment Breakdown
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Your Winning Bid:</span>
            <span className="font-medium">${connectionFee.bidAmount.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-red-600">
            <span>Connection Fee:</span>
            <span className="font-medium">-${connectionFee.amount.toLocaleString()}</span>
          </div>
          <hr className="my-2" />
          <div className="flex justify-between text-lg font-semibold text-green-600">
            <span>You Will Receive:</span>
            <span>${connectionFee.contractorReceives.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Information Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <Info className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-yellow-800">
              <strong>Important:</strong> This connection fee helps InstaBids maintain our platform 
              and match you with quality projects. Payment confirms your commitment to this project.
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleClose}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
          disabled={paymentStep === 'processing'}
        >
          Cancel
        </button>
        <button
          onClick={handleConfirmPayment}
          className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center justify-center gap-2"
          disabled={paymentStep === 'processing'}
        >
          <CreditCard className="w-4 h-4" />
          Confirm Payment (${connectionFee.amount})
        </button>
      </div>

      {/* Terms Note */}
      <p className="text-xs text-gray-500 text-center mt-4">
        By confirming payment, you agree to InstaBids' terms of service and contractor agreement.{' '}
        <a href="/terms" className="text-blue-600 hover:underline" target="_blank">
          View Terms <ExternalLink className="w-3 h-3 inline ml-1" />
        </a>
      </p>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="p-6 text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing Payment</h2>
      <p className="text-gray-600">Please wait while we process your connection fee payment...</p>
    </div>
  );

  const renderSuccessStep = () => (
    <div className="p-6 text-center">
      <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Successful!</h2>
      <p className="text-gray-600 mb-4">
        Your connection fee has been processed. You can now proceed with the project.
      </p>
      <div className="bg-green-50 rounded-lg p-4 mb-4">
        <p className="text-green-800 font-medium">Next Steps:</p>
        <ul className="text-sm text-green-700 mt-2 space-y-1 text-left">
          <li>• Contact the homeowner to schedule the work</li>
          <li>• Review project details and requirements</li>
          <li>• Begin work according to your timeline</li>
        </ul>
      </div>
      <button
        onClick={handleClose}
        className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
      >
        Continue to Project
      </button>
    </div>
  );

  const renderErrorStep = () => (
    <div className="p-6 text-center">
      <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Payment Failed</h2>
      <p className="text-gray-600 mb-4">{errorMessage}</p>
      <div className="flex gap-3">
        <button
          onClick={handleClose}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={() => setPaymentStep('confirm')}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {paymentStep === 'confirm' && renderConfirmStep()}
        {paymentStep === 'processing' && renderProcessingStep()}
        {paymentStep === 'success' && renderSuccessStep()}
        {paymentStep === 'error' && renderErrorStep()}
      </div>
    </div>
  );
};

export default FeePaymentConfirmationModal;