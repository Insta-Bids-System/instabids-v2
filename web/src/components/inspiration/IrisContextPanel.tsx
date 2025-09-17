import { Home, Sparkles, Image as ImageIcon, TrendingUp, CheckCircle, AlertCircle } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

interface IrisContextPanelProps {
  boardId: string;
  boardTitle: string;
  images: any[];
  boardConversation: any;
  onCreateBidCard: () => void;
}

interface ProjectContext {
  currentSpaceAnalysis: string[];
  inspirationThemes: string[];
  identifiedElements: {
    category: string;
    items: string[];
  }[];
  projectScope: string;
  estimatedBudget?: string;
  confidence: number;
}

const IrisContextPanel: React.FC<IrisContextPanelProps> = ({
  boardId,
  boardTitle,
  images,
  boardConversation,
  onCreateBidCard
}) => {
  const { user } = useAuth();
  const [projectContext, setProjectContext] = useState<ProjectContext>({
    currentSpaceAnalysis: [],
    inspirationThemes: [],
    identifiedElements: [],
    projectScope: "Gathering information...",
    confidence: 0
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Update context whenever images or conversation changes
  useEffect(() => {
    updateProjectContext();
  }, [images, boardConversation]);

  const updateProjectContext = () => {
    // Extract context from images and conversation
    const currentImages = images.filter(img => img.tags?.includes("current"));
    const inspirationImages = images.filter(img => 
      !img.tags?.includes("current") && !img.tags?.includes("vision")
    );

    // Build current space analysis
    const spaceAnalysis = currentImages.length > 0 ? [
      `${currentImages.length} photo${currentImages.length > 1 ? 's' : ''} of existing space`,
      currentImages[0]?.ai_analysis?.condition || "Space condition being assessed",
      currentImages[0]?.ai_analysis?.issues?.join(", ") || "Identifying improvement areas"
    ] : ["No current space photos yet"];

    // Build inspiration themes
    const themes = [];
    if (inspirationImages.length > 0) {
      themes.push(`${inspirationImages.length} inspiration image${inspirationImages.length > 1 ? 's' : ''} collected`);
      
      // Extract common themes from AI analysis
      const styles = new Set<string>();
      const colors = new Set<string>();
      const materials = new Set<string>();
      
      inspirationImages.forEach(img => {
        if (img.ai_analysis) {
          img.ai_analysis.style && styles.add(img.ai_analysis.style);
          img.ai_analysis.colors?.forEach((c: string) => colors.add(c));
          img.ai_analysis.materials?.forEach((m: string) => materials.add(m));
        }
      });

      if (styles.size > 0) themes.push(`Style: ${Array.from(styles).join(", ")}`);
      if (colors.size > 0) themes.push(`Colors: ${Array.from(colors).slice(0, 3).join(", ")}`);
      if (materials.size > 0) themes.push(`Materials: ${Array.from(materials).slice(0, 3).join(", ")}`);
    } else {
      themes.push("No inspiration images yet");
    }

    // Identify specific elements
    const elements = [];
    
    // Extract from persistent context if available
    if (boardConversation?.persistent_context) {
      const ctx = boardConversation.persistent_context;
      
      if (ctx.identified_features) {
        elements.push({
          category: "Desired Features",
          items: ctx.identified_features
        });
      }
      
      if (ctx.materials) {
        elements.push({
          category: "Materials & Finishes",
          items: ctx.materials
        });
      }
      
      if (ctx.style_preferences) {
        elements.push({
          category: "Style Preferences",
          items: ctx.style_preferences
        });
      }
    }

    // If no persistent context yet, use basic analysis
    if (elements.length === 0 && inspirationImages.length > 0) {
      elements.push({
        category: "Gathering Preferences",
        items: ["Analyzing uploaded images...", "Building project understanding..."]
      });
    }

    // Build project scope description
    let scope = "Gathering project information...";
    if (currentImages.length > 0 && inspirationImages.length > 0) {
      scope = `Transform existing ${boardTitle.toLowerCase()} based on ${inspirationImages.length} inspiration references`;
    } else if (inspirationImages.length > 0) {
      scope = `Design new ${boardTitle.toLowerCase()} based on collected inspiration`;
    } else if (currentImages.length > 0) {
      scope = `Improve existing ${boardTitle.toLowerCase()} space`;
    }

    // Calculate confidence (0-1)
    const confidence = boardConversation?.confidence_score || 
      (currentImages.length * 0.2 + inspirationImages.length * 0.15 + elements.length * 0.1);

    setProjectContext({
      currentSpaceAnalysis: spaceAnalysis,
      inspirationThemes: themes,
      identifiedElements: elements,
      projectScope: scope,
      estimatedBudget: boardConversation?.persistent_context?.estimated_budget,
      confidence: Math.min(confidence, 1)
    });
  };

  // Trigger analysis when new images are added
  const triggerAnalysis = async () => {
    if (isAnalyzing) return;
    
    setIsAnalyzing(true);
    
    // Call the board analysis endpoint to update context
    try {
      const response = await fetch(`/api/iris/board/${boardId}/update-context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_count: images.length,
          current_images: images.filter(img => img.tags?.includes("current")).length,
          inspiration_images: images.filter(img => !img.tags?.includes("current") && !img.tags?.includes("vision")).length
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Context updated:", data);
      }
    } catch (error) {
      console.error("Error updating context:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (images.length > 0) {
      triggerAnalysis();
    }
  }, [images.length]);

  const confidencePercentage = Math.round(projectContext.confidence * 100);
  const isReady = confidencePercentage >= 75;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Project Context</h3>
              <p className="text-xs text-gray-600">IRIS is building your project understanding</p>
            </div>
          </div>
          
          {/* Confidence Indicator */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4 text-gray-500" />
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    isReady ? "bg-green-500" : 
                    confidencePercentage >= 50 ? "bg-yellow-500" : "bg-gray-400"
                  }`}
                  style={{ width: `${confidencePercentage}%` }}
                />
              </div>
              <span className="text-xs text-gray-600">{confidencePercentage}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Current Space Section */}
      <div className="p-4 border-b">
        <div className="flex items-start gap-3">
          <Home className="w-5 h-5 text-gray-400 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Current Space</h4>
            <ul className="space-y-1">
              {projectContext.currentSpaceAnalysis.map((item, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-1">
                  <span className="text-gray-400 mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Inspiration Themes Section */}
      <div className="p-4 border-b">
        <div className="flex items-start gap-3">
          <ImageIcon className="w-5 h-5 text-gray-400 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Inspiration Themes</h4>
            <ul className="space-y-1">
              {projectContext.inspirationThemes.map((theme, idx) => (
                <li key={idx} className="text-sm text-gray-600 flex items-start gap-1">
                  <span className="text-gray-400 mt-1">•</span>
                  <span>{theme}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Identified Elements Section */}
      {projectContext.identifiedElements.length > 0 && (
        <div className="p-4 border-b">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Identified Elements</h4>
          <div className="space-y-3">
            {projectContext.identifiedElements.map((element, idx) => (
              <div key={idx}>
                <h5 className="text-xs font-medium text-gray-700 mb-1">{element.category}</h5>
                <div className="flex flex-wrap gap-1">
                  {element.items.map((item, itemIdx) => (
                    <span 
                      key={itemIdx}
                      className="inline-block px-2 py-1 bg-gray-100 text-xs text-gray-700 rounded"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Project Scope */}
      <div className="p-4 border-b bg-gray-50">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Project Scope</h4>
        <p className="text-sm text-gray-700">{projectContext.projectScope}</p>
        {projectContext.estimatedBudget && (
          <p className="text-sm text-gray-600 mt-2">
            Estimated Budget: <span className="font-medium">{projectContext.estimatedBudget}</span>
          </p>
        )}
      </div>

      {/* Action Section */}
      <div className="p-4 bg-gray-50">
        {isReady ? (
          <button
            type="button"
            onClick={onCreateBidCard}
            className="w-full flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-2.5 rounded-lg hover:bg-green-700 transition-colors"
          >
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Create Bid Card</span>
          </button>
        ) : (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <AlertCircle className="w-4 h-4" />
            <span>Add more photos to build project context ({75 - confidencePercentage}% more needed)</span>
          </div>
        )}
        
        {isAnalyzing && (
          <div className="mt-2 text-xs text-gray-500 text-center">
            IRIS is analyzing your latest updates...
          </div>
        )}
      </div>
    </div>
  );
};

export default IrisContextPanel;