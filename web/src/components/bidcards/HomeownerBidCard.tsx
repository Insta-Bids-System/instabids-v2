import {
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DollarOutlined,
  EditOutlined,
  EnvironmentOutlined,
  MessageOutlined,
  PictureOutlined,
  SaveOutlined,
  SendOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Badge,
  Button,
  Card,
  DatePicker,
  Divider,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  message,
  Select,
  Space,
  Switch,
  Tabs,
  Tag,
  Typography,
  Upload,
} from "antd";
import dayjs from "dayjs";
import type React from "react";
import { useEffect, useState } from "react";
import { useBidCard } from "../../contexts/BidCardContext";
import type { BidCardMessage, ContractorBid, HomeownerBidCardView } from "../../types/bidCard";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

interface HomeownerBidCardProps {
  bidCard: HomeownerBidCardView;
  onUpdate?: (updatedCard: HomeownerBidCardView) => void;
}

export const HomeownerBidCard: React.FC<HomeownerBidCardProps> = ({ bidCard, onUpdate }) => {
  const { updateBidCard, publishBidCard, getMessages, sendMessage, getUnreadCount } = useBidCard();
  const [isEditing, setIsEditing] = useState(false);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState("details");
  const [messages, setMessages] = useState<BidCardMessage[]>([]);
  const [bids, _setBids] = useState<ContractorBid[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [messageModalVisible, setMessageModalVisible] = useState(false);
  const [selectedContractor, setSelectedContractor] = useState<string | null>(null);

  useEffect(() => {
    loadMessages();
    loadUnreadCount();
  }, [loadMessages, loadUnreadCount]);

  const loadMessages = async () => {
    try {
      const msgs = await getMessages(bidCard.id);
      setMessages(msgs);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const count = await getUnreadCount(bidCard.id);
      setUnreadCount(count);
    } catch (error) {
      console.error("Failed to load unread count:", error);
    }
  };

  const handleEdit = () => {
    form.setFieldsValue({
      title: bidCard.title,
      description: bidCard.description,
      budget: [bidCard.budget_range.min, bidCard.budget_range.max],
      timeline: [dayjs(bidCard.timeline.start_date), dayjs(bidCard.timeline.end_date)],
      timeline_flexibility: bidCard.timeline.flexibility,
      project_type: bidCard.project_type,
      categories: bidCard.categories,
      requirements: bidCard.requirements,
      service_complexity: bidCard.service_complexity || "single-trade",
      trade_count: bidCard.trade_count || 1,
      primary_trade: bidCard.primary_trade || "",
      secondary_trades: bidCard.secondary_trades || [],
      location: {
        address: bidCard.location.address,
        city: bidCard.location.city,
        state: bidCard.location.state,
        zip_code: bidCard.location.zip_code,
      },
      group_bid_eligible: bidCard.group_bid_eligible,
      allows_questions: bidCard.allows_questions,
      requires_bid_before_message: bidCard.requires_bid_before_message,
    });
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const updates = {
        title: values.title,
        description: values.description,
        budget_range: {
          min: values.budget[0],
          max: values.budget[1],
        },
        timeline: {
          start_date: values.timeline[0].toISOString(),
          end_date: values.timeline[1].toISOString(),
          flexibility: values.timeline_flexibility,
        },
        project_type: values.project_type,
        categories: values.categories,
        requirements: values.requirements,
        service_complexity: values.service_complexity,
        trade_count: values.trade_count,
        primary_trade: values.primary_trade,
        secondary_trades: values.secondary_trades,
        location: values.location,
        group_bid_eligible: values.group_bid_eligible,
        allows_questions: values.allows_questions,
        requires_bid_before_message: values.requires_bid_before_message,
      };

      const updatedCard = await updateBidCard(bidCard.id, updates);
      message.success("Bid card updated successfully");
      setIsEditing(false);
      onUpdate?.(updatedCard as HomeownerBidCardView);
    } catch (_error) {
      message.error("Failed to update bid card");
    }
  };

  const handlePublish = async () => {
    Modal.confirm({
      title: "Publish Bid Card",
      content:
        "Are you sure you want to publish this bid card? It will become visible to contractors.",
      onOk: async () => {
        try {
          await publishBidCard(bidCard.id);
          message.success("Bid card published successfully");
        } catch (_error) {
          message.error("Failed to publish bid card");
        }
      },
    });
  };

  const handleSendMessage = async (content: string, recipientId: string) => {
    try {
      await sendMessage({
        bid_card_id: bidCard.id,
        recipient_id: recipientId,
        content,
      });
      message.success("Message sent");
      loadMessages();
      setMessageModalVisible(false);
    } catch (_error) {
      message.error("Failed to send message");
    }
  };

  const renderDetailsTab = () => (
    <Form form={form} layout="vertical" disabled={!isEditing}>
      <Form.Item name="title" label="Project Title" rules={[{ required: true }]}>
        <Input placeholder="e.g., Kitchen Renovation" />
      </Form.Item>

      <Form.Item name="description" label="Description" rules={[{ required: true }]}>
        <TextArea rows={4} placeholder="Describe your project in detail..." />
      </Form.Item>

      <Form.Item name="budget" label="Budget Range" rules={[{ required: true }]}>
        <Space>
          <InputNumber
            prefix="$"
            min={0}
            placeholder="Min"
            style={{ width: 120 }}
            value={form.getFieldValue(["budget", 0])}
            onChange={(value) => {
              const budget = form.getFieldValue("budget") || [];
              form.setFieldsValue({ budget: [value, budget[1]] });
            }}
          />
          <span>to</span>
          <InputNumber
            prefix="$"
            min={0}
            placeholder="Max"
            style={{ width: 120 }}
            value={form.getFieldValue(["budget", 1])}
            onChange={(value) => {
              const budget = form.getFieldValue("budget") || [];
              form.setFieldsValue({ budget: [budget[0], value] });
            }}
          />
        </Space>
      </Form.Item>

      <Form.Item name="timeline" label="Timeline" rules={[{ required: true }]}>
        <RangePicker style={{ width: "100%" }} />
      </Form.Item>

      <Form.Item name="timeline_flexibility" label="Timeline Flexibility">
        <Select>
          <Option value="flexible">Flexible</Option>
          <Option value="strict">Strict</Option>
          <Option value="asap">ASAP</Option>
        </Select>
      </Form.Item>

      <Form.Item name="project_type" label="Project Type" rules={[{ required: true }]}>
        <Select placeholder="Select project type">
          <Option value="renovation">Renovation</Option>
          <Option value="repair">Repair</Option>
          <Option value="installation">Installation</Option>
          <Option value="maintenance">Maintenance</Option>
          <Option value="construction">New Construction</Option>
        </Select>
      </Form.Item>

      <Form.Item name="categories" label="Categories">
        <Select mode="tags" placeholder="Add categories">
          <Option value="plumbing">Plumbing</Option>
          <Option value="electrical">Electrical</Option>
          <Option value="hvac">HVAC</Option>
          <Option value="roofing">Roofing</Option>
          <Option value="flooring">Flooring</Option>
          <Option value="painting">Painting</Option>
        </Select>
      </Form.Item>

      <Divider>Service Complexity</Divider>

      <Form.Item name="service_complexity" label="Service Complexity">
        <Select placeholder="Select service complexity">
          <Option value="single-trade">Single Trade (e.g., lawn care, pool cleaning, roofing)</Option>
          <Option value="multi-trade">Multi Trade (e.g., kitchen remodel, bathroom renovation)</Option>
          <Option value="complex-coordination">Complex Coordination (e.g., whole house renovation)</Option>
        </Select>
      </Form.Item>

      <Form.Item name="trade_count" label="Number of Trades Involved">
        <InputNumber min={1} max={20} placeholder="e.g., 1 for lawn care, 3-5 for kitchen remodel" />
      </Form.Item>

      <Form.Item name="primary_trade" label="Primary Trade">
        <Select placeholder="Select primary trade">
          <Option value="landscaping">Landscaping</Option>
          <Option value="pools">Pools</Option>
          <Option value="turf">Turf Installation</Option>
          <Option value="roofing">Roofing</Option>
          <Option value="kitchen">Kitchen Renovation</Option>
          <Option value="bathroom">Bathroom Renovation</Option>
          <Option value="plumbing">Plumbing</Option>
          <Option value="electrical">Electrical</Option>
          <Option value="hvac">HVAC</Option>
          <Option value="flooring">Flooring</Option>
          <Option value="painting">Painting</Option>
          <Option value="general">General Construction</Option>
        </Select>
      </Form.Item>

      <Form.Item name="secondary_trades" label="Secondary Trades">
        <Select mode="tags" placeholder="Select secondary trades (if applicable)">
          <Option value="landscaping">Landscaping</Option>
          <Option value="pools">Pools</Option>
          <Option value="turf">Turf Installation</Option>
          <Option value="roofing">Roofing</Option>
          <Option value="plumbing">Plumbing</Option>
          <Option value="electrical">Electrical</Option>
          <Option value="hvac">HVAC</Option>
          <Option value="flooring">Flooring</Option>
          <Option value="painting">Painting</Option>
          <Option value="general">General Construction</Option>
        </Select>
      </Form.Item>

      <Divider>Location</Divider>

      <Form.Item name={["location", "address"]} label="Address">
        <Input placeholder="Street address (optional)" />
      </Form.Item>

      <Space style={{ width: "100%" }} size="large">
        <Form.Item name={["location", "city"]} label="City" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name={["location", "state"]} label="State" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name={["location", "zip_code"]} label="ZIP Code" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
      </Space>

      <Divider>Options</Divider>

      <Form.Item name="group_bid_eligible" valuePropName="checked">
        <Space>
          <Switch />
          <Text>Eligible for group bidding (15-25% savings)</Text>
        </Space>
      </Form.Item>

      <Form.Item name="allows_questions" valuePropName="checked">
        <Space>
          <Switch />
          <Text>Allow contractors to ask questions</Text>
        </Space>
      </Form.Item>

      <Form.Item name="requires_bid_before_message" valuePropName="checked">
        <Space>
          <Switch />
          <Text>Require bid submission before messaging</Text>
        </Space>
      </Form.Item>
    </Form>
  );

  const renderBidsTab = () => (
    <List
      dataSource={bids}
      renderItem={(bid) => (
        <List.Item
          actions={[
            <Button
              icon={<MessageOutlined />}
              onClick={() => {
                setSelectedContractor(bid.contractor_id);
                setMessageModalVisible(true);
              }}
            >
              Message
            </Button>,
            bid.status === "submitted" && (
              <Space>
                <Button type="primary" icon={<CheckCircleOutlined />}>
                  Accept
                </Button>
                <Button danger icon={<CloseCircleOutlined />}>
                  Reject
                </Button>
              </Space>
            ),
          ]}
        >
          <List.Item.Meta
            avatar={<Avatar icon={<TeamOutlined />} />}
            title={`Contractor ${bid.contractor_id.slice(0, 8)}`}
            description={
              <Space direction="vertical">
                <Text strong>${bid.amount.toLocaleString()}</Text>
                <Text type="secondary">
                  {dayjs(bid.timeline.start_date).format("MMM D")} -{" "}
                  {dayjs(bid.timeline.end_date).format("MMM D, YYYY")}
                </Text>
                <Paragraph ellipsis={{ rows: 2 }}>{bid.proposal}</Paragraph>
                <Tag color={bid.status === "submitted" ? "blue" : "default"}>{bid.status}</Tag>
              </Space>
            }
          />
        </List.Item>
      )}
      locale={{ emptyText: "No bids received yet" }}
    />
  );

  const renderMessagesTab = () => (
    <List
      dataSource={messages}
      renderItem={(msg) => (
        <List.Item>
          <List.Item.Meta
            avatar={<Avatar icon={msg.sender_type === "contractor" ? <TeamOutlined /> : null} />}
            title={
              <Space>
                <Text>
                  {msg.sender_type === "contractor"
                    ? `Contractor ${msg.sender_id.slice(0, 8)}`
                    : "You"}
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {dayjs(msg.created_at).format("MMM D, h:mm A")}
                </Text>
              </Space>
            }
            description={msg.content}
          />
        </List.Item>
      )}
      locale={{ emptyText: "No messages yet" }}
    />
  );

  return (
    <>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              {bidCard.title || "Untitled Project"}
            </Title>
            {bidCard.status === "draft" && <Tag>Draft</Tag>}
            {bidCard.status === "active" && <Tag color="green">Active</Tag>}
            {bidCard.status === "collecting_bids" && <Tag color="blue">Collecting Bids</Tag>}
          </Space>
        }
        extra={
          <Space>
            {!isEditing ? (
              <>
                {bidCard.can_edit && (
                  <Button icon={<EditOutlined />} onClick={handleEdit}>
                    Edit
                  </Button>
                )}
                {bidCard.can_publish && bidCard.status === "draft" && (
                  <Button type="primary" icon={<SendOutlined />} onClick={handlePublish}>
                    Publish
                  </Button>
                )}
              </>
            ) : (
              <>
                <Button onClick={() => setIsEditing(false)}>Cancel</Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  Save
                </Button>
              </>
            )}
          </Space>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarExtraContent={
            <Space>
              <Badge count={bidCard.bid_count} showZero>
                <TeamOutlined /> Bids
              </Badge>
              <Badge count={unreadCount}>
                <MessageOutlined /> Messages
              </Badge>
            </Space>
          }
        >
          <TabPane tab="Details" key="details">
            {renderDetailsTab()}
          </TabPane>
          <TabPane tab={`Bids (${bidCard.bid_count})`} key="bids">
            {renderBidsTab()}
          </TabPane>
          <TabPane tab="Messages" key="messages">
            {renderMessagesTab()}
          </TabPane>
          <TabPane tab="Media" key="media">
            <Upload.Dragger multiple listType="picture-card" disabled={!isEditing}>
              <p className="ant-upload-drag-icon">
                <PictureOutlined />
              </p>
              <p className="ant-upload-text">Click or drag files to upload</p>
            </Upload.Dragger>
          </TabPane>
        </Tabs>

        <Divider />

        <Space size="large" wrap>
          <Space>
            <DollarOutlined />
            <Text>
              ${bidCard.budget_range.min.toLocaleString()} - $
              {bidCard.budget_range.max.toLocaleString()}
            </Text>
          </Space>
          <Space>
            <CalendarOutlined />
            <Text>
              {dayjs(bidCard.timeline.start_date).format("MMM D")} -{" "}
              {dayjs(bidCard.timeline.end_date).format("MMM D, YYYY")}
            </Text>
          </Space>
          <Space>
            <EnvironmentOutlined />
            <Text>
              {bidCard.location.city}, {bidCard.location.state} {bidCard.location.zip_code}
            </Text>
          </Space>
          {bidCard.service_complexity && (
            <Tag 
              color={
                bidCard.service_complexity === "single-trade" ? "blue" : 
                bidCard.service_complexity === "multi-trade" ? "orange" : "red"
              }
            >
              {bidCard.service_complexity === "single-trade" && "Single Trade"}
              {bidCard.service_complexity === "multi-trade" && "Multi Trade"}
              {bidCard.service_complexity === "complex-coordination" && "Complex"}
              {bidCard.trade_count && ` (${bidCard.trade_count} trades)`}
            </Tag>
          )}
          {bidCard.primary_trade && (
            <Tag color="purple">
              Primary: {bidCard.primary_trade}
            </Tag>
          )}
          {bidCard.secondary_trades && bidCard.secondary_trades.length > 0 && (
            <Tag color="cyan">
              +{bidCard.secondary_trades.length} more trades
            </Tag>
          )}
          {bidCard.group_bid_eligible && (
            <Tag color="green" icon={<TeamOutlined />}>
              Group Bid Eligible
            </Tag>
          )}
        </Space>
      </Card>

      <Modal
        title={`Send Message to Contractor`}
        visible={messageModalVisible}
        onCancel={() => setMessageModalVisible(false)}
        footer={null}
      >
        <Form onFinish={(values) => handleSendMessage(values.message, selectedContractor!)}>
          <Form.Item name="message" rules={[{ required: true, message: "Please enter a message" }]}>
            <TextArea rows={4} placeholder="Type your message..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SendOutlined />}>
              Send Message
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
