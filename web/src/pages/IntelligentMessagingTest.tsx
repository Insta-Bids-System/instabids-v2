import React from 'react';
import { IntelligentMessagingTester } from '@/components/testing/IntelligentMessagingTester';

const IntelligentMessagingTest: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            🛡️ InstaBids Messaging Security Testing
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Test the GPT-4o powered intelligent messaging system that prevents contact information sharing 
            and detects project scope changes. This is the business-critical system that protects the platform.
          </p>
        </div>
        
        <IntelligentMessagingTester />
        
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-3 text-blue-800">
            🎯 What This Tests:
          </h3>
          <ul className="space-y-2 text-sm text-blue-700">
            <li>• <strong>Contact Information Blocking</strong> - Phone numbers, emails, social media</li>
            <li>• <strong>Meeting Prevention</strong> - External meeting arrangements, coffee meetups</li>
            <li>• <strong>Payment Bypass Detection</strong> - Direct payment attempts outside platform</li>
            <li>• <strong>Scope Change Detection</strong> - Material, size, feature, timeline, budget changes</li>
            <li>• <strong>Image Analysis</strong> - Hidden contact info in images and documents</li>
            <li>• <strong>Agent Comments</strong> - Personalized warnings for contractors and homeowners</li>
            <li>• <strong>Real-time Processing</strong> - Live GPT-4o API calls with fallback protection</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default IntelligentMessagingTest;