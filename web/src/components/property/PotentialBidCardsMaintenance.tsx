import {
  Wrench,
  AlertTriangle,
  Clock,
  CheckCircle,
  MessageCircle,
  Package,
  DollarSign,
  Calendar,
  TrendingUp,
  Users,
  ChevronRight,
  Plus,
  Filter,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Card, Badge, Button, Select, Tooltip, Empty, Skeleton, Alert } from "antd";
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
    severity_assessment?: "low" | "medium" | "high" | "urgent";
    safety_concerns?: string[];
    maintenance_recommendations?: string[];
    immediate_action_required?: boolean;
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

interface PotentialBidCardsMaintenanceProps {
  className?: string;
  propertyId?: string;
}

const PotentialBidCardsMaintenance: React.FC<PotentialBidCardsMaintenanceProps> = ({
  className = "",
  propertyId
}) => {
  const { user } = useAuth();
  const [potentialBidCards, setPotentialBidCards] = useState<PotentialBidCard[]>([]);
  const [filteredCards, setFilteredCards] = useState<PotentialBidCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCards, setSelectedCards] = useState<string[]>([]);
  const [filterUrgency, setFilterUrgency] = useState<string>("all");
  const [filterTrade, setFilterTrade] = useState<string>("all");

  const loadPotentialBidCards = async () => {
    if (!user) return;

    try {
      setLoading(true);
      
      // Get maintenance-focused potential bid cards
      const response = await fetch(
        `/api/iris/potential-bid-cards/${user.id}?component_type=maintenance`
      );
      
      if (response.ok) {
        const data = await response.json();
        setPotentialBidCards(data.potential_bid_cards || []);
        setFilteredCards(data.potential_bid_cards || []);
      } else {
        throw new Error("Failed to load potential bid cards");
      }
    } catch (error) {
      console.error("Error loading potential bid cards:", error);
      toast.error("Failed to load maintenance projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPotentialBidCards();
  }, [user]);

  // Filter cards based on selected filters
  useEffect(() => {
    let filtered = potentialBidCards;

    if (filterUrgency !== "all") {
      filtered = filtered.filter(card => card.urgency_level === filterUrgency);
    }

    if (filterTrade !== "all") {
      filtered = filtered.filter(card => 
        card.primary_trade === filterTrade || 
        card.secondary_trades.includes(filterTrade)
      );
    }

    setFilteredCards(filtered);
  }, [potentialBidCards, filterUrgency, filterTrade]);

  const handleCardClick = (card: PotentialBidCard) => {
    // Open detailed view or start conversation about this maintenance issue
    console.log("Opening maintenance card details:", card);
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
      toast.error("Select at least 2 maintenance items to create a bundle");
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
            bundle_name: "Maintenance Bundle",
            requires_general_contractor: selectedCards.length > 4
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success(`Maintenance bundle created with ${selectedCards.length} items!`);
        setSelectedCards([]);
        loadPotentialBidCards(); // Refresh to show bundle status
      } else {
        throw new Error("Failed to create bundle");
      }
    } catch (error) {
      console.error("Error creating bundle:", error);
      toast.error("Failed to create maintenance bundle");
    }
  };

  const handleConvertToBidCards = async () => {
    if (selectedCards.length === 0) {
      toast.error("Select maintenance items to convert to bid cards");
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
        toast.success(`Converted ${result.total_converted} maintenance items to bid cards!`);
        setSelectedCards([]);
        loadPotentialBidCards(); // Refresh to show converted status
      } else {
        throw new Error("Failed to convert to bid cards");
      }
    } catch (error) {
      console.error("Error converting to bid cards:", error);
      toast.error("Failed to convert maintenance items");
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'urgent': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'processing';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  const getTradeColor = (trade: string) => {
    const colors: Record<string, string> = {
      'electrical': 'bg-yellow-100 text-yellow-800',
      'plumbing': 'bg-blue-100 text-blue-800',
      'hvac': 'bg-cyan-100 text-cyan-800',
      'roofing': 'bg-slate-100 text-slate-800',
      'painting': 'bg-purple-100 text-purple-800',
      'flooring': 'bg-brown-100 text-brown-800',
      'carpentry': 'bg-orange-100 text-orange-800',
      'landscaping': 'bg-green-100 text-green-800',
      'cleaning': 'bg-teal-100 text-teal-800',
      'general_contractor': 'bg-gray-100 text-gray-800',
    };
    return colors[trade] || 'bg-gray-100 text-gray-600';
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

  const urgentIssues = filteredCards.filter(card => 
    card.urgency_level === 'urgent' || 
    card.ai_analysis.immediate_action_required
  );

  const availableTrades = Array.from(new Set(
    potentialBidCards.flatMap(card => [card.primary_trade, ...card.secondary_trades])
  )).filter(Boolean);

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wrench className="w-6 h-6 text-orange-600" />
            <h2 className="text-xl font-semibold">Maintenance & Repairs</h2>
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
            <Wrench className="w-6 h-6 text-orange-600" />
            <h2 className="text-xl font-semibold">Maintenance & Repairs</h2>
          </div>
        </div>
        
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div className="text-center">
              <p className="text-gray-600 mb-4">
                No maintenance issues detected yet. Upload property photos to have IRIS identify potential repairs and improvements.
              </p>
              <Button 
                type="primary" 
                icon={<Plus />}
                onClick={() => {
                  // Navigate to property photos or trigger photo upload
                  console.log("Navigate to upload property photos");
                }}
              >
                Upload Property Photos
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
          <Wrench className="w-6 h-6 text-orange-600" />
          <h2 className="text-xl font-semibold">Maintenance & Repairs</h2>
          <Badge count={filteredCards.length} style={{ backgroundColor: '#ea580c' }} />
        </div>

        {selectedCards.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">
              {selectedCards.length} selected
            </span>
            {selectedCards.length > 1 && (
              <Button onClick={handleCreateBundle} icon={<Package />}>
                Bundle Items
              </Button>
            )}
            <Button 
              type="primary" 
              onClick={handleConvertToBidCards}
              icon={<ChevronRight />}
            >
              Get Quotes
            </Button>
          </div>
        )}
      </div>

      {/* Urgent Issues Alert */}
      {urgentIssues.length > 0 && (
        <Alert
          message={`${urgentIssues.length} Urgent Issue${urgentIssues.length > 1 ? 's' : ''} Require Immediate Attention`}
          description="These issues may pose safety risks or could lead to more expensive repairs if not addressed quickly."
          type="error"
          showIcon
          action={
            <Button 
              size="small" 
              type="primary" 
              danger
              onClick={() => {
                setSelectedCards(urgentIssues.map(card => card.id));
                handleConvertToBidCards();
              }}
            >
              Get Emergency Quotes
            </Button>
          }
        />
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <Filter className="w-4 h-4 text-gray-600" />
        <Select
          value={filterUrgency}
          onChange={setFilterUrgency}
          style={{ width: 120 }}
          options={[
            { value: "all", label: "All Urgency" },
            { value: "urgent", label: "Urgent" },
            { value: "high", label: "High" },
            { value: "medium", label: "Medium" },
            { value: "low", label: "Low" }
          ]}
        />
        <Select
          value={filterTrade}
          onChange={setFilterTrade}
          style={{ width: 150 }}
          options={[
            { value: "all", label: "All Trades" },
            ...availableTrades.map(trade => ({
              value: trade,
              label: trade.replace('_', ' ').toUpperCase()
            }))
          ]}
        />
        <span className="text-sm text-gray-600">
          Showing {filteredCards.length} of {potentialBidCards.length} items
        </span>
      </div>

      {/* Maintenance Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCards.map((card) => (
          <Card
            key={card.id}
            hoverable
            className={`relative ${selectedCards.includes(card.id) ? 'ring-2 ring-orange-500' : ''} ${
              card.urgency_level === 'urgent' ? 'border-red-300' : ''
            }`}
            cover={
              card.cover_photo_url ? (
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={card.cover_photo_url}
                    alt={card.title}
                    className="w-full h-full object-cover"
                  />
                  {card.urgency_level === 'urgent' && (
                    <div className="absolute top-2 left-2">
                      <Badge 
                        count="URGENT"
                        style={{ backgroundColor: '#dc2626' }}
                      />
                    </div>
                  )}
                  {card.ai_analysis.immediate_action_required && (
                    <div className="absolute top-2 right-2">
                      <AlertTriangle className="w-6 h-6 text-red-500 bg-white rounded-full p-1" />
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-48 bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
                  <Wrench className="w-12 h-12 text-orange-400" />
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
              <Tooltip title="Discuss with IRIS">
                <Button
                  icon={<MessageCircle />}
                  onClick={() => {
                    // Open IRIS chat with this maintenance card context
                    console.log("Start conversation about maintenance card:", card.id);
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
                      {card.room_location || card.property_area || "Property"}
                    </span>
                    <Badge 
                      className={getTradeColor(card.primary_trade)}
                      text={card.primary_trade.replace('_', ' ')}
                    />
                  </div>

                  {/* Urgency and Complexity */}
                  <div className="flex items-center justify-between">
                    <Badge 
                      color={getUrgencyColor(card.urgency_level)}
                      text={`${card.urgency_level} urgency`}
                    />
                    <span className="text-xs text-gray-500">
                      {card.project_complexity} project
                    </span>
                  </div>

                  {/* Detected Issues */}
                  {card.ai_analysis.detected_issues && card.ai_analysis.detected_issues.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Issues Detected:</p>
                      <div className="flex flex-wrap gap-1">
                        {card.ai_analysis.detected_issues.slice(0, 2).map((issue, idx) => (
                          <span 
                            key={idx}
                            className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded"
                          >
                            {issue}
                          </span>
                        ))}
                        {card.ai_analysis.detected_issues.length > 2 && (
                          <span className="text-xs text-gray-400">
                            +{card.ai_analysis.detected_issues.length - 2} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Safety Concerns */}
                  {card.ai_analysis.safety_concerns && card.ai_analysis.safety_concerns.length > 0 && (
                    <div className="flex items-center gap-1 text-xs text-red-600">
                      <AlertTriangle className="w-3 h-3" />
                      Safety concerns identified
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

                  {/* High Priority Indicator */}
                  {card.priority > 7 && (
                    <div className="flex items-center gap-1 text-xs text-orange-600">
                      <TrendingUp className="w-3 h-3" />
                      High priority maintenance
                    </div>
                  )}

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
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-8">
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {potentialBidCards.filter(c => c.urgency_level === 'urgent').length}
            </div>
            <div className="text-sm text-gray-600">Urgent</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {potentialBidCards.filter(c => c.urgency_level === 'high').length}
            </div>
            <div className="text-sm text-gray-600">High Priority</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {potentialBidCards.filter(c => c.status === 'refined').length}
            </div>
            <div className="text-sm text-gray-600">Ready for Quotes</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {potentialBidCards.filter(c => c.bundle_group_id).length}
            </div>
            <div className="text-sm text-gray-600">Bundled Items</div>
          </div>
        </Card>
        
        <Card size="small">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {potentialBidCards.filter(c => c.eligible_for_group_bidding).length}
            </div>
            <div className="text-sm text-gray-600">Group Eligible</div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default PotentialBidCardsMaintenance;