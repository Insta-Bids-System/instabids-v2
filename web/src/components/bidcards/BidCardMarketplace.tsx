import {
  CalendarOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  EnvironmentOutlined,
  FilterOutlined,
  FireOutlined,
  MessageOutlined,
  SearchOutlined,
  SendOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
  StarOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Checkbox,
  Col,
  Divider,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  Pagination,
  Radio,
  Row,
  Select,
  Slider,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import dayjs from "dayjs";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { useBidCard } from "../../contexts/BidCardContext";
import type { BidCardFilters, MarketplaceBidCardView } from "../../types/bidCard";
import { ContractorBidCard } from "./ContractorBidCard";

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Search } = Input;

interface BidCardMarketplaceProps {
  contractorId?: string;
  userType?: string;
}

export const BidCardMarketplace: React.FC<BidCardMarketplaceProps> = ({
  contractorId,
  userType,
}) => {
  const { searchBidCards, isLoading } = useBidCard();
  const [bidCards, setBidCards] = useState<MarketplaceBidCardView[]>([]);
  const [selectedCard, setSelectedCard] = useState<MarketplaceBidCardView | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [filterDrawerVisible, setFilterDrawerVisible] = useState(false);
  const [filters, setFilters] = useState<BidCardFilters>({
    status: ["generated", "active", "ready", "collecting_bids", "discovery", "bids_complete"],
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [total, setTotal] = useState(0);
  const [searchText, setSearchText] = useState("");

  const loadBidCards = useCallback(async () => {
    try {
      // Flatten location filters for API compatibility
      const flatFilters = {
        ...filters,
        // Flatten location object to individual parameters
        ...(filters.location && {
          city: filters.location.city,
          state: filters.location.state,
          zip_code: filters.location.zip_code,
          radius_miles: filters.location.radius_miles,
        }),
        // Remove nested location object
        location: undefined,
        page,
        page_size: pageSize,
      };

      const result = await searchBidCards(flatFilters);
      setBidCards(result.bid_cards);
      setTotal(result.total);
    } catch (error) {
      console.error("Failed to load bid cards:", error);
    }
  }, [searchBidCards, filters, page, pageSize]);

  useEffect(() => {
    loadBidCards();
  }, [loadBidCards]);

  const handleSearch = (value: string) => {
    setSearchText(value);
    // In a real implementation, this would be part of the filters
    loadBidCards();
  };

  const handleFilterChange = (newFilters: Partial<BidCardFilters>) => {
    setFilters({ ...filters, ...newFilters });
    setPage(1);
  };

  const handleCardClick = (card: MarketplaceBidCardView) => {
    setSelectedCard(card);
    setDrawerVisible(true);
  };

  const renderFilters = () => (
    <Form
      layout="vertical"
      initialValues={filters}
      onFinish={(values) => {
        handleFilterChange(values);
        setFilterDrawerVisible(false);
      }}
    >
      <Form.Item label="Project Type" name="project_types">
        <Checkbox.Group>
          <Space direction="vertical">
            <Checkbox value="renovation">Renovation</Checkbox>
            <Checkbox value="repair">Repair</Checkbox>
            <Checkbox value="installation">Installation</Checkbox>
            <Checkbox value="maintenance">Maintenance</Checkbox>
            <Checkbox value="construction">New Construction</Checkbox>
          </Space>
        </Checkbox.Group>
      </Form.Item>

      <Form.Item label="Service Complexity" name="service_complexity">
        <Checkbox.Group>
          <Space direction="vertical">
            <Checkbox value="single-trade">
              <Space>
                <Tag color="blue" size="small">Single Trade</Tag>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  (Lawn care, pools, roofing)
                </Text>
              </Space>
            </Checkbox>
            <Checkbox value="multi-trade">
              <Space>
                <Tag color="orange" size="small">Multi Trade</Tag>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  (Kitchen, bathroom remodels)
                </Text>
              </Space>
            </Checkbox>
            <Checkbox value="complex-coordination">
              <Space>
                <Tag color="red" size="small">Complex</Tag>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  (Whole house renovation)
                </Text>
              </Space>
            </Checkbox>
          </Space>
        </Checkbox.Group>
      </Form.Item>

      <Form.Item label="Categories" name="categories">
        <Select mode="multiple" placeholder="Select categories">
          <Option value="plumbing">Plumbing</Option>
          <Option value="electrical">Electrical</Option>
          <Option value="hvac">HVAC</Option>
          <Option value="roofing">Roofing</Option>
          <Option value="flooring">Flooring</Option>
          <Option value="painting">Painting</Option>
          <Option value="landscaping">Landscaping</Option>
          <Option value="general">General Construction</Option>
        </Select>
      </Form.Item>

      <Form.Item label="Budget Range">
        <Slider
          range
          min={0}
          max={100000}
          step={1000}
          marks={{
            0: "$0",
            25000: "$25k",
            50000: "$50k",
            75000: "$75k",
            100000: "$100k+",
          }}
          onChange={(value) => {
            handleFilterChange({
              budget: { min: value[0], max: value[1] },
            });
          }}
        />
      </Form.Item>

      <Form.Item label="Timeline">
        <Radio.Group
          onChange={(e) => {
            const value = e.target.value;
            const now = dayjs();
            let start_after, start_before;

            switch (value) {
              case "this_week":
                start_before = now.add(7, "days").toISOString();
                break;
              case "this_month":
                start_before = now.add(30, "days").toISOString();
                break;
              case "next_3_months":
                start_before = now.add(90, "days").toISOString();
                break;
            }

            handleFilterChange({ timeline: { start_after, start_before } });
          }}
        >
          <Space direction="vertical">
            <Radio value="this_week">This Week</Radio>
            <Radio value="this_month">This Month</Radio>
            <Radio value="next_3_months">Next 3 Months</Radio>
            <Radio value="custom">Custom Range</Radio>
          </Space>
        </Radio.Group>
      </Form.Item>

      <Form.Item name="group_bid_eligible" valuePropName="checked">
        <Checkbox>Group Bid Eligible Only</Checkbox>
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" block>
          Apply Filters
        </Button>
      </Form.Item>
    </Form>
  );

  const renderBidCard = (card: MarketplaceBidCardView) => (
    <Card
      hoverable
      onClick={() => handleCardClick(card)}
      style={{
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        transition: 'all 0.3s ease'
      }}
      bodyStyle={{ padding: '20px' }}
      cover={
        card.images && card.images.length > 0 ? (
          <img
            alt={card.title}
            src={card.images[0].thumbnail_url || card.images[0].url}
            style={{ height: 200, objectFit: "cover" }}
          />
        ) : (
          <div
            style={{
              height: 200,
              background: "#f0f2f5",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Text type="secondary">No Image</Text>
          </div>
        )
      }
      actions={[
        <Space key="budget">
          <DollarOutlined />
          <Text>{`$${card.budget_range.min.toLocaleString()}-${card.budget_range.max.toLocaleString()}`}</Text>
        </Space>,
        <Space key="location">
          <EnvironmentOutlined />
          <Text>
            {card.location.city}, {card.location.state}
          </Text>
        </Space>,
        <Space key="timeline">
          <CalendarOutlined />
          <Text>{dayjs(card.timeline.start_date).format("MMM D")}</Text>
        </Space>,
      ]}
    >
      <Card.Meta
        title={
          <Space direction="vertical" size={0} style={{ width: "100%" }}>
            <Title level={5} style={{ margin: 0 }} ellipsis>
              {card.title}
            </Title>
            <Space wrap>
              {card.is_urgent && (
                <Tag color="red" icon={<FireOutlined />}>
                  Urgent
                </Tag>
              )}
              {card.is_featured && (
                <Tag color="gold" icon={<StarOutlined />}>
                  Featured
                </Tag>
              )}
              {card.group_bid_eligible && (
                <Tag color="green" icon={<TeamOutlined />}>
                  Group
                </Tag>
              )}
              <Tag>{card.project_type}</Tag>
              {card.service_complexity && (
                <Tag 
                  color={
                    card.service_complexity === "single-trade" ? "blue" : 
                    card.service_complexity === "multi-trade" ? "orange" : "red"
                  }
                >
                  {card.service_complexity === "single-trade" && "Single"}
                  {card.service_complexity === "multi-trade" && "Multi"}
                  {card.service_complexity === "complex-coordination" && "Complex"}
                </Tag>
              )}
              {card.primary_trade && card.primary_trade !== card.project_type && (
                <Tag color="purple" style={{ fontSize: '11px' }}>
                  {card.primary_trade}
                </Tag>
              )}
            </Space>
          </Space>
        }
        description={
          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
            {card.description}
          </Paragraph>
        }
      />

      <Space size="small" wrap style={{ marginTop: 8 }}>
        {card.categories?.slice(0, 3).map((cat, index) => (
          <Tag key={index} color="blue">
            {cat}
          </Tag>
        ))}
        {card.categories && card.categories.length > 3 && (
          <Tag>+{card.categories.length - 3} more</Tag>
        )}
      </Space>

      <Divider style={{ margin: "12px 0" }} />

      <Row justify="space-between" align="middle">
        <Col>
          <Space size="small">
            <TeamOutlined />
            <Text type="secondary">{card.bid_count} bids</Text>
          </Space>
        </Col>
        <Col>
          {card.response_time_hours && (
            <Space size="small">
              <ClockCircleOutlined />
              <Text type="secondary">~{card.response_time_hours}h response</Text>
            </Space>
          )}
        </Col>
      </Row>

      {/* Action Buttons - Mobile Optimized */}
      <Divider style={{ margin: "16px 0" }} />
      <Row gutter={[8, 8]}>
        <Col span={24} sm={12}>
          <Button
            type="default"
            size="large"
            icon={<MessageOutlined />}
            onClick={(e) => {
              e.stopPropagation(); // Prevent card click
              handleCardClick(card); // Open drawer for messaging
            }}
            block
            className="border-blue-500 text-blue-600 hover:bg-blue-50"
            style={{ 
              height: '48px', 
              fontSize: '16px',
              fontWeight: '500'
            }}
          >
            Ask Questions
          </Button>
        </Col>
        <Col span={24} sm={12}>
          <Button
            type="primary"
            size="large"
            icon={<SendOutlined />}
            onClick={(e) => {
              e.stopPropagation(); // Prevent card click
              handleCardClick(card); // Open drawer for bid submission
            }}
            block
            style={{ 
              height: '48px', 
              fontSize: '16px',
              fontWeight: '500'
            }}
          >
            Submit Bid
          </Button>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div style={{ display: "flex", gap: 24, flexDirection: window.innerWidth < 768 ? 'column' : 'row' }}>
      {/* Left Sidebar - Responsive Location Filter */}
      <div
        style={{
          width: window.innerWidth < 768 ? '100%' : 280,
          background: "white",
          padding: window.innerWidth < 768 ? 16 : 20,
          borderRadius: 12,
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          height: "fit-content",
          position: window.innerWidth < 768 ? 'static' : "sticky",
          top: 24,
          marginBottom: window.innerWidth < 768 ? 20 : 0,
        }}
      >
        <Title level={4} style={{ marginBottom: 16 }}>
          <EnvironmentOutlined /> Location Search
        </Title>

        <Form
          layout="vertical"
          initialValues={{
            location: {
              zip_code: filters.location?.zip_code || "",
              radius_miles: filters.location?.radius_miles || 25,
            },
          }}
          onValuesChange={(_, values) => {
            if (values.location?.zip_code?.length === 5) {
              handleFilterChange(values);
            }
          }}
        >
          <Form.Item
            label="Your ZIP Code"
            name={["location", "zip_code"]}
            rules={[{ pattern: /^\d{5}$/, message: "Enter valid 5-digit ZIP" }]}
          >
            <Input
              placeholder="e.g., 90210"
              size="large"
              style={{ fontWeight: "bold" }}
              maxLength={5}
            />
          </Form.Item>

          <Form.Item label="Search Radius" name={["location", "radius_miles"]}>
            <Slider
              min={5}
              max={100}
              marks={{
                5: "5mi",
                25: "25mi",
                50: "50mi",
                100: "100mi",
              }}
              tooltip={{
                formatter: (value) => `${value} miles`,
              }}
            />
          </Form.Item>

          <Button
            type="primary"
            block
            size="large"
            icon={<SearchOutlined />}
            onClick={() => {
              // Trigger search with current form values
              const form = document.querySelector("form");
              if (form) {
                form.dispatchEvent(new Event("submit", { bubbles: true }));
              }
            }}
          >
            Search in Radius
          </Button>
        </Form>

        <Divider />

        <Text type="secondary" style={{ fontSize: 12 }}>
          Find projects within your service area. The search updates automatically when you enter a
          valid ZIP code.
        </Text>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1 }}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} md={12} lg={14}>
            <Search
              placeholder="Search projects by title, description, or location..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ height: '48px' }}
            />
          </Col>
          <Col xs={12} md={6} lg={5}>
            <Button
              size="large"
              icon={<FilterOutlined />}
              onClick={() => setFilterDrawerVisible(true)}
              block
              style={{ height: '48px', fontSize: '16px' }}
            >
              Filters
            </Button>
          </Col>
          <Col xs={12} md={6} lg={5}>
            <Select
              size="large"
              value={`${filters.sort_by}_${filters.sort_order}`}
              onChange={(value) => {
                const [sort_by, sort_order] = value.split("_");
                handleFilterChange({ sort_by: sort_by as any, sort_order: sort_order as any });
              }}
              style={{ width: '100%', height: '48px' }}
            >
              <Option value="created_at_desc">
                <SortDescendingOutlined /> Newest First
              </Option>
              <Option value="created_at_asc">
                <SortAscendingOutlined /> Oldest First
              </Option>
              <Option value="budget_desc">
                <DollarOutlined /> Highest Budget
              </Option>
              <Option value="budget_asc">
                <DollarOutlined /> Lowest Budget
              </Option>
              <Option value="bid_deadline_asc">
                <ClockCircleOutlined /> Deadline Soon
              </Option>
              <Option value="distance_asc">
                <EnvironmentOutlined /> Nearest First
              </Option>
            </Select>
          </Col>
        </Row>

        {isLoading ? (
          <div style={{ textAlign: "center", padding: 100 }}>
            <Spin size="large" />
          </div>
        ) : bidCards.length === 0 ? (
          <Empty
            description="No projects found matching your criteria"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <>
            <Row gutter={[16, 24]}>
              {bidCards.map((card) => (
                <Col key={card.id} xs={24} sm={24} md={12} lg={8} xl={6}>
                  <div style={{ marginBottom: '16px' }}>
                    {renderBidCard(card)}
                  </div>
                </Col>
              ))}
            </Row>

            <Row justify="center" style={{ marginTop: 32 }}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={setPage}
                showSizeChanger={false}
                showTotal={(total) => `Total ${total} projects`}
              />
            </Row>
          </>
        )}

        <Drawer
          title="Project Details"
          placement={window.innerWidth < 768 ? "bottom" : "right"}
          width={window.innerWidth < 768 ? "100%" : 800}
          height={window.innerWidth < 768 ? "90%" : undefined}
          visible={drawerVisible}
          onClose={() => setDrawerVisible(false)}
          bodyStyle={{ 
            padding: window.innerWidth < 768 ? 16 : 0,
            height: window.innerWidth < 768 ? "100%" : undefined,
            overflow: "auto"
          }}
          style={{
            maxWidth: window.innerWidth < 768 ? "100vw" : undefined
          }}
        >
          {selectedCard && (
            <ContractorBidCard
              bidCard={selectedCard as any}
              onBidSubmitted={() => {
                loadBidCards();
                setDrawerVisible(false);
              }}
            />
          )}
        </Drawer>

        <Drawer
          title="More Filters"
          placement="right"
          width={400}
          visible={filterDrawerVisible}
          onClose={() => setFilterDrawerVisible(false)}
        >
          {renderFilters()}
        </Drawer>
      </div>
    </div>
  );
};
