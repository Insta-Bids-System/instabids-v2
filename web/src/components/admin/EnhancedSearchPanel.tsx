import type React from "react";
import { useState, useEffect } from "react";
import LoadingSpinner from "../ui/LoadingSpinner";

interface SearchResult {
  bid_cards: Array<{
    id: string;
    bid_card_number: string;
    user_id?: string;
    homeowner_name?: string;
    project_type: string;
    status: string;
    budget_min?: number;
    budget_max?: number;
    created_at: string;
    location_city?: string;
    location_state?: string;
  }>;
  homeowners: Array<{
    user_id: string;
    homeowner_name: string;
    bid_card_count: number;
    email?: string;
    phone?: string;
  }>;
  contractors: Array<{
    id: string;
    name: string;
    company?: string;
    location?: string;
    specialties?: string;
    email?: string;
    phone?: string;
    tier?: string;
    response_rate?: number;
  }>;
  total_bid_cards: number;
  total_homeowners: number;
  total_contractors: number;
  search_query: string;
  search_type: string;
}

interface HomeownerSummary {
  user_id: string;
  homeowner_name: string;
  profile?: {
    email?: string;
    phone?: string;
    full_name?: string;
    created_at?: string;
  };
  statistics: {
    total_bid_cards: number;
    status_breakdown: Record<string, number>;
    total_budget_range: {
      min: number;
      max: number;
    };
    project_types: string[];
    first_bid_card?: string;
    latest_bid_card?: string;
  };
  recent_bid_cards: Array<{
    bid_card_number: string;
    project_type: string;
    status: string;
    created_at: string;
  }>;
}

interface AutocompleteResponse {
  suggestions: string[];
}

