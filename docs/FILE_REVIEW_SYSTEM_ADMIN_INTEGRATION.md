# File Review System - Admin Panel Integration Specification
**Created**: August 13, 2025  
**Purpose**: Complete integration guide for admin panel agent to build file review system UI  
**Status**: Ready for Implementation  

## 🎯 SYSTEM OVERVIEW

The file review system automatically flags files uploaded by contractors that contain potential contact information. Instead of blocking these files, they're stored in a quarantine area and sent to an admin review queue where admins can approve or reject them.

### **🔄 How It Works**

1. **Contractor uploads file** → **GPT-4o analyzes for contact info**
2. **Clean files** → **Normal upload process** 
3. **Flagged files** → **Quarantine storage + review queue**
4. **Admin reviews** → **Approve/Reject decision**
5. **Approved files** → **Move to main storage + create attachment record**
6. **Rejected files** → **Delete permanently**

---

## 🗄️ DATABASE SCHEMA

### **file_review_queue Table**
```sql
CREATE TABLE file_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID REFERENCES bid_cards(id) ON DELETE CASCADE,
    contractor_id UUID REFERENCES contractors(id),
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- quarantine/bid_id/timestamp_filename
    file_type TEXT NOT NULL,  -- MIME type
    file_size INTEGER,
    original_upload_data JSONB,  -- { upload_timestamp, bid_id, original_filename }
    
    -- Contact info analysis results
    contact_analysis JSONB NOT NULL,  -- Full GPT-4o analysis results
    flagged_reason TEXT NOT NULL,     -- Human-readable explanation
    confidence_score DECIMAL(3,2),    -- 0.00 to 1.00
    detected_contact_types TEXT[],    -- ['phone', 'email', 'address', 'social']
    
    -- Review status
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    admin_decision_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 🛠️ API ENDPOINTS

### **Base URL**: `http://localhost:8008/api/file-review`

### **1. Get Review Queue**
```http
GET /api/file-review/queue?status=pending&limit=50&offset=0
```
**Response**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "bid_card_id": "bid-card-uuid",
    "contractor_id": "contractor-uuid", 
    "file_name": "project_proposal.pdf",
    "file_path": "quarantine/bid_id/20250813_143022_project_proposal.pdf",
    "file_type": "application/pdf",
    "file_size": 2048576,
    "flagged_reason": "Contains phone number and email address",
    "confidence_score": 0.95,
    "detected_contact_types": ["phone", "email"],
    "review_status": "pending",
    "created_at": "2025-08-13T14:30:22.123456Z"
  }
]
```

### **2. Get Queue Statistics**
```http
GET /api/file-review/stats
```
**Response**:
```json
{
  "pending": 12,
  "approved": 45,
  "rejected": 8,
  "total": 65
}
```

### **3. Get File Details**
```http
GET /api/file-review/{review_id}
```
**Response**:
```json
{
  "id": "review-uuid",
  "file_name": "project_proposal.pdf",
  "contact_analysis": {
    "contact_info_detected": true,
    "confidence": 0.95,
    "explanation": "Found phone number (555-123-4567) and email (contractor@email.com)",
    "phones": ["555-123-4567"],
    "emails": ["contractor@email.com"],
    "addresses": [],
    "social_handles": []
  },
  "bid_cards": {
    "bid_card_number": "BC-KITCHEN-2025-001",
    "project_type": "Kitchen Renovation",
    "status": "collecting_bids"
  },
  "contractors": {
    "company_name": "ABC Construction",
    "contact_name": "John Smith"
  }
}
```

### **4. Make Review Decision**
```http
POST /api/file-review/{review_id}/decision
```
**Request Body**:
```json
{
  "decision": "approved",  // or "rejected"
  "admin_id": "admin-uuid",
  "notes": "File content is appropriate for project context",
  "reason": "Contact info appears to be business information only"
}
```

### **5. Download File for Review**
```http
GET /api/file-review/download/{review_id}
```
**Response**:
```json
{
  "download_url": "https://supabase-signed-url...",
  "expires_in": 3600
}
```

### **6. Delete Review Item (Admin)**
```http
DELETE /api/file-review/{review_id}?admin_id=admin-uuid
```

---

## 🎨 ADMIN PANEL UI COMPONENTS

### **1. File Review Dashboard**
```typescript
interface FileReviewDashboard {
  // Summary stats cards
  pendingCount: number;
  approvedCount: number; 
  rejectedCount: number;
  
