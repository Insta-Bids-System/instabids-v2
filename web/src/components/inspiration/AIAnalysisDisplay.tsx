import { Eye, Home, Lightbulb, Palette, Sparkles } from "lucide-react";
import type React from "react";

interface AnalysisData {
  description?: string;
  generated_tags?: string[];
  design_elements?: string[];
  color_palette?: Array<{ color: string; hex: string }>;
  suggestions?: string[];
}

interface AIAnalysisDisplayProps {
  analysis: AnalysisData | string | null;
  imageType: "current" | "inspiration" | "vision";
}

const AIAnalysisDisplay: React.FC<AIAnalysisDisplayProps> = ({ analysis, imageType }) => {
  if (!analysis) return null;

  // Parse the analysis if it's a string
  const parsedAnalysis = typeof analysis === "string" ? JSON.parse(analysis) : analysis;

  // Extract key information from the analysis
  const description = parsedAnalysis.description || "";
  const tags = parsedAnalysis.generated_tags || [];
  const designElements = parsedAnalysis.design_elements || [];
  const colors = parsedAnalysis.color_palette || [];
  const suggestions = parsedAnalysis.suggestions || [];
  const materials = parsedAnalysis.materials || [];

  const getIconForType = () => {
    switch (imageType) {
      case "current":
        return <Home className="w-4 h-4" />;
      case "vision":
        return <Eye className="w-4 h-4" />;
      default:
        return <Sparkles className="w-4 h-4" />;
    }
  };

  return (
    <div className="absolute inset-0 bg-black bg-opacity-75 p-4 opacity-0 hover:opacity-100 transition-opacity duration-300 overflow-y-auto">
      <div className="text-white space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          {getIconForType()}
          <h3 className="font-medium text-lg">AI Analysis</h3>
        </div>

        {/* Description */}
        {description && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300">What I See:</h4>
            <p className="text-sm leading-relaxed">{description}</p>
          </div>
        )}

        {/* Design Elements */}
        {designElements.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300">Key Elements:</h4>
            <div className="flex flex-wrap gap-1">
              {designElements.map((element: string, idx: number) => (
                <span key={idx} className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">
                  {element}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Colors */}
        {colors.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300 flex items-center gap-1">
              <Palette className="w-3 h-3" /> Colors:
            </h4>
            <div className="flex gap-2">
              {colors.map((color: { color: string; hex: string }, idx: number) => (
                <div key={idx} className="text-xs">
                  <div
                    className="w-8 h-8 rounded border border-white border-opacity-50 mb-1"
                    style={{ backgroundColor: color.hex || color }}
                  />
                  <span className="text-[10px]">{color.name || color}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Materials */}
        {materials.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300">Materials:</h4>
            <div className="text-xs space-y-1">
              {materials.map((material: string, idx: number) => (
                <div key={idx}>• {material}</div>
              ))}
            </div>
          </div>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && imageType === "current" && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300 flex items-center gap-1">
              <Lightbulb className="w-3 h-3" /> Ideas:
            </h4>
            <div className="text-xs space-y-1">
              {suggestions.map((suggestion: string, idx: number) => (
                <div key={idx}>• {suggestion}</div>
              ))}
            </div>
          </div>
        )}

        {/* Smart Tags */}
        {tags.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1 text-gray-300">Tags:</h4>
            <div className="flex flex-wrap gap-1">
              {tags.map((tag: string, idx: number) => (
                <span key={idx} className="text-xs bg-blue-500 bg-opacity-30 px-2 py-1 rounded">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAnalysisDisplay;
