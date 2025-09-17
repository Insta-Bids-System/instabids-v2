import { useState } from "react";
import { MessageInput } from "../components/messaging/MessageInput";
import { BidCardProvider, useBidCard } from "../contexts/BidCardContext";

// Test component to verify API integration
function TestMessagingAPI() {
  const [testResults, setTestResults] = useState<string[]>([]);
  const { sendMessage, getMessages } = useBidCard();

  const runTest = async () => {
    setTestResults(["Starting test..."]);

    try {
      // Test 1: Send message with contact info
      const messageResult = await sendMessage({
        bidCardId: "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
        content: "Hi, my phone is 555-1234 and email is test@email.com",
        conversationId: undefined,
      });

      setTestResults((prev) => [
        ...prev,
        `✅ Message sent successfully`,
        `   Content filtered: ${messageResult.content_filtered ? "YES" : "NO"}`,
        `   Filtered content: ${messageResult.content}`,
        `   Filter reasons: ${JSON.stringify(messageResult.filter_reasons || [])}`,
      ]);

      // Test 2: Get messages
      const messages = await getMessages("2cb6e43a-2c92-4e30-93f2-e44629f8975f");
      setTestResults((prev) => [...prev, `✅ Retrieved ${messages.length} messages`]);
    } catch (error: unknown) {
      setTestResults((prev) => [...prev, `❌ Error: ${error.message}`]);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Messaging API Test</h1>

      <button
        type="button"
        onClick={runTest}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mb-6"
      >
        Run API Test
      </button>

      <div className="bg-gray-100 p-4 rounded mb-6">
        <h2 className="font-bold mb-2">Test Results:</h2>
        <pre className="whitespace-pre-wrap">{testResults.join("\n")}</pre>
      </div>

      <div className="border-t pt-6">
        <h2 className="font-bold mb-4">Test Message Input Component:</h2>
        <MessageInput
          conversationId="test-conversation"
          bidCardId="2cb6e43a-2c92-4e30-93f2-e44629f8975f"
          senderId="test-user-123"
          senderType="homeowner"
          onMessageSent={() => {
            setTestResults((prev) => [...prev, "✅ Message sent via component"]);
          }}
        />
      </div>
    </div>
  );
}

// Wrap in provider for testing
export function TestMessagingPage() {
  return (
    <BidCardProvider>
      <TestMessagingAPI />
    </BidCardProvider>
  );
}