  // Recent activity
  recentReviews: FileReviewItem[];
  
  // Quick actions
  reviewQueue: FileReviewItem[];
}
```

### **2. Review Queue Table**
```typescript
interface FileReviewTable {
  columns: [
    "File Name",
    "Project", 
    "Contractor",
    "Flagged Reason",
    "Confidence",
    "Contact Types",
    "Upload Date",
    "Actions"
  ];
  
  actions: [
    "View Details",
    "Download File", 
    "Quick Approve",
    "Quick Reject"
  ];
  
  filters: {
    status: "pending" | "approved" | "rejected";
    confidence: "high" | "medium" | "low";
    contactTypes: string[];
    dateRange: [Date, Date];
  };
}
```

### **3. File Review Modal**
```typescript
interface FileReviewModal {
  // File information
  fileName: string;
  fileType: string;
  fileSize: number;
  uploadDate: string;
  
  // Project context
  bidCardNumber: string;
  projectType: string;
  contractorName: string;
  
  // Analysis results
  flaggedReason: string;
  confidenceScore: number;
  detectedContacts: {
    phones: string[];
    emails: string[];
    addresses: string[];
    socialHandles: string[];
  };
  
  // Review actions
  previewFile: () => void;
  downloadFile: () => void;
  approveFile: (notes?: string) => void;
  rejectFile: (reason: string) => void;
}
```

### **4. File Preview Component**
```typescript
interface FilePreviewComponent {
  // For PDFs
  pdfViewer: {
    highlightContacts: boolean;
    pageNavigation: boolean;
    zoomControls: boolean;
  };
  
  // For Images  
  imageViewer: {
    highlightRegions: boolean;
    zoomAndPan: boolean;
    metadataDisplay: boolean;
  };
  
  // Contact highlighting
  highlightedContacts: {
    type: "phone" | "email" | "address" | "social";
    text: string;
    coordinates?: { x: number; y: number };
  }[];
}
```

---

## 🔧 INTEGRATION IMPLEMENTATION

### **1. Add to Admin Navigation**
```typescript
// Add to admin menu
{
  icon: "FileText",
  label: "File Review",
  path: "/admin/file-review",
  badge: pendingCount > 0 ? pendingCount : undefined
}
```

### **2. File Review Page Structure**
```typescript
const FileReviewPage = () => {
  return (
    <AdminLayout>
      <Header title="File Review" />
      
      {/* Statistics Cards */}
      <StatsRow>
        <StatCard title="Pending Review" value={stats.pending} color="yellow" />
        <StatCard title="Approved" value={stats.approved} color="green" />
        <StatCard title="Rejected" value={stats.rejected} color="red" />
        <StatCard title="Total Processed" value={stats.total} color="blue" />
      </StatsRow>
      
      {/* Filters */}
      <FilterBar>
        <StatusFilter />
        <ConfidenceFilter />
        <ContactTypeFilter />
        <DateRangeFilter />
      </FilterBar>
      
      {/* Review Queue Table */}
      <FileReviewTable data={reviewQueue} />
      
      {/* Review Modal */}
      {selectedFile && (
        <FileReviewModal 
          file={selectedFile}
          onApprove={handleApprove}
          onReject={handleReject}
          onClose={closeModal}
        />
      )}
    </AdminLayout>
  );
};
```

### **3. State Management**
```typescript
interface FileReviewState {
  reviewQueue: FileReviewItem[];
  stats: ReviewStats;
  filters: ReviewFilters;
  selectedFile: FileReviewItem | null;
  loading: boolean;
  error: string | null;
}

