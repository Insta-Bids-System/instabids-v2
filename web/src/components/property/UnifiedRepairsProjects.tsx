import React, { useState, useEffect } from 'react';
import { 
  Wrench, 
  AlertTriangle, 
  Package, 
  MessageCircle, 
  CheckCircle,
  ChevronRight,
  ArrowDown,
  ArrowUp,
  Clock,
  Users,
  TrendingUp,
  Zap
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useIris } from '@/contexts/IrisContext';

interface MaintenanceIssue {
  id: string;
  photo_id: string;
  photo_url: string;
  photo_filename: string;
  description: string;
  severity: "low" | "medium" | "high" | "urgent";
  type: "maintenance" | "repair" | "safety" | "cosmetic";
  confidence?: number;
  estimated_cost?: "low" | "medium" | "high";
  detected_at: string;
  trade_type?: string; // For grouping into projects
}

interface PotentialBidCard {
  id: string;
  title: string;
  trade_type: string;
  repair_items: MaintenanceIssue[];
  urgency_level: "low" | "medium" | "high" | "urgent";
  complexity: "simple" | "moderate" | "complex";
  eligible_for_group_bidding: boolean;
  status: "draft" | "ready" | "converted";
}

interface UnifiedRepairsProjectsProps {
  maintenanceIssues: MaintenanceIssue[];
  propertyId: string;
  userId: string;
}

