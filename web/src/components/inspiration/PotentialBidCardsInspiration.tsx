import {
  Sparkles,
  Plus,
  CheckCircle,
  MessageCircle,
  TrendingUp,
  Package,
  Calendar,
  DollarSign,
  Users,
  ChevronRight,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Card, Badge, Button, Progress, Tooltip, Empty, Skeleton } from "antd";
import { useAuth } from "@/contexts/AuthContext";

interface PotentialBidCard {
  id: string;
  user_id: string;
  title: string;
  room_location?: string;
  property_area?: string;
  primary_trade: string;
  secondary_trades: string[];
  project_complexity: "simple" | "moderate" | "complex";
  photo_ids: string[];
  cover_photo_id?: string;
  cover_photo_url?: string;
  ai_analysis: {
    detected_issues?: string[];
    estimated_cost?: string;
    design_elements?: string[];
    style_analysis?: string;
    color_palette?: string[];
    inspiration_match_score?: number;
  };
  user_scope_notes: string;
  priority: number;
  status: "draft" | "refined" | "bundled" | "converted";
  bundle_group_id?: string;
  eligible_for_group_bidding: boolean;
  component_type: "inspiration" | "maintenance" | "both";
  urgency_level: "low" | "medium" | "high" | "urgent";
  estimated_timeline?: string;
  budget_range_min?: number;
  budget_range_max?: number;
  created_at: string;
  updated_at: string;
}

interface PotentialBidCardsInspirationProps {
  className?: string;
}

