import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Tag, 
  Modal, 
  Input, 
  Select, 
  Card, 
  Statistic, 
  Row, 
  Col, 
  Space, 
  Typography, 
  Alert, 
  Drawer,
  Descriptions,
  List,
  Avatar,
  Badge,
  Tooltip,
  message,
  Popconfirm,
  DatePicker,
  Switch,
  Image
} from 'antd';
// import { Document, Page, pdfjs } from 'react-pdf';
// import '../../styles/react-pdf.css';
import { 
  EyeOutlined, 
  DownloadOutlined, 
  CheckOutlined, 
  CloseOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  PhoneOutlined,
  MailOutlined,
  DollarOutlined,
  CalendarOutlined,
  UserOutlined,
  ProjectOutlined,
  FilterOutlined,
  ReloadOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  CloseCircleOutlined,
  ZoomInOutlined,
  ZoomOutOutlined
} from '@ant-design/icons';

// Configure PDF.js worker
// pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface ContactAnalysis {
  contact_info_detected: boolean;
  confidence: number;
  explanation: string;
  phones: string[];
  emails: string[];
  addresses: string[];
  social_handles: string[];
}

interface SubmittedProposal {
  id: string;
  bid_card_id: string;
  contractor_id: string;
  amount: number;
  timeline_start: string;
  timeline_end: string;
  proposal: string;
  approach: string;
  warranty_details?: string;
  bid_status: string;
  submitted_at: string;
  bid_card_number: string;
  project_type: string;
  urgency_level: string;
  contractor_name: string;
  contact_name?: string;
  attachment_count: number;
  contact_analysis: ContactAnalysis;
  review_status: 'pending' | 'flagged' | 'approved' | 'rejected';
  flagged_reason: string;
  requires_review: boolean;
}

interface ProposalStats {
  total: number;
  pending: number;
  flagged: number;
  approved: number;
  rejected: number;
  total_attachments: number;
  with_attachments: number;
}

interface ProposalAttachment {
  id: string;
  contractor_bid_id: string;
  type: string;
  url: string;
  name: string;
  size: number;
  mime_type: string;
  description?: string;
  created_at: string;
}