const UnifiedRepairsProjects: React.FC<UnifiedRepairsProjectsProps> = ({
  maintenanceIssues,
  propertyId,
  userId
}) => {
  const { setIsIrisOpen, setPropertyContext, updateSession } = useIris();
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [showIndividualItems, setShowIndividualItems] = useState(true);
  const [potentialBidCards, setPotentialBidCards] = useState<PotentialBidCard[]>([]);
  const [expandedProjects, setExpandedProjects] = useState<string[]>([]);

  // Group maintenance issues by trade type into potential bid cards
  useEffect(() => {
    const groupedByTrade = maintenanceIssues.reduce((acc, issue) => {
      const tradeType = getTradeType(issue.type, issue.description);
      if (!acc[tradeType]) {
        acc[tradeType] = [];
      }
      acc[tradeType].push(issue);
      return acc;
    }, {} as Record<string, MaintenanceIssue[]>);

    const bidCards: PotentialBidCard[] = Object.entries(groupedByTrade).map(([trade, items]) => ({
      id: `project-${trade}`,
      title: `${formatTradeName(trade)} Project`,
      trade_type: trade,
      repair_items: items,
      urgency_level: getHighestUrgency(items),
      complexity: items.length > 3 ? "complex" : items.length > 1 ? "moderate" : "simple",
      eligible_for_group_bidding: items.length > 2,
      status: "draft"
    }));

    setPotentialBidCards(bidCards);
  }, [maintenanceIssues]);

  const getTradeType = (type: string, description: string): string => {
    const desc = description.toLowerCase();
    if (desc.includes('electrical') || desc.includes('outlet') || desc.includes('switch') || desc.includes('wiring')) return 'electrical';
    if (desc.includes('plumbing') || desc.includes('leak') || desc.includes('faucet') || desc.includes('drain') || desc.includes('pipe')) return 'plumbing';
    if (desc.includes('paint') || desc.includes('wall') || desc.includes('ceiling')) return 'painting';
    if (desc.includes('floor') || desc.includes('carpet') || desc.includes('tile')) return 'flooring';
    if (desc.includes('roof') || desc.includes('gutter')) return 'roofing';
    if (desc.includes('hvac') || desc.includes('heating') || desc.includes('cooling') || desc.includes('air')) return 'hvac';
    if (desc.includes('window') || desc.includes('door')) return 'carpentry';
    if (desc.includes('landscape') || desc.includes('yard') || desc.includes('garden')) return 'landscaping';
    return 'general';
  };

  const formatTradeName = (trade: string): string => {
    const names: Record<string, string> = {
      electrical: 'Electrical',
      plumbing: 'Plumbing', 
      painting: 'Painting',
      flooring: 'Flooring',
      roofing: 'Roofing',
      hvac: 'HVAC',
      carpentry: 'Carpentry',
      landscaping: 'Landscaping',
      general: 'General Repairs'
    };
    return names[trade] || trade;
  };

  const getHighestUrgency = (items: MaintenanceIssue[]): "low" | "medium" | "high" | "urgent" => {
    const levels = { urgent: 4, high: 3, medium: 2, low: 1 };
    const highest = Math.max(...items.map(item => levels[item.severity] || 1));
    return Object.keys(levels).find(key => levels[key as keyof typeof levels] === highest) as any || 'low';
  };


  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTradeColor = (trade: string) => {
    const colors: Record<string, string> = {
      electrical: 'bg-yellow-100 text-yellow-800',
      plumbing: 'bg-blue-100 text-blue-800', 
      painting: 'bg-purple-100 text-purple-800',
      flooring: 'bg-brown-100 text-brown-800',
      roofing: 'bg-slate-100 text-slate-800',
      hvac: 'bg-cyan-100 text-cyan-800',
      carpentry: 'bg-orange-100 text-orange-800',
      landscaping: 'bg-green-100 text-green-800',
      general: 'bg-gray-100 text-gray-800'
    };
    return colors[trade] || 'bg-gray-100 text-gray-600';
  };

  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleRemoveFromProject = (bidCardId: string, itemId: string) => {
    setPotentialBidCards(prev => 
      prev.map(card => 
        card.id === bidCardId 
          ? { ...card, repair_items: card.repair_items.filter(item => item.id !== itemId) }
          : card
      ).filter(card => card.repair_items.length > 0) // Remove empty projects
    );
    toast.success('Repair item removed from project');
  };

  const handleMoveToProject = (itemId: string, targetProjectId: string) => {
    const item = maintenanceIssues.find(issue => issue.id === itemId);
    if (!item) return;

    setPotentialBidCards(prev => {
      // Remove from current project
      const withoutItem = prev.map(card => ({
        ...card,
        repair_items: card.repair_items.filter(repairItem => repairItem.id !== itemId)
      }));

      // Add to target project
      return withoutItem.map(card => 
        card.id === targetProjectId 
          ? { ...card, repair_items: [...card.repair_items, item] }
          : card
      ).filter(card => card.repair_items.length > 0);
    });
    toast.success('Repair item moved to project');
  };

  const handleSmartPlacement = async (itemId: string) => {
    const item = maintenanceIssues.find(issue => issue.id === itemId);
    if (!item) return;

    // Use AI to determine best placement
    const suggestedTradeType = getTradeType(item.type, item.description);
    
    // Look for existing project of that trade type
    const existingProject = potentialBidCards.find(card => card.trade_type === suggestedTradeType);
    
    if (existingProject) {
      // Move to existing project
      handleMoveToProject(itemId, existingProject.id);
      toast.success(`Added to existing ${formatTradeName(suggestedTradeType)} project`);
    } else {
      // Create new project with intelligent trade type
      const newProject: PotentialBidCard = {
        id: `project-${suggestedTradeType}-${Date.now()}`,
        title: `${formatTradeName(suggestedTradeType)} Project`,
        trade_type: suggestedTradeType,
        repair_items: [item],
        urgency_level: item.severity,
        complexity: "simple",
        eligible_for_group_bidding: false,
        status: "draft"
      };

      // Remove from existing projects and add new project
      setPotentialBidCards(prev => {
        const withoutItem = prev.map(card => ({
          ...card,
          repair_items: card.repair_items.filter(repairItem => repairItem.id !== itemId)
        })).filter(card => card.repair_items.length > 0);

        return [...withoutItem, newProject];
      });
      
      toast.success(`Created new ${formatTradeName(suggestedTradeType)} project`);
    }
  };

  const toggleProjectExpansion = (projectId: string) => {
    setExpandedProjects(prev => 
      prev.includes(projectId) 
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    );
  };

  const handleChatAboutProject = (bidCard: PotentialBidCard) => {
    // Set up IRIS context with detailed project information
    const projectContext = {
      type: 'maintenance_project',
      property_id: propertyId,
      project_title: bidCard.title,
      trade_type: bidCard.trade_type,
      urgency_level: bidCard.urgency_level,
      complexity: bidCard.complexity,
      repair_items: bidCard.repair_items.map(item => ({
        id: item.id,
        description: item.description,
        severity: item.severity,
        photo_url: item.photo_url,
        photo_filename: item.photo_filename,
        detected_at: item.detected_at
      })),
      total_items: bidCard.repair_items.length,
      photos: bidCard.repair_items.map(item => item.photo_url),
      context_message: `I want to discuss the ${bidCard.title} which includes ${bidCard.repair_items.length} repair items. The project has ${bidCard.urgency_level} urgency and ${bidCard.complexity} complexity. The repairs include: ${bidCard.repair_items.map(item => item.description).join(', ')}.`
    };

    // Update IRIS session with project context
    updateSession({
      context_type: 'property_maintenance',
      project_context: projectContext,
      last_action: 'discuss_project',
      timestamp: new Date().toISOString()
    });

    // Set property context and open IRIS
    setPropertyContext(propertyId);
    setIsIrisOpen(true);
    
    toast.success(`Opening IRIS chat for ${bidCard.title}`);
  };

  const handleOpenGeneralChat = () => {
    const generalContext = {
      type: 'property_maintenance',
      property_id: propertyId,
      total_issues: maintenanceIssues.length,
      total_projects: potentialBidCards.length,
      context_message: `I want to discuss maintenance and repairs for this property. We have ${maintenanceIssues.length} identified repair items grouped into ${potentialBidCards.length} potential projects.`
    };

    updateSession({
      context_type: 'property_maintenance', 
      general_context: generalContext,
      last_action: 'open_general_chat',
      timestamp: new Date().toISOString()
    });

    setPropertyContext(propertyId);
    setIsIrisOpen(true);
    toast.success('Opening IRIS chat for property maintenance');
  };

  const handleGetQuotes = async (bidCard: PotentialBidCard) => {
    try {
      const response = await fetch(`/api/properties/${propertyId}/create-project-bid-card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          project_type: bidCard.trade_type,
          repair_items: bidCard.repair_items.map(item => item.id),
          title: bidCard.title,
          urgency_level: bidCard.urgency_level
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(`Bid card created for ${bidCard.title}! Contractors will be contacted soon.`);
        
        // Update status
        setPotentialBidCards(prev => 
          prev.map(card => 
            card.id === bidCard.id 
              ? { ...card, status: "converted" as const }
              : card
          )
        );
      } else {
        throw new Error('Failed to create bid card');
      }
    } catch (error) {
      console.error('Error creating bid card:', error);
      toast.error('Failed to create bid card. Please try again.');
    }
  };

  if (maintenanceIssues.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">🔧</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No repairs needed</h3>
        <p className="text-gray-600 mb-4">Upload photos and chat with IRIS to detect maintenance issues with AI.</p>
        <button
          onClick={handleOpenGeneralChat}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          💬 Chat with IRIS
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Wrench className="w-6 h-6 text-orange-600" />
          <h2 className="text-xl font-semibold">Repairs & Projects</h2>
          <span className="text-sm text-gray-500">
            {potentialBidCards.length} projects • {maintenanceIssues.length} items
          </span>
        </div>
        <button
          onClick={handleOpenGeneralChat}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <MessageCircle className="w-4 h-4" />
          Chat with IRIS
        </button>
      </div>

      {/* Potential Bid Cards */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
          <Package className="w-5 h-5 text-green-600" />
          Potential Projects
          <span className="text-sm text-gray-500">Grouped by trade type</span>
        </h3>
        
        {potentialBidCards.map((bidCard) => (
          <div key={bidCard.id} className="bg-white rounded-lg border-2 border-green-200 p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h4 className="text-lg font-semibold text-gray-900">{bidCard.title}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTradeColor(bidCard.trade_type)}`}>
                    {formatTradeName(bidCard.trade_type)}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(bidCard.urgency_level)}`}>
                    {bidCard.urgency_level} urgency
                  </span>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  <span className="flex items-center gap-1">
                    <Wrench className="w-4 h-4" />
                    {bidCard.repair_items.length} repair{bidCard.repair_items.length > 1 ? 's' : ''}
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    {bidCard.complexity} project
                  </span>
                  {bidCard.eligible_for_group_bidding && (
                    <span className="flex items-center gap-1 text-green-600">
                      <Users className="w-4 h-4" />
                      Group bidding eligible
                    </span>
                  )}
                </div>

                {/* Expandable repair items list */}
                <div className="mb-3">
                  <button
                    onClick={() => toggleProjectExpansion(bidCard.id)}
                    className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
                  >
                    {expandedProjects.includes(bidCard.id) ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                    {expandedProjects.includes(bidCard.id) ? 'Hide' : 'Show'} repair items ({bidCard.repair_items.length})
                  </button>
                  
                  {expandedProjects.includes(bidCard.id) && (
                    <div className="mt-3 space-y-2 border-l-2 border-gray-200 pl-4">
                      {bidCard.repair_items.map((item) => (
                        <div key={item.id} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{item.description}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(item.severity)}`}>
                                {item.severity}
                              </span>
                              <span className="text-xs text-gray-500">📸 {item.photo_filename}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleRemoveFromProject(bidCard.id, item.id)}
                            className="text-red-600 hover:text-red-800 text-sm px-2 py-1 rounded hover:bg-red-50"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleChatAboutProject(bidCard)}
                  className="bg-blue-100 text-blue-700 px-3 py-2 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2"
                >
                  <MessageCircle className="w-4 h-4" />
                  Discuss
                </button>
                {bidCard.status === "converted" ? (
                  <span className="bg-green-100 text-green-700 px-3 py-2 rounded-lg font-medium">
                    ✓ Bid Card Created
                  </span>
                ) : (
                  <button
                    onClick={() => handleGetQuotes(bidCard)}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
                  >
                    Get Quotes
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Individual Repair Items */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            Individual Repair Items
          </h3>
          <button
            onClick={() => setShowIndividualItems(!showIndividualItems)}
            className="text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            {showIndividualItems ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
            {showIndividualItems ? 'Hide' : 'Show'} Details
          </button>
        </div>

        {showIndividualItems && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {maintenanceIssues.map((issue) => {
              const currentProject = potentialBidCards.find(card => 
                card.repair_items.some(item => item.id === issue.id)
              );
              
              return (
                <div key={issue.id} className="bg-white rounded-lg border p-4 shadow-sm">
                  <div className="flex gap-3 mb-3">
                    <img 
                      src={issue.photo_url} 
                      alt={issue.description}
                      className="w-16 h-16 rounded-lg object-cover cursor-pointer hover:opacity-90"
                      onClick={() => window.open(issue.photo_url, '_blank')}
                    />
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 text-sm mb-1 truncate">
                        {issue.description}
                      </h4>
                      <div className="flex flex-wrap gap-1 mb-2">
                        <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(issue.severity)}`}>
                          {issue.severity}
                        </span>
                        <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                          {issue.type}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">
                        📸 {issue.photo_filename}
                      </p>
                      
                      {/* Current Project Assignment */}
                      {currentProject && (
                        <div className="text-xs text-blue-600 mb-2">
                          📋 In: {currentProject.title}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Transfer Controls */}
                  <div className="space-y-2">
                    {/* Move to existing project */}
                    {potentialBidCards.filter(card => !card.repair_items.some(item => item.id === issue.id)).length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-xs text-gray-600 font-medium">Move to:</span>
                        {potentialBidCards.filter(card => !card.repair_items.some(item => item.id === issue.id)).map((project) => (
                          <button
                            key={project.id}
                            onClick={() => handleMoveToProject(issue.id, project.id)}
                            className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded hover:bg-blue-200"
                          >
                            {formatTradeName(project.trade_type)}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {/* Smart placement button */}
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleSmartPlacement(issue.id)}
                        className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded hover:bg-green-200 flex items-center gap-1"
                      >
                        <Zap className="w-3 h-3" />
                        Smart Place
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default UnifiedRepairsProjects;