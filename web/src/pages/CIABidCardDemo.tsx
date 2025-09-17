import React from 'react';
import CIAChatWithBidCardPreview from '@/components/chat/CIAChatWithBidCardPreview';

const CIABidCardDemo: React.FC = () => {
  const handleProjectReady = (bidCardId: string) => {
    console.log('Project ready! Official bid card ID:', bidCardId);
    // Here you could redirect to the bid card page or show success message
    alert(`Great! Your bid card has been created. Bid Card ID: ${bidCardId}`);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-full mx-auto h-screen">
        <CIAChatWithBidCardPreview
          initialMessage="Hi! I'm Alex, your AI project assistant. I'll help you create a bid card to get competitive quotes from verified contractors. Let's start with the basics - what type of project are you planning?"
          showBidCardPreview={true}
          onProjectReady={handleProjectReady}
        />
      </div>
    </div>
  );
};

export default CIABidCardDemo;