const EnhancedSearchPanel: React.FC = () => {
  const [searchType, setSearchType] = useState<"unified" | "bid_cards" | "homeowners" | "contractors">("unified");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedHomeowner, setSelectedHomeowner] = useState<HomeownerSummary | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [autocompleteResults, setAutocompleteResults] = useState<string[]>([]);
  const [showAutocomplete, setShowAutocomplete] = useState(false);

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim().length >= 2) {
        performSearch();
        fetchAutocomplete();
      } else {
        setSearchResults(null);
        setAutocompleteResults([]);
        setShowAutocomplete(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchType]);

  const performSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      let endpoint = "";
      let params = new URLSearchParams();

      switch (searchType) {
        case "unified":
          endpoint = "/api/admin/search/unified";
          params.append("query", searchQuery);
          break;
        case "bid_cards":
          endpoint = "/api/admin/search/bid-cards/by-homeowner";
          params.append("homeowner_name", searchQuery);
          break;
        case "homeowners":
          endpoint = "/api/admin/search/homeowners";
          params.append("search_term", searchQuery);
          break;
        case "contractors":
          endpoint = "/api/admin/search/contractors";
          params.append("search_term", searchQuery);
          break;
      }

      const response = await fetch(`${endpoint}?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        
        if (searchType === "unified") {
          setSearchResults({
            ...data,
            contractors: data.contractors || [],
            total_contractors: data.total_contractors || 0
          });
        } else if (searchType === "bid_cards") {
          setSearchResults({
            bid_cards: data.bid_cards || [],
            homeowners: [],
            contractors: [],
            total_bid_cards: data.total || 0,
            total_homeowners: 0,
            total_contractors: 0,
            search_query: searchQuery,
            search_type: "bid_cards"
          });
        } else if (searchType === "homeowners") {
          setSearchResults({
            bid_cards: [],
            homeowners: data.homeowners || [],
            contractors: [],
            total_bid_cards: 0,
            total_homeowners: data.total || 0,
            total_contractors: 0,
            search_query: searchQuery,
            search_type: "homeowners"
          });
        } else if (searchType === "contractors") {
          setSearchResults({
            bid_cards: [],
            homeowners: [],
            contractors: data.contractors || [],
            total_bid_cards: 0,
            total_homeowners: 0,
            total_contractors: data.total || 0,
            search_query: searchQuery,
            search_type: "contractors"
          });
        }
      }
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const fetchAutocomplete = async () => {
    if (!searchQuery.trim() || searchQuery.length < 2) return;

    try {
      const field = searchType === "bid_cards" ? "homeowner_name" : 
                    searchType === "contractors" ? "contractor_name" : "homeowner_name";
      const response = await fetch(
        `/api/admin/search/autocomplete?field=${field}&term=${encodeURIComponent(searchQuery)}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
          },
        }
      );

      if (response.ok) {
        const data: AutocompleteResponse = await response.json();
        setAutocompleteResults(data.suggestions);
        setShowAutocomplete(data.suggestions.length > 0);
      }
    } catch (error) {
      console.error("Autocomplete failed:", error);
    }
  };

  const loadHomeownerDetails = async (homeownerId: string) => {
    setIsLoadingDetails(true);
    try {
      const response = await fetch(
        `/api/admin/search/homeowner/${homeownerId}/summary`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
          },
        }
      );

      if (response.ok) {
        const data: HomeownerSummary = await response.json();
        setSelectedHomeowner(data);
      }
    } catch (error) {
      console.error("Failed to load homeowner details:", error);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const formatBudget = (min?: number, max?: number): string => {
    if (!min && !max) return "Not specified";
    if (!min) return `Up to $${max?.toLocaleString()}`;
    if (!max) return `From $${min.toLocaleString()}`;
    return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "generated":
        return "bg-blue-100 text-blue-800";
      case "collecting_bids":
        return "bg-yellow-100 text-yellow-800";
      case "bids_complete":
        return "bg-green-100 text-green-800";
      case "cancelled":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">🔍 Enhanced Search</h3>
        
        {/* Search Type Dropdown */}
        <div className="mb-4">
          <label htmlFor="search-type" className="block text-sm font-medium text-gray-700 mb-2">
            Search In:
          </label>
          <select
            id="search-type"
            value={searchType}
            onChange={(e) => setSearchType(e.target.value as "unified" | "bid_cards" | "homeowners" | "contractors")}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
          >
            <option value="unified">🌐 Search Everything (Unified)</option>
            <option value="homeowners">👤 Homeowners (by name, ID, email, phone)</option>
            <option value="bid_cards">📋 Bid Cards (by homeowner name)</option>
            <option value="contractors">👷 Contractors (by name, company, location)</option>
          </select>
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            placeholder={
              searchType === "unified"
                ? "Search across all bid cards, homeowners, and contractors..."
                : searchType === "bid_cards"
                ? "Search bid cards by homeowner name..."
                : searchType === "homeowners"
                ? "Search homeowners by name, ID, email, or phone..."
                : "Search contractors by name, company, location, or specialty..."
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setShowAutocomplete(autocompleteResults.length > 0)}
            onBlur={() => setTimeout(() => setShowAutocomplete(false), 200)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {isSearching && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <LoadingSpinner size="sm" />
            </div>
          )}

          {/* Autocomplete Dropdown */}
          {showAutocomplete && autocompleteResults.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
              {autocompleteResults.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setSearchQuery(suggestion);
                    setShowAutocomplete(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 first:rounded-t-md last:rounded-b-md"
                >
                  💡 {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Search Results */}
      <div className="p-6">
        {searchResults && (
          <div className="space-y-6">
            {/* Results Summary */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">
                Search Results for "{searchResults.search_query}"
              </h4>
              <div className="flex flex-wrap gap-4 text-sm text-blue-700">
                <span>📋 {searchResults.total_bid_cards} bid cards</span>
                <span>👤 {searchResults.total_homeowners} homeowners</span>
                <span>👷 {searchResults.total_contractors} contractors</span>
              </div>
            </div>

            {/* Bid Cards Results */}
            {searchResults.bid_cards.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">📋 Bid Cards ({searchResults.total_bid_cards})</h4>
                <div className="space-y-3">
                  {searchResults.bid_cards.map((card) => (
                    <div key={card.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-3">
                            <h5 className="font-medium text-gray-900">{card.bid_card_number}</h5>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(card.status)}`}>
                              {card.status.replace("_", " ").toUpperCase()}
                            </span>
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            <span className="font-medium">{card.project_type.replace(/_/g, " ")}</span>
                            {card.homeowner_name && <span> • Homeowner: {card.homeowner_name}</span>}
                            {(card.location_city || card.location_state) && (
                              <span> • 📍 {card.location_city}{card.location_state && `, ${card.location_state}`}</span>
                            )}
                          </div>
                          <div className="mt-1 text-xs text-gray-500">
                            Budget: {formatBudget(card.budget_min, card.budget_max)} • Created: {new Date(card.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        {card.user_id && (
                          <button
                            onClick={() => loadHomeownerDetails(card.user_id!)}
                            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                          >
                            View Homeowner
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Homeowners Results */}
            {searchResults.homeowners.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">👤 Homeowners ({searchResults.total_homeowners})</h4>
                <div className="space-y-3">
                  {searchResults.homeowners.map((homeowner) => (
                    <div key={homeowner.user_id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300">
                      <div className="flex items-center justify-between">
                        <div>
                          <h5 className="font-medium text-gray-900">{homeowner.homeowner_name}</h5>
                          <div className="mt-1 text-sm text-gray-600">
                            📋 {homeowner.bid_card_count} bid cards
                            {homeowner.email && <span> • 📧 {homeowner.email}</span>}
                            {homeowner.phone && <span> • 📞 {homeowner.phone}</span>}
                          </div>
                        </div>
                        <button
                          onClick={() => loadHomeownerDetails(homeowner.user_id)}
                          className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Contractors Results */}
            {searchResults.contractors.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">👷 Contractors ({searchResults.total_contractors})</h4>
                <div className="space-y-3">
                  {searchResults.contractors.map((contractor) => (
                    <div key={contractor.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300">
                      <div className="flex items-center justify-between">
                        <div>
                          <h5 className="font-medium text-gray-900">{contractor.name}</h5>
                          <div className="mt-1 text-sm text-gray-600">
                            {contractor.company && <span>🏢 {contractor.company}</span>}
                            {contractor.location && <span> • 📍 {contractor.location}</span>}
                            {contractor.specialties && <span> • 🔧 {contractor.specialties}</span>}
                          </div>
                          <div className="mt-1 text-xs text-gray-500">
                            {contractor.email && <span>📧 {contractor.email}</span>}
                            {contractor.phone && <span> • 📞 {contractor.phone}</span>}
                            {contractor.tier && <span> • 🎯 Tier {contractor.tier}</span>}
                            {contractor.response_rate && <span> • 📊 {contractor.response_rate}% response rate</span>}
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                            Contractor
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Results */}
            {searchResults.total_bid_cards === 0 && searchResults.total_homeowners === 0 && searchResults.total_contractors === 0 && (
              <div className="text-center py-8">
                <div className="text-gray-400 text-4xl mb-4">🔍</div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h4>
                <p className="text-gray-600">
                  No bid cards, homeowners, or contractors match your search for "{searchResults.search_query}"
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Try adjusting your search terms or using different keywords
                </p>
              </div>
            )}
          </div>
        )}

        {/* Homeowner Details Modal */}
        {selectedHomeowner && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    👤 Homeowner Details: {selectedHomeowner.homeowner_name}
                  </h3>
                  <button
                    onClick={() => setSelectedHomeowner(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {isLoadingDetails ? (
                <div className="p-8 text-center">
                  <LoadingSpinner size="lg" />
                  <p className="mt-4 text-gray-600">Loading homeowner details...</p>
                </div>
              ) : (
                <div className="p-6 space-y-6">
                  {/* Contact Information */}
                  {selectedHomeowner.profile && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">Contact Information</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {selectedHomeowner.profile.email && (
                          <div>
                            <span className="font-medium text-gray-700">Email:</span>
                            <span className="ml-2 text-gray-600">{selectedHomeowner.profile.email}</span>
                          </div>
                        )}
                        {selectedHomeowner.profile.phone && (
                          <div>
                            <span className="font-medium text-gray-700">Phone:</span>
                            <span className="ml-2 text-gray-600">{selectedHomeowner.profile.phone}</span>
                          </div>
                        )}
                        {selectedHomeowner.profile.created_at && (
                          <div>
                            <span className="font-medium text-gray-700">Member Since:</span>
                            <span className="ml-2 text-gray-600">{new Date(selectedHomeowner.profile.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Statistics */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-3">Project Statistics</h4>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-700">{selectedHomeowner.statistics.total_bid_cards}</div>
                        <div className="text-sm text-blue-600">Total Bid Cards</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-700">
                          ${selectedHomeowner.statistics.total_budget_range.min.toLocaleString()} - ${selectedHomeowner.statistics.total_budget_range.max.toLocaleString()}
                        </div>
                        <div className="text-sm text-green-600">Budget Range</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-700">{selectedHomeowner.statistics.project_types.length}</div>
                        <div className="text-sm text-purple-600">Project Types</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-700">
                          {Object.values(selectedHomeowner.statistics.status_breakdown).reduce((a, b) => a + b, 0)}
                        </div>
                        <div className="text-sm text-orange-600">Total Projects</div>
                      </div>
                    </div>
                  </div>

                  {/* Project Types */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Project Types</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedHomeowner.statistics.project_types.map((type, index) => (
                        <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                          {type.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Recent Bid Cards */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Recent Bid Cards</h4>
                    <div className="space-y-2">
                      {selectedHomeowner.recent_bid_cards.map((card, index) => (
                        <div key={index} className="flex items-center justify-between border border-gray-200 rounded p-3">
                          <div>
                            <span className="font-medium text-gray-900">{card.bid_card_number}</span>
                            <span className="ml-3 text-gray-600">{card.project_type.replace(/_/g, " ")}</span>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(card.status)}`}>
                              {card.status.replace("_", " ")}
                            </span>
                            <span className="text-sm text-gray-500">{new Date(card.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Default State */}
        {!searchResults && !isSearching && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🔍</div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">Enhanced Search</h4>
            <p className="text-gray-600">
              Search for bid cards, homeowners, or contractors using the dropdown above
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Find projects, customer details, and contractor information all in one place
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedSearchPanel;