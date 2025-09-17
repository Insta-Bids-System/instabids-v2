import React, { useState, useEffect } from "react";
import PotentialBidCard from "@/components/bidcards/PotentialBidCard";
import { BidCardEditModal } from "@/components/bidcards/BidCardEditModal";

const TestPotentialBidCard = () => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [bidCard, setBidCard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch REAL potential bid card from database
  useEffect(() => {
    const fetchRealBidCard = async () => {
      try {
        setLoading(true);
        // Use the kitchen renovation bid card we found in the database
        const response = await fetch('/api/cia/potential-bid-cards/6141f0b6-9578-453c-b757-8e33177f0bb4');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch bid card: ${response.status}`);
        }
        
        const realBidCard = await response.json();
        console.log('Fetched REAL bid card:', realBidCard);
        setBidCard(realBidCard);
      } catch (err) {
        console.error('Error fetching real bid card:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRealBidCard();
  }, []);

  const handleReview = (bidCard: any) => {
    console.log("Review clicked for bid card:", bidCard);
    setShowEditModal(true);
  };

  const handleBidCardUpdate = () => {
    console.log("Bid card updated");
  };

  const handleConversionReady = (bidCardId: string) => {
    console.log("Bid card ready for conversion:", bidCardId);
    alert(`Bid card ${bidCardId} is ready for conversion!`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">REAL Potential Bid Card</h1>
          <div className="flex items-center justify-center py-12">
            <div className="text-lg">Loading REAL bid card from database...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">REAL Potential Bid Card</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error loading bid card: {error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!bidCard) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">REAL Potential Bid Card</h1>
          <div className="text-center py-12">
            <p>No bid card found</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">REAL Potential Bid Card from Database</h1>
        
        <div className="mb-4 p-4 bg-green-50 rounded-lg">
          <p className="text-green-800">
            ✅ This is REAL data from the database! Bid Card ID: {bidCard.id}
          </p>
          <p className="text-green-700 text-sm mt-1">
            Created: {new Date(bidCard.created_at).toLocaleString()} | Completion: {bidCard.completion_percentage}%
          </p>
        </div>

        <PotentialBidCard 
          bidCard={bidCard}
          onReview={handleReview}
        />

        <BidCardEditModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          bidCard={bidCard}
          onBidCardUpdate={handleBidCardUpdate}
          onConversionReady={handleConversionReady}
        />
      </div>
    </div>
  );
};

export default TestPotentialBidCard;