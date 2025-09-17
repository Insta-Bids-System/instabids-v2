import React, { useState } from 'react';

// Test component to isolate image rendering issue
const TestReactImages = () => {
  const [messages, setMessages] = useState([]);
  
  const testImageDisplay = async () => {
    console.log('🧪 Starting React image test...');
    
    try {
      // Call the real API
      const response = await fetch('http://localhost:8008/api/iris/find-inspiration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'farmhouse kitchen',
          search_query: 'farmhouse kitchen inspiration',
          user_id: '550e8400-e29b-41d4-a716-446655440001'
        })
      });
      
      const data = await response.json();
      console.log('🧪 API Response:', data);
      
      // Map the images exactly like IrisChat does
      const mappedImages = data.inspiration_items?.map((item) => ({
        url: item.image_url,
        description: item.description
      })) || [];
      
      console.log('🧪 Mapped Images:', mappedImages);
      
      // Create message exactly like IrisChat does
      const testMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Test message with images",
        timestamp: new Date(),
        images: mappedImages
      };
      
      console.log('🧪 Test Message:', {
        hasImages: !!testMessage.images,
        imageCount: testMessage.images?.length,
        firstImage: testMessage.images?.[0]
      });
      
      // Add to messages array
      setMessages([testMessage]);
      
    } catch (error) {
      console.error('🧪 Test failed:', error);
    }
  };
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>React Image Rendering Test</h1>
      <button onClick={testImageDisplay} style={{ 
        padding: '10px 20px', 
        background: '#007bff', 
        color: 'white', 
        border: 'none', 
        cursor: 'pointer' 
      }}>
        Test Image Display
      </button>
      
      <div style={{ marginTop: '20px' }}>
        {messages.map((message) => (
          <div key={message.id} style={{ 
            background: '#f8f9fa', 
            padding: '15px', 
            margin: '10px 0', 
            borderRadius: '8px' 
          }}>
            <p>{message.content}</p>
            
            {/* Debug info */}
            <div style={{ background: '#e9ecef', padding: '10px', margin: '10px 0', fontSize: '12px' }}>
              <strong>Debug Info:</strong><br/>
              Has images: {message.images ? 'YES' : 'NO'}<br/>
              Image count: {message.images?.length || 0}<br/>
              Images array: {JSON.stringify(message.images, null, 2)}
            </div>
            
            {/* Conditional rendering test - exactly like IrisChat */}
            {message.images && message.images.length > 0 && (
              <div style={{ marginTop: '15px' }}>
                <p style={{ color: 'green', fontSize: '12px' }}>
                  🖼️ RENDERING {message.images.length} IMAGES
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  {message.images.map((image, idx) => (
                    <div key={idx}>
                      <img
                        src={image.url}
                        alt={image.description}
                        style={{ 
                          width: '100%', 
                          height: '150px', 
                          objectFit: 'cover', 
                          borderRadius: '8px' 
                        }}
                        onLoad={() => console.log(`🧪 Image ${idx} loaded:`, image.url)}
                        onError={(e) => console.error(`🧪 Image ${idx} failed:`, image.url)}
                      />
                      <p style={{ fontSize: '12px', marginTop: '5px' }}>
                        {image.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TestReactImages;