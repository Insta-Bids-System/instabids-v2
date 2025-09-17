import React, { useState, useRef } from 'react';

interface TestResult {
  success: boolean;
  approved: boolean;
  agent_decision: string;
  threats_detected: string[];
  confidence_score: number;
  original_content: string;
  filtered_content: string;
  agent_comments: Array<{
    visible_to: string;
    user_id: string;
    content: string;
    type: string;
    timestamp: string;
  }>;
  scope_changes_detected?: string[];
  scope_change_details?: Record<string, any>;
  requires_bid_update?: boolean;
  image_analysis?: Record<string, any>;
  error?: string;
}

export const IntelligentMessagingTester: React.FC = () => {
  const [message, setMessage] = useState('');
  const [senderType, setSenderType] = useState<'homeowner' | 'contractor'>('contractor');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const loadingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Test message presets
  const testMessages = {
    contactInfo: "Hi! I love your project. Can you call me at 555-123-4567 to discuss? Email me at contractor@example.com",
    socialMedia: "Check out my Instagram @mycompany and let's connect on LinkedIn",
    meetingArrange: "Let's grab coffee tomorrow to discuss your project in person",
    paymentBypass: "I can give you a 20% discount if you pay me directly via Venmo",
    legitimate: "I can install kitchen cabinets for $15,000. Timeline would be 2 weeks. Do you have color preferences?",
    scopeChange: "Actually, let's do mulch instead of rocks around the trees, and can we add a pergola over the patio area?",
    budgetChange: "I think we should increase the budget to $25,000 to get premium materials",
    timelineChange: "Actually, I need this project completed by next week instead of next month"
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Create preview URL for images
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const testMessage = async () => {
    if (!message.trim() && !selectedFile) {
      alert('Please enter a message or select a file');
      return;
    }

    setIsLoading(true);
    setTestResult(null);
    setElapsedTime(0);
    setLoadingMessage('🤖 Connecting to GPT-5 Intelligent Agent...');
    
    // Start timer
    const startTime = Date.now();
    loadingIntervalRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedTime(elapsed);
      
      // Update loading message based on elapsed time
      if (elapsed < 2) {
        setLoadingMessage('🤖 Connecting to GPT-5 Intelligent Agent...');
      } else if (elapsed < 4) {
        setLoadingMessage('🔍 Analyzing message for security threats...');
      } else if (elapsed < 6) {
        setLoadingMessage('🛡️ Checking for contact information patterns...');
      } else if (elapsed < 8) {
        setLoadingMessage('📋 Detecting project scope changes...');
      } else if (elapsed < 10) {
        setLoadingMessage('💭 GPT-5 is thinking deeply about this message...');
      } else {
        setLoadingMessage('⚡ Finalizing security analysis...');
      }
    }, 100);

    try {
      let result: TestResult;

      if (selectedFile && selectedFile.type.startsWith('image/')) {
        // Test with image
        const formData = new FormData();
        formData.append('content', message || 'Image attachment');
        formData.append('sender_type', senderType);
        formData.append('sender_id', `test-${senderType}-123`);
        formData.append('bid_card_id', '11111111-2222-3333-4444-555555555555');
        formData.append('image', selectedFile);

        const response = await fetch('/api/intelligent-messages/send-with-image', {
          method: 'POST',
          body: formData,
        });

        result = await response.json();
      } else {
        // Test text message - use query parameter as backend expects
        const testUrl = `/api/intelligent-messages/test-security?test_content=${encodeURIComponent(message)}`;
        console.log('Testing message:', message);
        console.log('API URL:', testUrl);
        
        const response = await fetch(testUrl, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
          },
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success && data.analysis_result) {
          result = data.analysis_result;
        } else {
          result = data;
        }
      }

      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult({
        success: false,
        approved: false,
        agent_decision: 'error',
        threats_detected: ['system_error'],
        confidence_score: 0,
        original_content: message,
        filtered_content: '',
        agent_comments: [],
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      // Clear the loading interval
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
      setIsLoading(false);
      setLoadingMessage('');
      setElapsedTime(0);
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision.toLowerCase()) {
      case 'block': return 'text-red-600 bg-red-50 border-red-200';
      case 'redact': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'allow': return 'text-green-600 bg-green-50 border-green-200';
      case 'warn': return 'text-orange-600 bg-orange-50 border-orange-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getThreatBadgeColor = (threat: string) => {
    const colors: Record<string, string> = {
      contact_info: 'bg-red-100 text-red-800',
      social_media: 'bg-purple-100 text-purple-800',
      external_meeting: 'bg-orange-100 text-orange-800',
      payment_bypass: 'bg-yellow-100 text-yellow-800',
      platform_bypass: 'bg-pink-100 text-pink-800',
    };
    return colors[threat] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">
          🤖 Intelligent Messaging System Tester
        </h2>
        
        {/* Test Presets */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Quick Test Messages:</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(testMessages).map(([key, msg]) => (
              <button
                key={key}
                onClick={() => setMessage(msg)}
                className="px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 rounded transition-colors"
              >
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </button>
            ))}
          </div>
        </div>

        {/* Message Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Test Message:
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter message to test for security threats..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>

        {/* Sender Type */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sender Type:
          </label>
          <select
            value={senderType}
            onChange={(e) => setSenderType(e.target.value as 'homeowner' | 'contractor')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="contractor">Contractor</option>
            <option value="homeowner">Homeowner</option>
          </select>
        </div>

        {/* File Upload */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Test Image/Document (Optional):
          </label>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept="image/*,.pdf,.doc,.docx"
            className="mb-2"
          />
          {selectedFile && (
            <div className="mt-2">
              <p className="text-sm text-gray-600">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)}KB)
              </p>
              {previewUrl && (
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  className="mt-2 max-w-xs max-h-32 object-contain border rounded"
                />
              )}
            </div>
          )}
        </div>

        {/* Test Button */}
        <button
          onClick={testMessage}
          disabled={isLoading || (!message.trim() && !selectedFile)}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Testing...' : '🧪 Run Security Test'}
        </button>
      </div>

      {/* Loading State Display */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow-lg p-6 animate-pulse">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <div className="flex-1">
              <p className="text-lg font-semibold text-blue-600">{loadingMessage}</p>
              <p className="text-sm text-gray-500">
                {elapsedTime > 0 && `Processing for ${elapsedTime} seconds...`}
              </p>
            </div>
          </div>
          
          {/* GPT-5 Thinking Visualization */}
          {elapsedTime > 5 && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700 font-medium mb-2">GPT-5 Analysis in Progress:</p>
              <div className="space-y-2">
                <div className={`flex items-center space-x-2 ${elapsedTime > 5 ? 'opacity-100' : 'opacity-30'}`}>
                  <span className="text-green-500">✓</span>
                  <span className="text-sm">Pattern matching for contact information</span>
                </div>
                <div className={`flex items-center space-x-2 ${elapsedTime > 7 ? 'opacity-100' : 'opacity-30'}`}>
                  <span className="text-green-500">✓</span>
                  <span className="text-sm">Analyzing conversation context</span>
                </div>
                <div className={`flex items-center space-x-2 ${elapsedTime > 9 ? 'opacity-100' : 'opacity-30'}`}>
                  <span className="text-green-500">✓</span>
                  <span className="text-sm">Detecting project scope changes</span>
                </div>
                <div className={`flex items-center space-x-2 ${elapsedTime > 11 ? 'opacity-100' : 'opacity-30'}`}>
                  <span className="text-yellow-500">⚡</span>
                  <span className="text-sm font-medium">Deep semantic analysis...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Test Results */}
      {testResult && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold mb-4">Test Results</h3>
          
          {/* Decision Summary */}
          <div className={`p-4 rounded-lg border-2 mb-4 ${getDecisionColor(testResult.agent_decision)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-lg">
                Decision: {testResult.agent_decision.toUpperCase()}
              </span>
              <span className="text-sm">
                Confidence: {(testResult.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="text-sm">
              Approved: <strong>{testResult.approved ? 'YES' : 'NO'}</strong>
            </div>
          </div>

          {/* Threats Detected */}
          {testResult.threats_detected.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold mb-2">🚨 Threats Detected:</h4>
              <div className="flex flex-wrap gap-2">
                {testResult.threats_detected.map((threat, index) => (
                  <span
                    key={index}
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getThreatBadgeColor(threat)}`}
                  >
                    {threat.replace(/_/g, ' ').toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Content Comparison */}
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div>
              <h4 className="font-semibold mb-2">📝 Original Content:</h4>
              <div className="bg-gray-100 p-3 rounded text-sm">
                {testResult.original_content || 'No text content'}
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-2">✏️ Filtered Content:</h4>
              <div className="bg-green-50 p-3 rounded text-sm">
                {testResult.filtered_content || '(Blocked - no content delivered)'}
              </div>
            </div>
          </div>

          {/* Agent Comments */}
          {testResult.agent_comments.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold mb-2">💬 Agent Comments:</h4>
              <div className="space-y-2">
                {testResult.agent_comments.map((comment, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border-l-4 ${
                      comment.type === 'warning' 
                        ? 'bg-red-50 border-red-400 text-red-700'
                        : comment.type === 'info'
                        ? 'bg-blue-50 border-blue-400 text-blue-700'
                        : 'bg-gray-50 border-gray-400 text-gray-700'
                    }`}
                  >
                    <div className="text-xs font-medium mb-1">
                      To: {comment.visible_to} • Type: {comment.type}
                    </div>
                    <div className="text-sm">{comment.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scope Changes */}
          {testResult.scope_changes_detected && testResult.scope_changes_detected.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold mb-2">📋 Scope Changes Detected:</h4>
              <div className="bg-yellow-50 p-3 rounded">
                <div className="flex flex-wrap gap-2 mb-2">
                  {testResult.scope_changes_detected.map((change, index) => (
                    <span key={index} className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded text-xs">
                      {change.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  ))}
                </div>
                {testResult.requires_bid_update && (
                  <div className="text-sm text-yellow-800 font-medium">
                    ⚠️ Bid update required - other contractors should be notified
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Image Analysis */}
          {testResult.image_analysis && (
            <div className="mb-4">
              <h4 className="font-semibold mb-2">🖼️ Image Analysis:</h4>
              <div className="bg-purple-50 p-3 rounded">
                <pre className="text-sm text-purple-800">
                  {JSON.stringify(testResult.image_analysis, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Error */}
          {testResult.error && (
            <div className="mb-4">
              <h4 className="font-semibient mb-2 text-red-600">❌ Error:</h4>
              <div className="bg-red-50 p-3 rounded text-red-700 text-sm">
                {testResult.error}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};