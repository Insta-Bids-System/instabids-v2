"use client";

import { Card, Empty, Spin, Button, Tag, Typography } from "antd";
import { DollarOutlined, EnvironmentOutlined, CalendarOutlined, EyeOutlined, SendOutlined } from "@ant-design/icons";
import type React from "react";
import dayjs from "dayjs";

const { Text, Title } = Typography;

interface BidCard {
  id: string;
  title: string;
  description: string;
  project_type: string;
  location: {
    city: string;
    state: string;
    zip: string;
  };
  budget_range: {
    min: number;
    max: number;
  };
  timeline: {
    start_date?: string;
    end_date?: string;
  };
  distance_miles?: number;
  status: string;
  is_urgent?: boolean;
  is_featured?: boolean;
  images?: Array<{
    url: string;
    thumbnail_url?: string;
  }>;
}

interface BSABidCardsDisplayProps {
  bidCards: BidCard[];
  searchStatus: 'none' | 'searching' | 'found';
  onBidCardSelect: (bidCard: BidCard) => void;
  contractorId?: string;
  searchMetadata?: {
    count: number;
    radius: number;
    contractor_zip: string;
    project_type?: string;
  };
}

export const BSABidCardsDisplay: React.FC<BSABidCardsDisplayProps> = ({
  bidCards,
  searchStatus,
  onBidCardSelect,
  contractorId,
  searchMetadata
}) => {
  if (searchStatus === 'none') {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
        <div className="text-center p-8">
          <div className="text-4xl mb-4">💬</div>
          <div className="text-lg font-medium mb-2">Ask me to find bid cards</div>
          <div className="text-sm text-gray-400">
            Say something like "Show me kitchen projects near me" or "Find bathroom remodel opportunities"
          </div>
        </div>
      </div>
    );
  }

  if (searchStatus === 'searching') {
    return (
      <div className="h-full flex items-center justify-center bg-blue-50 rounded-lg border border-blue-200">
        <div className="text-center p-8">
          <Spin size="large" />
          <div className="mt-4 text-lg font-medium text-blue-600">
            Searching for projects near you...
          </div>
          <div className="text-sm text-blue-400 mt-2">
            Finding the best opportunities in your area
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full p-4 bg-white rounded-lg border">
      {/* Header Section */}
      <div className="mb-4 pb-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <Title level={4} className="!mb-1">
              📋 Available Projects ({bidCards.length})
            </Title>
            {searchMetadata && (
              <Text className="text-gray-600">
                Found within {searchMetadata.radius} miles of {searchMetadata.contractor_zip}
                {searchMetadata.project_type && ` • ${searchMetadata.project_type} projects`}
              </Text>
            )}
          </div>
          {bidCards.length > 0 && (
            <div className="text-right">
              <div className="text-sm text-green-600 font-medium">
                ✅ {bidCards.length} opportunities found
              </div>
              <div className="text-xs text-gray-500">
                Click any project to learn more
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bid Cards Grid */}
      {bidCards.length === 0 ? (
        <Empty
          description="No projects found in your area"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <div className="text-sm text-gray-500 mt-2">
            Try expanding your search radius or different project types
          </div>
        </Empty>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto max-h-96">
          {bidCards.map((card) => (
            <BSABidCardItem
              key={card.id}
              bidCard={card}
              onSelect={() => onBidCardSelect(card)}
              contractorId={contractorId}
            />
          ))}
        </div>
      )}

      {/* Footer with helpful tips */}
      {bidCards.length > 0 && (
        <div className="mt-4 pt-4 border-t bg-gray-50 rounded p-3">
          <div className="text-xs text-gray-600">
            💡 <strong>Pro Tip:</strong> Click "View Details" to see full project requirements, 
            or "Submit Bid" to start preparing your proposal right away.
          </div>
        </div>
      )}
    </div>
  );
};

interface BSABidCardItemProps {
  bidCard: BidCard;
  onSelect: () => void;
  contractorId?: string;
}

export const BSABidCardItem: React.FC<BSABidCardItemProps> = ({
  bidCard,
  onSelect,
  contractorId
}) => {
  return (
    <Card
      hoverable
      className="h-64 cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg"
      cover={
        bidCard.images && bidCard.images.length > 0 ? (
          <img
            alt={bidCard.title}
            src={bidCard.images[0].thumbnail_url || bidCard.images[0].url}
            className="h-24 object-cover"
          />
        ) : (
          <div className="h-24 bg-gradient-to-r from-blue-100 to-purple-100 flex items-center justify-center">
            <div className="text-2xl">🏠</div>
          </div>
        )
      }
      actions={[
        <Button 
          key="view" 
          type="default" 
          size="small"
          icon={<EyeOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="border-blue-500 text-blue-600 hover:bg-blue-50"
        >
          View Details
        </Button>,
        <Button 
          key="bid" 
          type="primary" 
          size="small"
          icon={<SendOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="bg-orange-500 hover:bg-orange-600"
        >
          Submit Bid
        </Button>
      ]}
      onClick={onSelect}
    >
      <Card.Meta
        title={
          <div className="space-y-1">
            <div className="text-sm font-bold truncate" title={bidCard.title}>
              {bidCard.title}
            </div>
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <EnvironmentOutlined />
              {bidCard.location?.city}, {bidCard.location?.state}
              {bidCard.distance_miles && (
                <span className="ml-2 text-blue-600 font-medium">
                  📏 {bidCard.distance_miles.toFixed(1)} miles
                </span>
              )}
            </div>
          </div>
        }
        description={
          <div className="space-y-2">
            {/* Budget */}
            <div className="flex items-center gap-1 text-sm font-medium text-green-600">
              <DollarOutlined />
              ${bidCard.budget_range?.min?.toLocaleString()} - ${bidCard.budget_range?.max?.toLocaleString()}
            </div>
            
            {/* Timeline */}
            {bidCard.timeline?.start_date && (
              <div className="flex items-center gap-1 text-xs text-gray-600">
                <CalendarOutlined />
                Starts {dayjs(bidCard.timeline.start_date).format('MMM D, YYYY')}
              </div>
            )}
            
            {/* Tags */}
            <div className="flex flex-wrap gap-1">
              {bidCard.is_urgent && (
                <Tag color="red" size="small">🔥 Urgent</Tag>
              )}
              {bidCard.is_featured && (
                <Tag color="gold" size="small">⭐ Featured</Tag>
              )}
              <Tag color="blue" size="small">{bidCard.project_type}</Tag>
            </div>
            
            {/* Description preview */}
            {bidCard.description && (
              <div className="text-xs text-gray-500 line-clamp-2">
                {bidCard.description.substring(0, 80)}...
              </div>
            )}
          </div>
        }
      />
    </Card>
  );
};