const SubmittedProposalsTab: React.FC = () => {
  const [proposals, setProposals] = useState<SubmittedProposal[]>([]);
  const [stats, setStats] = useState<ProposalStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<SubmittedProposal | null>(null);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [attachments, setAttachments] = useState<ProposalAttachment[]>([]);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<'approved' | 'rejected' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewReason, setReviewReason] = useState('');

  // File viewing state
  const [fileViewerVisible, setFileViewerVisible] = useState(false);
  const [currentFile, setCurrentFile] = useState<ProposalAttachment | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);

  // Filters
  const [filters, setFilters] = useState({
    status: 'all',
    has_attachments: null as boolean | null,
    has_contact_info: null as boolean | null,
    project_type: '',
    date_range: null as [string, string] | null
  });

  const loadProposals = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status !== 'all') params.append('status', filters.status);
      if (filters.has_attachments !== null) params.append('has_attachments', filters.has_attachments.toString());
      if (filters.has_contact_info !== null) params.append('has_contact_info', filters.has_contact_info.toString());
      if (filters.project_type) params.append('project_type', filters.project_type);

      const response = await fetch(`/api/proposal-review/queue?${params}`);
      const data = await response.json();
      setProposals(data);
    } catch (error) {
      console.error('Error loading proposals:', error);
      message.error('Failed to load submitted proposals');
    }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/proposal-review/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  useEffect(() => {
    loadProposals();
    loadStats();
  }, [filters]);

  const getProposalStatusColor = (status: string) => {
    switch (status) {
      case 'flagged': return 'red';
      case 'approved': return 'green';
      case 'rejected': return 'red';
      case 'pending': return 'blue';
      default: return 'default';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'emergency': return 'red';
      case 'urgent': return 'orange';
      case 'standard': return 'blue';
      case 'flexible': return 'green';
      default: return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const handleViewDetails = async (proposal: SubmittedProposal) => {
    setSelectedProposal(proposal);
    
    // Load attachments
    try {
      const response = await fetch(`/api/proposal-review/${proposal.id}/attachments`);
      const attachmentData = await response.json();
      setAttachments(attachmentData);
    } catch (error) {
      console.error('Error loading attachments:', error);
      setAttachments([]);
    }
    
    setDetailsVisible(true);
  };

  const handleReviewProposal = (proposal: SubmittedProposal, decision: 'approved' | 'rejected') => {
    setSelectedProposal(proposal);
    setReviewDecision(decision);
    setReviewNotes('');
    setReviewReason('');
    setReviewModalVisible(true);
  };

  const submitReview = async () => {
    if (!selectedProposal || !reviewDecision) return;

    try {
      const response = await fetch(`/api/proposal-review/${selectedProposal.id}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          decision: reviewDecision,
          admin_id: 'admin@instabids.com', // Should come from auth context
          notes: reviewNotes,
          reason: reviewReason
        })
      });

      if (response.ok) {
        message.success(`Proposal ${reviewDecision} successfully`);
        setReviewModalVisible(false);
        loadProposals();
        loadStats();
      } else {
        throw new Error('Failed to submit review');
      }
    } catch (error) {
      console.error('Error submitting review:', error);
      message.error('Failed to submit review decision');
    }
  };

  const handleDownload = async (proposal: SubmittedProposal, attachmentId?: string) => {
    try {
      const url = attachmentId 
        ? `/api/proposal-review/${proposal.id}/download?attachment_id=${attachmentId}`
        : `/api/proposal-review/${proposal.id}/download`;
        
      const response = await fetch(url);
      const data = await response.json();
      
      // Open download URL in new tab
      window.open(data.download_url, '_blank');
    } catch (error) {
      console.error('Error downloading:', error);
      message.error('Failed to generate download URL');
    }
  };

  const handleViewFile = async (attachment: ProposalAttachment) => {
    try {
      setCurrentFile(attachment);
      
      // Use the new viewing endpoint for better access control
      const response = await fetch(`/api/proposal-review/${selectedProposal?.id}/attachments/${attachment.id}/view`);
      
      if (!response.ok) {
        throw new Error('Failed to load file for viewing');
      }
      
      const fileData = await response.json();
      
      // For images and PDFs, load via the returned URL
      if (attachment.mime_type?.startsWith('image/') || attachment.mime_type === 'application/pdf') {
        setFileContent(fileData.url);
        if (attachment.mime_type === 'application/pdf') {
          setPageNumber(1);
          setScale(1.0);
        }
        setFileViewerVisible(true);
        return;
      }
      
      // For other files, show download option
      message.info('This file type can only be downloaded');
      
    } catch (error) {
      console.error('Error viewing file:', error);
      message.error('Failed to load file for viewing');
    }
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const isImageFile = (mimeType?: string) => {
    return mimeType?.startsWith('image/');
  };

  const isPdfFile = (mimeType?: string) => {
    return mimeType === 'application/pdf';
  };

  const getFileIcon = (mimeType?: string) => {
    if (isImageFile(mimeType)) return <FileImageOutlined />;
    if (isPdfFile(mimeType)) return <FilePdfOutlined />;
    return <FileTextOutlined />;
  };

  const columns = [
    {
      title: 'Project',
      key: 'project',
      render: (record: SubmittedProposal) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.bid_card_number}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <ProjectOutlined style={{ marginRight: 4 }} />
            {record.project_type}
          </div>
          <Tag color={getUrgencyColor(record.urgency_level)} size="small">
            {record.urgency_level}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Contractor',
      key: 'contractor',
      render: (record: SubmittedProposal) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.contractor_name}</div>
          {record.contact_name && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              <UserOutlined style={{ marginRight: 4 }} />
              {record.contact_name}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Bid Amount',
      key: 'amount',
      render: (record: SubmittedProposal) => (
        <div>
          <div style={{ fontWeight: 500, fontSize: '16px' }}>
            {formatCurrency(record.amount)}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <CalendarOutlined style={{ marginRight: 4 }} />
            {record.timeline_start} - {record.timeline_end}
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: SubmittedProposal) => (
        <div>
          <Tag color={getProposalStatusColor(record.review_status)}>
            {record.review_status.toUpperCase()}
          </Tag>
          {record.requires_review && (
            <Tooltip title={record.flagged_reason}>
              <ExclamationCircleOutlined style={{ color: 'red', marginLeft: 8 }} />
            </Tooltip>
          )}
        </div>
      ),
    },
    {
      title: 'Attachments',
      key: 'attachments',
      render: (record: SubmittedProposal) => (
        <div style={{ textAlign: 'center' }}>
          {record.attachment_count > 0 ? (
            <Badge count={record.attachment_count}>
              <FileTextOutlined style={{ fontSize: '16px' }} />
            </Badge>
          ) : (
            <Text type="secondary">None</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Contact Info',
      key: 'contact_info',
      render: (record: SubmittedProposal) => (
        <div style={{ textAlign: 'center' }}>
          {record.contact_analysis.contact_info_detected ? (
            <div>
              {record.contact_analysis.phones.length > 0 && (
                <PhoneOutlined style={{ color: 'red', marginRight: 4 }} />
              )}
              {record.contact_analysis.emails.length > 0 && (
                <MailOutlined style={{ color: 'red', marginRight: 4 }} />
              )}
              <div style={{ fontSize: '10px', color: 'red' }}>
                {Math.round(record.contact_analysis.confidence * 100)}% confidence
              </div>
            </div>
          ) : (
            <Text type="secondary">Clean</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Submitted',
      key: 'submitted_at',
      render: (record: SubmittedProposal) => (
        <div style={{ fontSize: '12px' }}>
          {new Date(record.submitted_at).toLocaleDateString()}
          <br />
          {new Date(record.submitted_at).toLocaleTimeString()}
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: SubmittedProposal) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetails(record)}
          />
          <Button
            icon={<DownloadOutlined />}
            size="small"
            onClick={() => handleDownload(record)}
          />
          {record.review_status === 'pending' || record.review_status === 'flagged' ? (
            <>
              <Button
                icon={<CheckOutlined />}
                size="small"
                type="primary"
                onClick={() => handleReviewProposal(record, 'approved')}
              />
              <Button
                icon={<CloseOutlined />}
                size="small"
                danger
                onClick={() => handleReviewProposal(record, 'rejected')}
              />
            </>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Submitted Proposals Review</Title>
      <Paragraph>
        Review contractor proposals for contact information violations and approve/reject submissions.
      </Paragraph>

      {/* Statistics Cards */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={4}>
            <Card>
              <Statistic
                title="Total Proposals"
                value={stats.total}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="Needs Review"
                value={stats.flagged}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="Pending"
                value={stats.pending}
                prefix={<CloseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="Approved"
                value={stats.approved}
                prefix={<CheckOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="Rejected"
                value={stats.rejected}
                prefix={<CloseOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="With Attachments"
                value={stats.with_attachments}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <FilterOutlined style={{ marginRight: 8 }} />
            <Text strong>Filters:</Text>
          </Col>
          <Col>
            <Select
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              style={{ width: 120 }}
            >
              <Option value="all">All Status</Option>
              <Option value="pending">Pending</Option>
              <Option value="flagged">Flagged</Option>
              <Option value="approved">Approved</Option>
              <Option value="rejected">Rejected</Option>
            </Select>
          </Col>
          <Col>
            <Select
              value={filters.has_attachments}
              onChange={(value) => setFilters(prev => ({ ...prev, has_attachments: value }))}
              style={{ width: 140 }}
              placeholder="Attachments"
            >
              <Option value={null}>Any</Option>
              <Option value={true}>With Attachments</Option>
              <Option value={false}>No Attachments</Option>
            </Select>
          </Col>
          <Col>
            <Select
              value={filters.has_contact_info}
              onChange={(value) => setFilters(prev => ({ ...prev, has_contact_info: value }))}
              style={{ width: 140 }}
              placeholder="Contact Info"
            >
              <Option value={null}>Any</Option>
              <Option value={true}>Has Contact Info</Option>
              <Option value={false}>Clean</Option>
            </Select>
          </Col>
          <Col>
            <Input
              placeholder="Project Type"
              value={filters.project_type}
              onChange={(e) => setFilters(prev => ({ ...prev, project_type: e.target.value }))}
              style={{ width: 150 }}
            />
          </Col>
          <Col>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                loadProposals();
                loadStats();
              }}
            >
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Proposals Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={proposals}
          loading={loading}
          rowKey="id"
          pagination={{
            total: proposals.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} proposals`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Proposal Details Drawer */}
      <Drawer
        title="Proposal Details"
        placement="right"
        width={800}
        onClose={() => setDetailsVisible(false)}
        visible={detailsVisible}
      >
        {selectedProposal && (
          <div>
            {/* Contact Info Alert */}
            {selectedProposal.requires_review && (
              <Alert
                message="Contact Information Detected"
                description={selectedProposal.flagged_reason}
                type="warning"
                icon={<ExclamationCircleOutlined />}
                style={{ marginBottom: 16 }}
                action={
                  <Space>
                    <Button
                      size="small"
                      type="primary"
                      onClick={() => handleReviewProposal(selectedProposal, 'approved')}
                    >
                      Approve
                    </Button>
                    <Button
                      size="small"
                      danger
                      onClick={() => handleReviewProposal(selectedProposal, 'rejected')}
                    >
                      Reject
                    </Button>
                  </Space>
                }
              />
            )}

            {/* Basic Information */}
            <Descriptions title="Project Information" bordered size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Bid Card Number" span={2}>
                {selectedProposal.bid_card_number}
              </Descriptions.Item>
              <Descriptions.Item label="Project Type">
                {selectedProposal.project_type}
              </Descriptions.Item>
              <Descriptions.Item label="Urgency Level">
                <Tag color={getUrgencyColor(selectedProposal.urgency_level)}>
                  {selectedProposal.urgency_level}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Contractor">
                {selectedProposal.contractor_name}
              </Descriptions.Item>
              <Descriptions.Item label="Contact Person">
                {selectedProposal.contact_name || 'Not specified'}
              </Descriptions.Item>
              <Descriptions.Item label="Bid Amount">
                <Text strong style={{ fontSize: '16px' }}>
                  {formatCurrency(selectedProposal.amount)}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Timeline" span={2}>
                {selectedProposal.timeline_start} to {selectedProposal.timeline_end}
              </Descriptions.Item>
              <Descriptions.Item label="Submitted At">
                {new Date(selectedProposal.submitted_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            {/* Proposal Content */}
            <Card title="Proposal Details" style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Project Proposal:</Text>
                <Paragraph style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5' }}>
                  {selectedProposal.proposal}
                </Paragraph>
              </div>

              {selectedProposal.approach && (
                <div style={{ marginBottom: 16 }}>
                  <Text strong>Technical Approach:</Text>
                  <Paragraph style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5' }}>
                    {selectedProposal.approach}
                  </Paragraph>
                </div>
              )}

              {selectedProposal.warranty_details && (
                <div>
                  <Text strong>Warranty Details:</Text>
                  <Paragraph style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5' }}>
                    {selectedProposal.warranty_details}
                  </Paragraph>
                </div>
              )}
            </Card>

            {/* Contact Analysis */}
            {selectedProposal.contact_analysis.contact_info_detected && (
              <Card title="Contact Information Analysis" style={{ marginBottom: 24 }}>
                <Alert
                  type="warning"
                  message={`Confidence: ${Math.round(selectedProposal.contact_analysis.confidence * 100)}%`}
                  description={selectedProposal.contact_analysis.explanation}
                  style={{ marginBottom: 16 }}
                />
                
                {selectedProposal.contact_analysis.phones.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Phone Numbers Found:</Text>
                    <ul>
                      {selectedProposal.contact_analysis.phones.map((phone, idx) => (
                        <li key={idx}>{phone}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedProposal.contact_analysis.emails.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>Email Addresses Found:</Text>
                    <ul>
                      {selectedProposal.contact_analysis.emails.map((email, idx) => (
                        <li key={idx}>{email}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            )}

            {/* Attachments */}
            {attachments.length > 0 && (
              <Card title="Proposal Attachments">
                <List
                  dataSource={attachments}
                  renderItem={(attachment) => (
                    <List.Item
                      actions={[
                        ...(isImageFile(attachment.mime_type) || isPdfFile(attachment.mime_type) 
                          ? [
                              <Button
                                icon={<EyeOutlined />}
                                onClick={() => handleViewFile(attachment)}
                                type="primary"
                              >
                                View
                              </Button>
                            ] 
                          : []),
                        <Button
                          icon={<DownloadOutlined />}
                          onClick={() => handleDownload(selectedProposal, attachment.id)}
                        >
                          Download
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<Avatar icon={getFileIcon(attachment.mime_type)} />}
                        title={attachment.name}
                        description={
                          <div>
                            <div>Type: {attachment.mime_type}</div>
                            <div>Size: {Math.round(attachment.size / 1024)} KB</div>
                            <div>Uploaded: {new Date(attachment.created_at).toLocaleString()}</div>
                            {(isImageFile(attachment.mime_type) || isPdfFile(attachment.mime_type)) && (
                              <Tag color="green" size="small">Viewable</Tag>
                            )}
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            )}
          </div>
        )}
      </Drawer>

      {/* Review Decision Modal */}
      <Modal
        title={`${reviewDecision === 'approved' ? 'Approve' : 'Reject'} Proposal`}
        visible={reviewModalVisible}
        onOk={submitReview}
        onCancel={() => setReviewModalVisible(false)}
        okText={reviewDecision === 'approved' ? 'Approve' : 'Reject'}
        okButtonProps={{ 
          danger: reviewDecision === 'rejected',
          type: reviewDecision === 'approved' ? 'primary' : 'default'
        }}
      >
        {selectedProposal && (
          <div>
            <p>
              Are you sure you want to <strong>{reviewDecision}</strong> the proposal from{' '}
              <strong>{selectedProposal.contractor_name}</strong> for project{' '}
              <strong>{selectedProposal.bid_card_number}</strong>?
            </p>

            <div style={{ marginBottom: 16 }}>
              <Text strong>Admin Notes (Optional):</Text>
              <TextArea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add any notes about this decision..."
                rows={3}
                style={{ marginTop: 8 }}
              />
            </div>

            {reviewDecision === 'rejected' && (
              <div>
                <Text strong>Rejection Reason:</Text>
                <TextArea
                  value={reviewReason}
                  onChange={(e) => setReviewReason(e.target.value)}
                  placeholder="Please specify the reason for rejection..."
                  rows={2}
                  style={{ marginTop: 8 }}
                />
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* File Viewer Modal */}
      <Modal
        title={
          <div>
            <span style={{ marginRight: 8 }}>{getFileIcon(currentFile?.mime_type)}</span>
            {currentFile?.name}
            {isPdfFile(currentFile?.mime_type) && numPages && (
              <span style={{ marginLeft: 16, fontSize: '14px', color: '#666' }}>
                Page {pageNumber} of {numPages}
              </span>
            )}
          </div>
        }
        visible={fileViewerVisible}
        onCancel={() => {
          setFileViewerVisible(false);
          setCurrentFile(null);
          setFileContent(null);
          setPageNumber(1);
          setScale(1.0);
          setNumPages(null);
        }}
        width="80%"
        style={{ top: 20 }}
        footer={[
          <Space key="controls">
            {isPdfFile(currentFile?.mime_type) && (
              <>
                <Button
                  icon={<ZoomOutOutlined />}
                  onClick={() => setScale(Math.max(0.5, scale - 0.25))}
                  disabled={scale <= 0.5}
                >
                  Zoom Out
                </Button>
                <Button
                  icon={<ZoomInOutlined />}
                  onClick={() => setScale(Math.min(2.0, scale + 0.25))}
                  disabled={scale >= 2.0}
                >
                  Zoom In
                </Button>
                <Button
                  onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
                  disabled={pageNumber <= 1}
                >
                  Previous Page
                </Button>
                <Button
                  onClick={() => setPageNumber(Math.min(numPages || 1, pageNumber + 1))}
                  disabled={pageNumber >= (numPages || 1)}
                >
                  Next Page
                </Button>
              </>
            )}
            <Button
              icon={<DownloadOutlined />}
              onClick={() => {
                if (selectedProposal && currentFile) {
                  handleDownload(selectedProposal, currentFile.id);
                }
              }}
            >
              Download
            </Button>
            <Button 
              icon={<CloseCircleOutlined />}
              onClick={() => {
                setFileViewerVisible(false);
                setCurrentFile(null);
                setFileContent(null);
                setPageNumber(1);
                setScale(1.0);
                setNumPages(null);
              }}
            >
              Close
            </Button>
          </Space>
        ]}
      >
        <div style={{ textAlign: 'center', minHeight: '400px' }}>
          {currentFile && fileContent && (
            <>
              {/* Image Viewer */}
              {isImageFile(currentFile.mime_type) && (
                <div className="image-viewer-container">
                  <Image
                    src={fileContent}
                    alt={currentFile.name}
                    style={{ maxWidth: '100%', maxHeight: '70vh' }}
                    placeholder={
                      <div style={{ padding: '60px', color: '#999' }}>
                        Loading image...
                      </div>
                    }
                    preview={{
                      mask: <div>Click to enlarge</div>
                    }}
                  />
                </div>
              )}

              {/* PDF Viewer */}
              {isPdfFile(currentFile.mime_type) && (
                <div className="pdf-viewer-container">
                  <div style={{ padding: '60px', color: '#999', textAlign: 'center' }}>
                    PDF viewer not available. Please download the file to view.
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default SubmittedProposalsTab;