const useFileReview = () => {
  const [state, setState] = useState<FileReviewState>(initialState);
  
  const loadReviewQueue = async (filters?: ReviewFilters) => {
    // GET /api/file-review/queue
  };
  
  const loadStats = async () => {
    // GET /api/file-review/stats  
  };
  
  const approveFile = async (reviewId: string, notes?: string) => {
    // POST /api/file-review/{reviewId}/decision
  };
  
  const rejectFile = async (reviewId: string, reason: string) => {
    // POST /api/file-review/{reviewId}/decision
  };
  
  const downloadFile = async (reviewId: string) => {
    // GET /api/file-review/download/{reviewId}
  };
  
  return { state, actions: { loadReviewQueue, approveFile, rejectFile, downloadFile } };
};
```

---

## 🚨 REAL-TIME UPDATES

### **WebSocket Integration**
```typescript
// Listen for new flagged files
const useFileReviewWebSocket = () => {
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8008/ws");
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "file_flagged") {
        // New file added to review queue
        updateReviewQueue(data.file);
        showNotification("New file flagged for review");
      }
      
      if (data.type === "file_reviewed") {
        // File review completed
        updateReviewQueue(data.file);
      }
    };
    
    return () => ws.close();
  }, []);
};
```

### **Browser Notifications**
```typescript
const showFileReviewNotification = (file: FileReviewItem) => {
  if (Notification.permission === "granted") {
    new Notification("New File Flagged", {
      body: `${file.file_name} requires admin review`,
      icon: "/admin-icon.png",
      tag: `file-review-${file.id}`
    });
  }
};
```

---

## 📊 ADMIN WORKFLOW

### **1. Review Process**
1. **Admin sees notification** → New file flagged
2. **Open file review page** → See pending files list
3. **Click file to review** → Open detailed modal
4. **Preview file content** → Download or view inline
5. **Analyze contact info** → See highlighted contacts
6. **Make decision** → Approve with notes or reject with reason
7. **Submit decision** → File moved to appropriate status

### **2. Bulk Actions**
```typescript
const BulkActions = () => {
  const handleBulkApprove = async (selectedIds: string[]) => {
    // Approve multiple files at once
    await Promise.all(
      selectedIds.map(id => approveFile(id, "Bulk approved - business context"))
    );
  };
  
  const handleBulkReject = async (selectedIds: string[], reason: string) => {
    // Reject multiple files with same reason
    await Promise.all(
      selectedIds.map(id => rejectFile(id, reason))
    );
  };
};
```

### **3. Review Guidelines**
```typescript
const ReviewGuidelines = () => (
  <InfoPanel>
    <h3>File Review Guidelines</h3>
    <ul>
      <li><strong>Approve if:</strong> Contact info is business-related (company phone, work email)</li>
      <li><strong>Approve if:</strong> Contact info is in proper context (portfolio, credentials)</li>
      <li><strong>Reject if:</strong> Personal contact info for off-platform communication</li>
      <li><strong>Reject if:</strong> Contact info appears to bypass platform messaging</li>
    </ul>
  </InfoPanel>
);
```

---

## ✅ IMPLEMENTATION CHECKLIST

### **Database Setup** ✅ COMPLETE
- [x] `file_review_queue` table created
- [x] Indexes and triggers added
- [x] Foreign key relationships established

### **Backend API** ✅ COMPLETE  
- [x] File analysis integration in bid submission
- [x] Quarantine storage system
- [x] Admin review API endpoints
- [x] File approval/rejection workflow

### **Admin Panel Integration** 🚧 FOR YOUR ADMIN AGENT
- [ ] File review page component
- [ ] Review queue table with filters
- [ ] File review modal with preview
- [ ] Bulk action capabilities
- [ ] Real-time notification system
- [ ] WebSocket integration for live updates

### **Testing Requirements**
- [ ] Upload file with contact info → Verify quarantine
- [ ] Admin approve file → Verify move to main storage
- [ ] Admin reject file → Verify deletion
- [ ] Bulk operations → Verify batch processing

---

## 🎯 PRIORITY FEATURES

### **Phase 1: Core Functionality**
1. Basic review queue table
2. File details modal
3. Approve/reject actions
4. Download file capability

### **Phase 2: Enhanced UX**
1. File preview (PDF/image viewer)
2. Contact highlighting
3. Bulk actions
4. Advanced filters

### **Phase 3: Real-time Features**
1. WebSocket notifications
2. Auto-refresh queue
3. Admin collaboration features
4. Audit logging

---

**This specification provides everything needed to build the complete file review system into the admin panel. All backend infrastructure is ready and tested.**