const PotentialBidCardsInspiration: React.FC<PotentialBidCardsInspirationProps> = ({
  className = ""
}) => {
  const { user } = useAuth();
  const [potentialBidCards, setPotentialBidCards] = useState<PotentialBidCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCards, setSelectedCards] = useState<string[]>([]);
  const [showingBundleModal, setShowingBundleModal] = useState(false);

  const loadPotentialBidCards = async () => {
    if (!user) return;

    try {
      setLoading(true);
      
      // Get inspiration-focused potential bid cards
      const response = await fetch(
        `/api/iris/potential-bid-cards/${user.id}?component_type=inspiration`
      );
      
      if (response.ok) {
        const data = await response.json();
        setPotentialBidCards(data.potential_bid_cards || []);
      } else {
        throw new Error("Failed to load potential bid cards");
      }
    } catch (error) {
      console.error("Error loading potential bid cards:", error);
      toast.error("Failed to load inspiration projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPotentialBidCards();
  }, [user]);

  const handleCardClick = (card: PotentialBidCard) => {
    // Open detailed view or start conversation about this card
    // This would integrate with IRIS conversation system
    console.log("Opening card details:", card);
  };

  const handleSelectCard = (cardId: string) => {
    setSelectedCards(prev => 
      prev.includes(cardId) 
        ? prev.filter(id => id !== cardId)
        : [...prev, cardId]
    );
  };

  const handleCreateBundle = async () => {
    if (selectedCards.length < 2) {
      toast.error("Select at least 2 projects to create a bundle");
      return;
    }

    try {
      const response = await fetch(
        `/api/iris/potential-bid-cards/bundle?user_id=${user?.id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_ids: selectedCards,
            bundle_name: "Inspiration Bundle",
            requires_general_contractor: selectedCards.length > 3
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success(`Bundle created with ${selectedCards.length} projects!`);
        setSelectedCards([]);
        loadPotentialBidCards(); // Refresh to show bundle status
      } else {
        throw new Error("Failed to create bundle");
      }
    } catch (error) {
      console.error("Error creating bundle:", error);
      toast.error("Failed to create project bundle");
    }
  };

  const handleConvertToBidCards = async () => {
    if (selectedCards.length === 0) {
      toast.error("Select projects to convert to bid cards");
      return;
    }

    try {
      const response = await fetch(
        `/api/iris/potential-bid-cards/convert-to-bid-cards?user_id=${user?.id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_ids: selectedCards,
            conversion_type: selectedCards.length > 1 ? "bundle" : "individual"
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success(`Converted ${result.total_converted} projects to bid cards!`);
        setSelectedCards([]);
        loadPotentialBidCards(); // Refresh to show converted status
      } else {
        throw new Error("Failed to convert to bid cards");
      }
    } catch (error) {
      console.error("Error converting to bid cards:", error);
      toast.error("Failed to convert projects");
    }
  };

  const getTradeColor = (trade: string) => {
    const colors: Record<string, string> = {
      'electrical': 'bg-yellow-100 text-yellow-800',
      'plumbing': 'bg-blue-100 text-blue-800',
      'painting': 'bg-purple-100 text-purple-800',
      'flooring': 'bg-brown-100 text-brown-800',
      'carpentry': 'bg-orange-100 text-orange-800',
      'landscaping': 'bg-green-100 text-green-800',
      'general_contractor': 'bg-gray-100 text-gray-800',
    };
    return colors[trade] || 'bg-gray-100 text-gray-600';
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple': return 'success';
      case 'moderate': return 'warning'; 
      case 'complex': return 'error';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'default';
      case 'refined': return 'processing';
      case 'bundled': return 'warning';
      case 'converted': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-semibold">Inspiration Projects</h2>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <Card key={i} style={{ width: '100%' }}>
              <Skeleton loading active avatar paragraph={{ rows: 4 }} />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (potentialBidCards.length === 0) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-semibold">Inspiration Projects</h2>
          </div>
        </div>
        
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div className="text-center">
              <p className="text-gray-600 mb-4">
                No inspiration projects yet. Upload photos and chat with IRIS to create projects from your design ideas.
              </p>
              <Button 
                type="primary" 
                icon={<Plus />}
                onClick={() => {
                  // Navigate to inspiration board or trigger IRIS chat
                  console.log("Navigate to create inspiration project");
                }}
              >
                Start an Inspiration Project
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-semibold">Inspiration Projects</h2>
          <Badge count={potentialBidCards.length} style={{ backgroundColor: '#7c3aed' }} />
        </div>

        {selectedCards.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">
              {selectedCards.length} selected
            </span>
            {selectedCards.length > 1 && (
              <Button onClick={handleCreateBundle} icon={<Package />}>
                Bundle Projects
              </Button>
            )}
            <Button 
              type="primary" 
              onClick={handleConvertToBidCards}
              icon={<ChevronRight />}
            >
              Convert to Bid Cards
            </Button>
          </div>
        )}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {potentialBidCards.map((card) => (
          <Card
            key={card.id}
            hoverable
            className={`relative ${selectedCards.includes(card.id) ? 'ring-2 ring-purple-500' : ''}`}
            cover={
              card.cover_photo_url ? (
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={card.cover_photo_url}
                    alt={card.title}
                    className="w-full h-full object-cover"
                  />
                  {card.ai_analysis.inspiration_match_score && (
                    <div className="absolute top-2 right-2">
                      <Badge 
                        count={`${Math.round(card.ai_analysis.inspiration_match_score * 100)}% match`}
                        style={{ backgroundColor: '#7c3aed' }}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-48 bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                  <Sparkles className="w-12 h-12 text-purple-400" />
                </div>
              )
            }
            actions={[
              <Tooltip title="Select for bundling">
                <Button
                  type={selectedCards.includes(card.id) ? "primary" : "default"}
                  icon={<CheckCircle />}
                  onClick={() => handleSelectCard(card.id)}
                />
              </Tooltip>,
              <Tooltip title="Chat about this project">
                <Button
                  icon={<MessageCircle />}
                  onClick={() => {
                    // Open IRIS chat with this card context
                    console.log("Start conversation about card:", card.id);
                  }}
                />
              </Tooltip>,
              <Tooltip title="View details">
                <Button
                  icon={<ChevronRight />}
                  onClick={() => handleCardClick(card)}
                />
              </Tooltip>
            ]}
          >
            <Card.Meta
              title={
                <div className="flex items-center justify-between">
                  <span className="truncate">{card.title}</span>
                  <Badge 
                    status={getStatusColor(card.status) as any} 
                    text={card.status}
                  />
                </div>
              }
              description={
                <div className="space-y-3">
                  {/* Location and Trade */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {card.room_location || card.property_area || "General"}
                    </span>
                    <Badge 
                      className={getTradeColor(card.primary_trade)}
                      text={card.primary_trade.replace('_', ' ')}
                    />
                  </div>

                  {/* Design Elements */}
                  {card.ai_analysis.design_elements && card.ai_analysis.design_elements.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Design Elements:</p>
                      <div className="flex flex-wrap gap-1">
                        {card.ai_analysis.design_elements.slice(0, 3).map((element, idx) => (
                          <span 
                            key={idx}
                            className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded"
                          >
                            {element}
                          </span>
                        ))}
                        {card.ai_analysis.design_elements.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{card.ai_analysis.design_elements.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Budget and Timeline */}
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    {card.budget_range_min && card.budget_range_max ? (
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        ${card.budget_range_min.toLocaleString()}-${card.budget_range_max.toLocaleString()}
                      </div>
                    ) : card.ai_analysis.estimated_cost ? (
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        {card.ai_analysis.estimated_cost}
                      </div>
                    ) : null}
                    
                    {card.estimated_timeline && (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {card.estimated_timeline}
                      </div>
                    )}
                  </div>

                  {/* Group Bidding Eligibility */}
                  {card.eligible_for_group_bidding && (
                    <div className="flex items-center gap-1 text-xs text-green-600">
                      <Users className="w-3 h-3" />
                      Group bidding eligible (15-25% savings)
                    </div>
                  )}

                  {/* Complexity and Priority */}
                  <div className="flex items-center justify-between">
                    <Badge 
                      color={getComplexityColor(card.project_complexity)}
                      text={`${card.project_complexity} project`}
                    />
                    {card.priority > 5 && (
                      <div className="flex items-center gap-1 text-xs text-orange-600">
                        <TrendingUp className="w-3 h-3" />
                        High priority
                      </div>
                    )}
                  </div>

                  {/* User Notes Preview */}
                  {card.user_scope_notes && (
                    <p className="text-xs text-gray-600 italic truncate">
                      "{card.user_scope_notes}"
                    </p>
                  )}
                </div>
              }
            />
          </Card>
        ))}
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {potentialBidCards.filter(c => c.status === 'draft').length}
            </div>
            <div className="text-sm text-gray-600">Draft Projects</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {potentialBidCards.filter(c => c.status === 'refined').length}
            </div>
            <div className="text-sm text-gray-600">Ready to Convert</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {potentialBidCards.filter(c => c.bundle_group_id).length}
            </div>
            <div className="text-sm text-gray-600">Bundled Projects</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {potentialBidCards.filter(c => c.eligible_for_group_bidding).length}
            </div>
            <div className="text-sm text-gray-600">Group Bidding Eligible</div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default PotentialBidCardsInspiration;