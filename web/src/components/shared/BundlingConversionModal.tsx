import React, { useState, useEffect } from 'react';
import { X, Package, ArrowRight, Check, AlertTriangle, Plus } from 'lucide-react';

interface PotentialBidCard {
  id: string;
  title: string;
  room_location?: string;
  primary_trade: string;
  secondary_trades: string[];
  project_complexity: 'simple' | 'moderate' | 'complex';
  user_scope_notes: string;
  eligible_for_group_bidding: boolean;
  requires_general_contractor: boolean;
  status: 'draft' | 'refined' | 'bundled' | 'converted';
  priority: number;
  urgency_level: 'low' | 'medium' | 'high' | 'urgent';
  ai_analysis?: any;
  created_at: string;
  bundle_group_id?: string;
}

interface BundlingConversionModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCards: PotentialBidCard[];
  userId: string;
  onBundleComplete?: (bundleId: string, bundledCards: PotentialBidCard[]) => void;
  onConversionComplete?: (convertedCards: any[]) => void;
}

type ConversionType = 'individual' | 'bundle' | 'group_bidding';

const BundlingConversionModal: React.FC<BundlingConversionModalProps> = ({
  isOpen,
  onClose,
  selectedCards,
  userId,
  onBundleComplete,
  onConversionComplete
}) => {
  const [step, setStep] = useState<'selection' | 'bundling' | 'conversion' | 'confirmation'>('selection');
  const [conversionType, setConversionType] = useState<ConversionType>('individual');
  const [bundleName, setBundleName] = useState('');
  const [requiresGeneralContractor, setRequiresGeneralContractor] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (selectedCards.length > 1) {
      setConversionType('bundle');
      setBundleName(`${selectedCards.length}-Project Bundle`);
    } else {
      setConversionType('individual');
    }

    // Auto-detect if general contractor needed
    const hasComplexProject = selectedCards.some(card => 
      card.project_complexity === 'complex' || 
      card.requires_general_contractor ||
      card.secondary_trades.length > 2
    );
    setRequiresGeneralContractor(hasComplexProject);
  }, [selectedCards]);

  const calculatePotentialSavings = () => {
    if (selectedCards.length < 2) return null;
    
    const eligibleForGroupBidding = selectedCards.filter(card => card.eligible_for_group_bidding).length;
    const locationBasedSavings = Math.min(eligibleForGroupBidding * 5, 25); // 5% per project, max 25%
    const bundleDiscount = selectedCards.length >= 3 ? 15 : 10; // Bundle discount
    
    return {
      groupBiddingSavings: locationBasedSavings,
      bundleDiscount,
      totalSavings: Math.min(locationBasedSavings + bundleDiscount, 35) // Max 35% total savings
    };
  };

  const handleCreateBundle = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/iris/potential-bid-cards/bundle?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_ids: selectedCards.map(card => card.id),
          bundle_name: bundleName,
          requires_general_contractor: requiresGeneralContractor
        })
      });

      if (response.ok) {
        const bundleResult = await response.json();
        setResult(bundleResult);
        setStep('confirmation');
        onBundleComplete?.(bundleResult.bundle_id, selectedCards);
      } else {
        throw new Error('Failed to create bundle');
      }
    } catch (error) {
      console.error('Bundle creation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToBidCards = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/iris/potential-bid-cards/convert-to-bid-cards?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_ids: selectedCards.map(card => card.id),
          conversion_type: conversionType
        })
      });

      if (response.ok) {
        const conversionResult = await response.json();
        setResult(conversionResult);
        setStep('confirmation');
        onConversionComplete?.(conversionResult.converted_cards);
      } else {
        throw new Error('Failed to convert to bid cards');
      }
    } catch (error) {
      console.error('Conversion error:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderSelectionStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Selected Projects</h3>
        <p className="text-gray-600">Review the projects you want to work with:</p>
      </div>

      <div className="space-y-3">
        {selectedCards.map((card) => (
          <div key={card.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0">
              <div className={`w-3 h-3 rounded-full ${
                card.urgency_level === 'urgent' ? 'bg-red-500' :
                card.urgency_level === 'high' ? 'bg-orange-500' :
                card.urgency_level === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
              }`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{card.title}</p>
              <p className="text-sm text-gray-500">{card.primary_trade} • {card.room_location}</p>
            </div>
            <div className="flex-shrink-0">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                card.project_complexity === 'simple' ? 'bg-green-100 text-green-800' :
                card.project_complexity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {card.project_complexity}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="border-t pt-6">
        <h4 className="font-medium text-gray-900 mb-3">What would you like to do?</h4>
        <div className="space-y-3">
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="radio"
              name="action"
              value="bundle"
              checked={step === 'bundling'}
              onChange={() => setStep('bundling')}
              className="mt-1"
            />
            <div>
              <div className="font-medium text-gray-900">Bundle Projects</div>
              <div className="text-sm text-gray-600">Group projects together for efficiency and cost savings</div>
            </div>
          </label>
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="radio"
              name="action"
              value="convert"
              checked={step === 'conversion'}
              onChange={() => setStep('conversion')}
              className="mt-1"
            />
            <div>
              <div className="font-medium text-gray-900">Convert to Bid Cards</div>
              <div className="text-sm text-gray-600">Send directly to contractors for quotes</div>
            </div>
          </label>
        </div>
      </div>
    </div>
  );

  const renderBundlingStep = () => {
    const savings = calculatePotentialSavings();

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Bundle Configuration</h3>
          <p className="text-gray-600">Configure how these projects should be bundled together:</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Bundle Name</label>
            <input
              type="text"
              value={bundleName}
              onChange={(e) => setBundleName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter a name for this bundle"
            />
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="generalContractor"
              checked={requiresGeneralContractor}
              onChange={(e) => setRequiresGeneralContractor(e.target.checked)}
            />
            <label htmlFor="generalContractor" className="text-sm font-medium text-gray-700">
              Requires general contractor coordination
            </label>
          </div>
        </div>

        {savings && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Check className="w-5 h-5 text-green-600" />
              <h4 className="font-medium text-green-900">Potential Savings</h4>
            </div>
            <div className="space-y-1 text-sm">
              {savings.groupBiddingSavings > 0 && (
                <div className="text-green-700">
                  Location-based group bidding: {savings.groupBiddingSavings}% savings
                </div>
              )}
              <div className="text-green-700">
                Bundle discount: {savings.bundleDiscount}% savings
              </div>
              <div className="font-medium text-green-800 border-t border-green-200 pt-1 mt-2">
                Total estimated savings: {savings.totalSavings}%
              </div>
            </div>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            onClick={() => setStep('selection')}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          <button
            onClick={handleCreateBundle}
            disabled={loading || !bundleName.trim()}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 flex items-center justify-center space-x-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <>
                <Package className="w-4 h-4" />
                <span>Create Bundle</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  };

  const renderConversionStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Convert to Bid Cards</h3>
        <p className="text-gray-600">Send these projects to contractors for quotes:</p>
      </div>

      <div className="space-y-3">
        <label className="flex items-start space-x-3 cursor-pointer">
          <input
            type="radio"
            name="conversionType"
            value="individual"
            checked={conversionType === 'individual'}
            onChange={(e) => setConversionType(e.target.value as ConversionType)}
            className="mt-1"
          />
          <div>
            <div className="font-medium text-gray-900">Individual Bid Cards</div>
            <div className="text-sm text-gray-600">Create separate bid cards for each project</div>
          </div>
        </label>

        {selectedCards.length > 1 && (
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="radio"
              name="conversionType"
              value="bundle"
              checked={conversionType === 'bundle'}
              onChange={(e) => setConversionType(e.target.value as ConversionType)}
              className="mt-1"
            />
            <div>
              <div className="font-medium text-gray-900">Bundled Bid Card</div>
              <div className="text-sm text-gray-600">Single bid card with all projects combined</div>
            </div>
          </label>
        )}

        {selectedCards.some(card => card.eligible_for_group_bidding) && (
          <label className="flex items-start space-x-3 cursor-pointer">
            <input
              type="radio"
              name="conversionType"
              value="group_bidding"
              checked={conversionType === 'group_bidding'}
              onChange={(e) => setConversionType(e.target.value as ConversionType)}
              className="mt-1"
            />
            <div>
              <div className="font-medium text-gray-900">Group Bidding</div>
              <div className="text-sm text-gray-600">Coordinate with neighbors for better rates</div>
              <div className="text-xs text-green-600 mt-1">15-25% potential savings</div>
            </div>
          </label>
        )}
      </div>

      <div className="flex space-x-3">
        <button
          onClick={() => setStep('selection')}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleConvertToBidCards}
          disabled={loading}
          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-300 flex items-center justify-center space-x-2"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          ) : (
            <>
              <ArrowRight className="w-4 h-4" />
              <span>Convert to Bid Cards</span>
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderConfirmationStep = () => (
    <div className="space-y-6 text-center">
      <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
        <Check className="w-8 h-8 text-green-600" />
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Success!</h3>
        {result?.bundle_id ? (
          <div className="space-y-2">
            <p className="text-gray-600">Bundle created successfully with {result.bundled_projects?.length} projects</p>
            <p className="text-sm text-gray-500">Bundle ID: {result.bundle_id}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600">
              {result?.total_converted} project{result?.total_converted !== 1 ? 's' : ''} converted to bid cards
            </p>
            <p className="text-sm text-gray-500">Conversion Type: {result?.conversion_type}</p>
          </div>
        )}
      </div>

      <button
        onClick={onClose}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Done
      </button>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {step === 'selection' && 'Project Actions'}
            {step === 'bundling' && 'Bundle Projects'}
            {step === 'conversion' && 'Convert to Bid Cards'}
            {step === 'confirmation' && 'Complete'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {step === 'selection' && renderSelectionStep()}
          {step === 'bundling' && renderBundlingStep()}
          {step === 'conversion' && renderConversionStep()}
          {step === 'confirmation' && renderConfirmationStep()}
        </div>
      </div>
    </div>
  );
};

export default BundlingConversionModal;