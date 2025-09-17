import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  DollarOutlined,
  EditOutlined,
  EnvironmentOutlined,
  InfoCircleOutlined,
  MessageOutlined,
  PaperClipOutlined,
  PlusOutlined,
  SendOutlined,
  TeamOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Avatar,
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  message,
  Row,
  Space,
  Steps,
  Switch,
  Tag,
  Tooltip,
  Typography,
  Upload,
} from "antd";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { useBidCard } from "../../contexts/BidCardContext";
import {
  checkExistingConversation,
  sendBidCardMessage,
  startBidCardConversation,
} from "../../services/messaging";
import type {
  BidCardMessage,
  BidMilestone,
  BidSubmissionRequest,
  ContractorBidCardView,
} from "../../types/bidCard";

dayjs.extend(relativeTime);

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Step } = Steps;

interface ContractorBidCardProps {
  bidCard: ContractorBidCardView;
  onBidSubmitted?: () => void;
}

export const ContractorBidCard: React.FC<ContractorBidCardProps> = ({
  bidCard,
  onBidSubmitted,
}) => {
  const { submitBid, updateBid, withdrawBid, sendMessage, getMessages } = useBidCard();
  const [bidModalVisible, setBidModalVisible] = useState(false);
  const [messageModalVisible, setMessageModalVisible] = useState(false);
  const [messages, setMessages] = useState<BidCardMessage[]>([]);
  const [form] = Form.useForm();
  const [milestones, setMilestones] = useState<Omit<BidMilestone, "id">[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasExistingConversation, setHasExistingConversation] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [uploadLoading, setUploadLoading] = useState(false);

  const loadMessages = useCallback(async () => {
    try {
      const contractor_id = "22222222-2222-2222-2222-222222222222"; // TODO: Get from auth/props

      // Check if we have an existing conversation
      const existingConversation = await checkExistingConversation(bidCard.id, contractor_id);

      if (existingConversation) {
        // Load messages from the messaging service
        const { getConversationMessages } = await import("../../services/messaging");
        const msgs = await getConversationMessages(
          existingConversation.id,
          "contractor",
          contractor_id
        );
        setMessages(msgs as any); // TODO: Type alignment
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error("Failed to load messages:", error);
      setMessages([]);
    }
  }, [bidCard.id]);

  const checkForExistingConversation = useCallback(async () => {
    try {
      // Assuming contractor_id is available from props or context
      const contractor_id = "22222222-2222-2222-2222-222222222222"; // TODO: Get from auth/props
      const conversation = await checkExistingConversation(bidCard.id, contractor_id);
      setHasExistingConversation(!!conversation);
    } catch (error) {
      console.error("Error checking for conversation:", error);
    }
  }, [bidCard.id]);

  useEffect(() => {
    if (bidCard.has_bid) {
      loadMessages();
    }
    checkForExistingConversation();
  }, [bidCard.has_bid, checkForExistingConversation, loadMessages]);

  const _calculateDaysUntilStart = () => {
    const start = dayjs(bidCard.timeline.start_date);
    const now = dayjs();
    return start.diff(now, "days");
  };

  const handleSubmitBid = async () => {
    try {
      const values = await form.validateFields();
      setIsSubmitting(true);

      const bidRequest: BidSubmissionRequest = {
        bid_card_id: bidCard.id,
        amount: values.amount,
        timeline: {
          start_date: values.timeline[0].toISOString(),
          end_date: values.timeline[1].toISOString(),
        },
        proposal: values.proposal,
        approach: values.approach,
        materials_included: values.materials_included,
        warranty_details: values.warranty_details,
        milestones: milestones,
        attachments: attachments.map((att) => ({
          name: att.name,
          type: att.type,
          size: att.size,
          url: att.url,
          file: att.file, // Include file for actual upload to backend
        })),
      };

      await submitBid(bidRequest);
      message.success("Bid submitted successfully!");
      setBidModalVisible(false);
      form.resetFields();
      setMilestones([]);
      // Clean up attachment URLs and reset state
      attachments.forEach((att) => {
        if (att.url && att.url.startsWith("blob:")) {
          URL.revokeObjectURL(att.url);
        }
      });
      setAttachments([]);
      onBidSubmitted?.();
    } catch (_error) {
      message.error("Failed to submit bid");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleWithdrawBid = () => {
    Modal.confirm({
      title: "Withdraw Bid",
      content: "Are you sure you want to withdraw your bid? This action cannot be undone.",
      onOk: async () => {
        try {
          await withdrawBid(bidCard.my_bid?.id);
          message.success("Bid withdrawn successfully");
          onBidSubmitted?.();
        } catch (_error) {
          message.error("Failed to withdraw bid");
        }
      },
    });
  };

  const handleSendMessage = async (content: string) => {
    try {
      const contractor_id = "22222222-2222-2222-2222-222222222222"; // TODO: Get from auth/props

      const result = await sendBidCardMessage(bidCard.id, contractor_id, content);

      if (result.success) {
        message.success("Message sent");
        // Show content filtering info if applicable
        if (result.content_filtered) {
          message.info(`Message was filtered for privacy. Contact info was removed.`);
        }
        setMessageModalVisible(false);
        // Reload messages if we have a conversation
        loadMessages();
      } else {
        message.error(result.error || "Failed to send message");
      }
    } catch (error) {
      message.error("Failed to send message");
      console.error("Error sending message:", error);
    }
  };

  const handleStartConversation = async (initialMessage?: string) => {
    try {
      setIsLoadingConversation(true);
      const contractor_id = "22222222-2222-2222-2222-222222222222"; // TODO: Get from auth/props

      const result = await startBidCardConversation(
        bidCard.id,
        contractor_id,
        bidCard.user_id,
        initialMessage ||
          "Hi! I'm interested in your project and have some questions about the requirements."
      );

      if (result.success) {
        message.success("Conversation started! You can now message the homeowner.");
        setHasExistingConversation(true);
        setMessageModalVisible(true);
      } else {
        message.error(result.error || "Failed to start conversation");
      }
    } catch (error) {
      message.error("Failed to start conversation");
      console.error("Error starting conversation:", error);
    } finally {
      setIsLoadingConversation(false);
    }
  };

  const addMilestone = () => {
    const newMilestone = {
      title: "",
      description: "",
      amount: 0,
      estimated_completion: "",
    };
    setMilestones([...milestones, newMilestone]);
  };

  const updateMilestone = (index: number, field: keyof Omit<BidMilestone, "id">, value: any) => {
    const updated = [...milestones];
    updated[index] = { ...updated[index], [field]: value };
    setMilestones(updated);
  };

  const removeMilestone = (index: number) => {
    setMilestones(milestones.filter((_, i) => i !== index));
  };

  // File upload handlers
  const handleFileUpload = async (file: any) => {
    setUploadLoading(true);
    try {
      // For now, simulate file upload - this will be connected to actual storage later
      const fakeUrl = URL.createObjectURL(file);
      const attachment = {
        uid: file.uid,
        name: file.name,
        status: "done",
        url: fakeUrl,
        type: file.type.includes("image")
          ? "image"
          : file.type.includes("pdf")
            ? "pdf"
            : "document",
        size: file.size,
        file: file, // Keep reference for actual upload later
      };

      setAttachments((prev) => [...prev, attachment]);
      message.success(`${file.name} uploaded successfully`);
      setUploadLoading(false);
      return false; // Prevent default upload
    } catch (error) {
      message.error(`Failed to upload ${file.name}`);
      setUploadLoading(false);
      return false;
    }
  };

  const handleRemoveAttachment = (file: any) => {
    setAttachments((prev) => prev.filter((att) => att.uid !== file.uid));
    // Clean up object URL to prevent memory leaks
    if (file.url && file.url.startsWith("blob:")) {
      URL.revokeObjectURL(file.url);
    }
  };

  const renderBidForm = () => (
    <Form form={form} layout="vertical">
      <Form.Item
        name="amount"
        label="Bid Amount"
        rules={[
          { required: true, message: "Please enter your bid amount" },
          {
            type: "number",
            min: 1,
            message: "Please enter a valid bid amount",
          },
        ]}
      >
        <InputNumber
          prefix="$"
          style={{ width: "100%" }}
          placeholder="Enter your bid amount"
        />
      </Form.Item>

      <Form.Item
        name="timeline"
        label="Project Timeline"
        rules={[{ required: true, message: "Please select project timeline" }]}
      >
        <RangePicker
          style={{ width: "100%" }}
          disabledDate={(current) => current && current < dayjs().startOf("day")}
          placeholder={[
            `Earliest: ${dayjs(bidCard.timeline.start_date).format("MMM D, YYYY")}`,
            `Latest: ${dayjs(bidCard.timeline.end_date).format("MMM D, YYYY")}`,
          ]}
        />
      </Form.Item>

      <Form.Item
        name="proposal"
        label="Project Proposal"
        rules={[{ required: true, message: "Please describe your proposal" }]}
      >
        <TextArea
          rows={4}
          placeholder="Describe how you will complete this project, your experience with similar projects, and why you're the best choice..."
        />
      </Form.Item>

      <Form.Item
        name="approach"
        label="Technical Approach"
        rules={[{ required: true, message: "Please describe your approach" }]}
      >
        <TextArea rows={3} placeholder="Explain your technical approach, tools, and methods..." />
      </Form.Item>

      <Form.Item name="materials_included" valuePropName="checked" initialValue={false}>
        <Space>
          <Switch />
          <Text>Materials included in bid price</Text>
        </Space>
      </Form.Item>

      <Form.Item name="warranty_details" label="Warranty Details">
        <TextArea rows={2} placeholder="Describe any warranties or guarantees you offer..." />
      </Form.Item>

      <Divider>Supporting Documents (Optional)</Divider>

      <Form.Item
        label={
          <Space>
            <PaperClipOutlined />
            <span>Attach Documents</span>
          </Space>
        }
        extra="Upload portfolios, licenses, certificates, or project photos (PDF, Images, Documents)"
      >
        <Upload.Dragger
          multiple
          beforeUpload={handleFileUpload}
          onRemove={handleRemoveAttachment}
          fileList={attachments}
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp"
          loading={uploadLoading}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: 48, color: "#1890ff" }} />
          </p>
          <p className="ant-upload-text">Click or drag files to this area to upload</p>
          <p className="ant-upload-hint">
            Support for PDFs, images, and documents. Multiple files are supported.
            <br />
            <strong>Recommended:</strong> Portfolio photos, licenses, project examples
          </p>
        </Upload.Dragger>
      </Form.Item>

      <Divider>Payment Milestones (Optional)</Divider>

      {milestones.map((milestone, index) => (
        <Card key={index} size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={10}>
              <Input
                placeholder="Milestone title"
                value={milestone.title}
                onChange={(e) => updateMilestone(index, "title", e.target.value)}
              />
            </Col>
            <Col span={6}>
              <InputNumber
                prefix="$"
                placeholder="Amount"
                style={{ width: "100%" }}
                value={milestone.amount}
                onChange={(value) => updateMilestone(index, "amount", value)}
              />
            </Col>
            <Col span={6}>
              <DatePicker
                placeholder="Completion"
                style={{ width: "100%" }}
                value={
                  milestone.estimated_completion ? dayjs(milestone.estimated_completion) : undefined
                }
                onChange={(date) =>
                  updateMilestone(index, "estimated_completion", date?.toISOString())
                }
              />
            </Col>
            <Col span={2}>
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeMilestone(index)}
              />
            </Col>
          </Row>
          <Input.TextArea
            placeholder="Milestone description"
            rows={2}
            style={{ marginTop: 8 }}
            value={milestone.description}
            onChange={(e) => updateMilestone(index, "description", e.target.value)}
          />
        </Card>
      ))}

      <Button type="dashed" onClick={addMilestone} icon={<PlusOutlined />} block>
        Add Payment Milestone
      </Button>
    </Form>
  );

  const renderMyBid = () => {
    if (!bidCard.my_bid) return null;

    return (
      <Card
        title="Your Bid"
        extra={
          <Space>
            {bidCard.my_bid.status === "submitted" && (
              <>
                <Button icon={<EditOutlined />} disabled>
                  Edit
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleWithdrawBid}>
                  Withdraw
                </Button>
              </>
            )}
            {bidCard.my_bid.status === "accepted" && (
              <Tag color="success" icon={<CheckCircleOutlined />}>
                Accepted
              </Tag>
            )}
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: "100%" }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8}>
              <Text type="secondary">Bid Amount</Text>
              <Title level={4}>${bidCard.my_bid.amount.toLocaleString()}</Title>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Text type="secondary">Timeline</Text>
              <Text strong display="block">
                {dayjs(bidCard.my_bid.timeline.start_date).format("MMM D")} -
                {dayjs(bidCard.my_bid.timeline.end_date).format("MMM D, YYYY")}
              </Text>
            </Col>
            <Col xs={24} sm={24} md={8}>
              <Text type="secondary">Status</Text>
              <Tag
                color={
                  bidCard.my_bid.status === "accepted"
                    ? "success"
                    : bidCard.my_bid.status === "rejected"
                      ? "error"
                      : bidCard.my_bid.status === "submitted"
                        ? "processing"
                        : "default"
                }
              >
                {bidCard.my_bid.status.toUpperCase()}
              </Tag>
            </Col>
          </Row>

          <Divider />

          <div>
            <Text type="secondary">Proposal</Text>
            <Paragraph>{bidCard.my_bid.proposal}</Paragraph>
          </div>

          {bidCard.my_bid.allows_messages && (
            <Button icon={<MessageOutlined />} onClick={() => setMessageModalVisible(true)}>
              Message Homeowner
            </Button>
          )}
        </Space>
      </Card>
    );
  };

  return (
    <>
      <Card
        title={
          <Space direction="vertical" size={0}>
            <Title level={4} style={{ margin: 0 }}>
              {bidCard.title}
            </Title>
            <Space>
              {bidCard.is_urgent && <Tag color="red">Urgent</Tag>}
              {bidCard.is_featured && <Tag color="gold">Featured</Tag>}
              {bidCard.group_bid_eligible && (
                <Tag color="green" icon={<TeamOutlined />}>
                  Group Eligible
                </Tag>
              )}
              <Tag>{bidCard.project_type}</Tag>
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
                </Tag>
              )}
              {bidCard.primary_trade && (
                <Tag color="purple">
                  {bidCard.primary_trade}
                </Tag>
              )}
            </Space>
          </Space>
        }
        extra={
          <Space>
            {bidCard.distance_miles && (
              <Text type="secondary">
                <EnvironmentOutlined /> {bidCard.distance_miles.toFixed(1)} miles
              </Text>
            )}
            {bidCard.match_score && (
              <Tooltip title="Match score based on your profile and project requirements">
                <Tag color="blue">{Math.round(bidCard.match_score * 100)}% Match</Tag>
              </Tooltip>
            )}
          </Space>
        }
      >
        {bidCard.status === "active" && !bidCard.has_bid && (
          <Alert
            message={`Project starts ${dayjs(bidCard.timeline.start_date).fromNow()}`}
            type="info"
            showIcon
            icon={<ClockCircleOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Paragraph>{bidCard.description}</Paragraph>

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" bordered={false}>
              <Space direction="vertical" align="center" style={{ width: "100%" }}>
                <DollarOutlined style={{ fontSize: 24, color: "#52c41a" }} />
                <Text type="secondary">Budget</Text>
                <Text strong>
                  ${bidCard.budget_range.min.toLocaleString()} - $
                  {bidCard.budget_range.max.toLocaleString()}
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" bordered={false}>
              <Space direction="vertical" align="center" style={{ width: "100%" }}>
                <CalendarOutlined style={{ fontSize: 24, color: "#1890ff" }} />
                <Text type="secondary">Timeline</Text>
                <Text strong>
                  {dayjs(bidCard.timeline.start_date).format("MMM D")} -{" "}
                  {dayjs(bidCard.timeline.end_date).format("MMM D")}
                </Text>
                <Tag>{bidCard.timeline.flexibility}</Tag>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" bordered={false}>
              <Space direction="vertical" align="center" style={{ width: "100%" }}>
                <EnvironmentOutlined style={{ fontSize: 24, color: "#fa8c16" }} />
                <Text type="secondary">Location</Text>
                <Text strong>
                  {bidCard.location.city}, {bidCard.location.state}
                </Text>
                <Text type="secondary">{bidCard.location.zip_code}</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" bordered={false}>
              <Space direction="vertical" align="center" style={{ width: "100%" }}>
                <TeamOutlined style={{ fontSize: 24, color: "#722ed1" }} />
                <Text type="secondary">Service Complexity</Text>
                <Text strong>
                  {bidCard.service_complexity === "single-trade" && "Single Trade"}
                  {bidCard.service_complexity === "multi-trade" && "Multi Trade"}
                  {bidCard.service_complexity === "complex-coordination" && "Complex"}
                  {!bidCard.service_complexity && "Not specified"}
                </Text>
                {bidCard.trade_count && (
                  <Tag color="purple">{bidCard.trade_count} trade{bidCard.trade_count !== 1 ? 's' : ''}</Tag>
                )}
                {bidCard.secondary_trades && bidCard.secondary_trades.length > 0 && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    +{bidCard.secondary_trades.length} secondary trade{bidCard.secondary_trades.length !== 1 ? 's' : ''}
                  </Text>
                )}
              </Space>
            </Card>
          </Col>
        </Row>

        <Divider />

        <Space direction="vertical" style={{ width: "100%" }}>
          <Text strong>Requirements:</Text>
          <Space wrap>
            {bidCard.requirements && bidCard.requirements.length > 0 ? (
              bidCard.requirements.map((req, index) => (
                <Tag key={index}>{req}</Tag>
              ))
            ) : (
              <Text type="secondary">No specific requirements listed</Text>
            )}
          </Space>

          <Text strong>Categories:</Text>
          <Space wrap>
            {bidCard.categories && bidCard.categories.length > 0 ? (
              bidCard.categories.map((cat, index) => (
                <Tag key={index} color="blue">
                  {cat}
                </Tag>
              ))
            ) : (
              <Text type="secondary">No categories specified</Text>
            )}
          </Space>
        </Space>

        <Divider />

        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space wrap>
              <TeamOutlined />
              <Text>{bidCard.bid_count} bids submitted</Text>
              {bidCard.bid_deadline && (
                <>
                  <Divider type="vertical" />
                  <Text type="secondary">
                    Deadline: {dayjs(bidCard.bid_deadline).format("MMM D, YYYY")}
                  </Text>
                </>
              )}
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Row gutter={[8, 8]} justify={window.innerWidth < 768 ? "center" : "end"}>
              <Col xs={24} sm={12} md={12}>
                {/* Messaging Button */}
                {hasExistingConversation ? (
                  <Button
                    icon={<MessageOutlined />}
                    onClick={() => setMessageModalVisible(true)}
                    className="border-blue-500 text-blue-600 hover:bg-blue-50"
                    block={window.innerWidth < 768}
                    style={{ 
                      height: window.innerWidth < 768 ? '48px' : 'auto',
                      fontSize: window.innerWidth < 768 ? '16px' : '14px'
                    }}
                  >
                    Continue Chat
                  </Button>
                ) : (
                  <Button
                    icon={<MessageOutlined />}
                    loading={isLoadingConversation}
                    onClick={() => setMessageModalVisible(true)}
                    className="border-blue-500 text-blue-600 hover:bg-blue-50"
                    block={window.innerWidth < 768}
                    style={{ 
                      height: window.innerWidth < 768 ? '48px' : 'auto',
                      fontSize: window.innerWidth < 768 ? '16px' : '14px'
                    }}
                  >
                    Ask Questions
                  </Button>
                )}
              </Col>
              <Col xs={24} sm={12} md={12}>
                {/* Bid Submission Button */}
                {!bidCard.has_bid && bidCard.can_bid ? (
                  <Button
                    type="primary"
                    size="large"
                    icon={<SendOutlined />}
                    onClick={() => setBidModalVisible(true)}
                    block={window.innerWidth < 768}
                    style={{ 
                      height: window.innerWidth < 768 ? '48px' : 'auto',
                      fontSize: window.innerWidth < 768 ? '16px' : '14px'
                    }}
                  >
                    Submit Bid
                  </Button>
                ) : bidCard.has_bid ? (
                  <Tag color="success" icon={<CheckCircleOutlined />} style={{ width: '100%', textAlign: 'center', padding: '8px' }}>
                    Bid Submitted
                  </Tag>
                ) : (
                  <Tooltip title="You cannot bid on this project">
                    <Button 
                      disabled 
                      block={window.innerWidth < 768}
                      style={{ 
                        height: window.innerWidth < 768 ? '48px' : 'auto',
                        fontSize: window.innerWidth < 768 ? '16px' : '14px'
                      }}
                    >
                      Cannot Bid
                    </Button>
                  </Tooltip>
                )}
              </Col>
            </Row>
          </Col>
        </Row>

        {bidCard.has_bid && bidCard.my_bid && (
          <>
            <Divider />
            {renderMyBid()}
          </>
        )}
      </Card>

      <Modal
        title="Submit Your Bid"
        visible={bidModalVisible}
        onCancel={() => setBidModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setBidModalVisible(false)}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={isSubmitting}
            onClick={handleSubmitBid}
            icon={<SendOutlined />}
          >
            Submit Bid
          </Button>,
        ]}
      >
        {renderBidForm()}
      </Modal>

      <Modal
        title={
          <Space>
            <MessageOutlined />
            <span>Message Homeowner About: {bidCard.title}</span>
          </Space>
        }
        visible={messageModalVisible}
        onCancel={() => setMessageModalVisible(false)}
        width={600}
        footer={null}
      >
        {/* Project Context Header */}
        <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 6 }}>
          <Text strong>Project: </Text>
          <Text>{bidCard.title}</Text>
          <br />
          <Text strong>Budget: </Text>
          <Text>
            ${bidCard.budget_range.min.toLocaleString()} - $
            {bidCard.budget_range.max.toLocaleString()}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            <InfoCircleOutlined /> Messages are filtered for privacy. Phone numbers and emails will
            be removed.
          </Text>
        </div>

        <List
          dataSource={messages}
          renderItem={(msg: any) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar icon={msg.sender_type === "homeowner" ? null : <TeamOutlined />} />}
                title={
                  <Space>
                    <Text>{msg.sender_type === "homeowner" ? "Homeowner" : "You"}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(msg.created_at).fromNow()}
                    </Text>
                    {msg.content_filtered && (
                      <Tag size="small" color="orange">
                        Filtered
                      </Tag>
                    )}
                  </Space>
                }
                description={
                  <div>
                    <div>{msg.filtered_content || msg.content}</div>
                    {msg.content_filtered &&
                      msg.filter_reasons &&
                      msg.filter_reasons.length > 0 && (
                        <div style={{ marginTop: 4, fontSize: 12, color: "#fa8c16" }}>
                          <InfoCircleOutlined /> Contact info removed for privacy
                        </div>
                      )}
                  </div>
                }
              />
            </List.Item>
          )}
          style={{ maxHeight: 300, overflow: "auto", marginBottom: 16 }}
        />

        <Form onFinish={(values) => handleSendMessage(values.message)}>
          <Form.Item name="message" rules={[{ required: true, message: "Please enter a message" }]}>
            <TextArea rows={3} placeholder="Type your message..." />
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
