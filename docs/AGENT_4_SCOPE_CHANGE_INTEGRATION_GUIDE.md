# Agent 4 - Scope Change Notification Integration Guide
**Author**: Agent 3 (Homeowner UX)  
**Date**: August 8, 2025  
**Purpose**: Integration guide for scope change notifications in contractor messaging interface

## 🎯 OVERVIEW

The intelligent messaging system now detects when homeowners make project scope changes and can notify other contractors. **Agent 4 needs to integrate these notifications into the contractor messaging interface** so contractors see bid updates in real-time.

## 🚀 WHAT'S BEEN BUILT FOR YOU

### **✅ COMPLETE API ENDPOINTS READY**
- **Scope change notification system** with GPT-5 detection
- **Database tables** for storing notifications
- **Message routing** to all contractors on a bid card
- **Homeowner approval system** for sending notifications

### **✅ API ENDPOINTS AVAILABLE**

#### 1. Get Scope Change Notifications for Contractor
```http
GET /api/intelligent-messages/scope-change-notifications/{contractor_id}
?bid_card_id=optional-filter-by-bid-card
```

**Response:**
```json
{
  "success": true,
  "notifications": [
    {
      "id": "msg-123",
      "content": "📋 Project Update: The homeowner has made changes to material specifications and additional features. Please review the updated project details and adjust your bid accordingly if needed. All contractors are receiving this same notification to ensure everyone has the most current project information.",
      "message_type": "scope_change_notification",
      "created_at": "2025-08-08T10:30:00Z",
      "is_read": false,
      "metadata": {
        "scope_changes": ["material_change", "feature_addition"],
        "scope_change_details": {
          "material_change": {
            "original": "rocks around trees",
            "updated": "mulch around trees"
          }
        }
      }
    }
  ]
}
```

#### 2. Health Check (Test if system is working)
```http
GET /api/intelligent-messages/health
```

## 🏗️ WHAT YOU NEED TO BUILD

### **1. CONTRACTOR MESSAGING INTERFACE UPDATES**

#### **Add System Message Display**
In your contractor messaging component, add special handling for system messages:

```typescript
interface ScopeChangeNotification {
  id: string;
  content: string;
  message_type: "scope_change_notification";
  created_at: string;
  is_read: boolean;
  metadata: {
    scope_changes: string[];
    scope_change_details: Record<string, any>;
  };
}

// Add to your messaging component
const ScopeChangeMessage = ({ notification }: { notification: ScopeChangeNotification }) => {
  return (
    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 my-4 rounded-r-lg">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          📋 {/* System icon */}
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-blue-800">
            Bid Card Updated
          </p>
          <p className="mt-1 text-sm text-blue-700">
            {notification.content}
          </p>
          <div className="mt-2 text-xs text-blue-600">
            Changes: {notification.metadata.scope_changes.join(", ")}
          </div>
          <button className="mt-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600">
            Review Updated Project Details
          </button>
        </div>
      </div>
    </div>
  );
};
```

#### **Update Message List to Include Notifications**
```typescript
const ContractorMessagingInterface = ({ contractorId, bidCardId }) => {
  const [scopeNotifications, setScopeNotifications] = useState([]);
  
  useEffect(() => {
    // Fetch scope change notifications
    fetch(`/api/intelligent-messages/scope-change-notifications/${contractorId}?bid_card_id=${bidCardId}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setScopeNotifications(data.notifications);
        }
      });
  }, [contractorId, bidCardId]);
  
  // Merge notifications with regular messages chronologically
  const allMessages = useMemo(() => {
    return [...regularMessages, ...scopeNotifications]
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }, [regularMessages, scopeNotifications]);
  
  return (
    <div className="messaging-interface">
      {allMessages.map(message => (
        message.message_type === "scope_change_notification" 
          ? <ScopeChangeMessage key={message.id} notification={message} />
          : <RegularMessage key={message.id} message={message} />
      ))}
    </div>
  );
};
```

### **2. BID CARD UPDATED INDICATORS**

#### **Add Scope Change Badge to Bid Cards**
```typescript
const BidCardHeader = ({ bidCard }) => {
  const hasRecentScopeChanges = bidCard.scope_last_updated && 
    new Date(bidCard.scope_last_updated) > new Date(Date.now() - 24 * 60 * 60 * 1000);
  
  return (
    <div className="bid-card-header flex items-center justify-between">
      <h3>{bidCard.project_type}</h3>
      {hasRecentScopeChanges && (
        <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">
          Updated 📋
        </span>
      )}
    </div>
  );
};
```

### **3. REAL-TIME UPDATES (OPTIONAL)**

#### **WebSocket Integration for Live Notifications**
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8008/ws');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'scope_change_notification' && data.contractor_id === contractorId) {
      // Add new notification to state
      setScopeNotifications(prev => [...prev, data.notification]);
      
      // Show toast notification
      toast.info('Project scope has been updated!', {
        action: {
          label: 'View Changes',
          onClick: () => scrollToLatestNotification()
        }
      });
    }
  };
  
  return () => ws.close();
}, [contractorId]);
```

## 📊 USER EXPERIENCE FLOW

### **Contractor's View:**
1. **Regular conversation** with homeowner
2. **System notification appears**: "📋 Project Update: The homeowner has made changes to material specifications..."
3. **Orange "Updated" badge** appears on bid card
4. **"Review Updated Details" button** to see what changed
5. **Continue conversation** with updated project knowledge

### **Example Timeline:**
```
10:30 AM - Contractor: "What type of materials do you prefer around the trees?"
10:35 AM - [SYSTEM] Project Update: The homeowner has made changes to material specifications and additional features...
10:36 AM - Contractor can now reference the updated requirements
```

## 🧪 TESTING YOUR INTEGRATION

### **Manual Test Steps:**
1. **Start your contractor interface**
2. **Call the API**: `GET /api/intelligent-messages/scope-change-notifications/test-contractor-123`
3. **Verify notifications display** correctly in messaging interface
4. **Test notification styling** and interaction buttons

### **Test Data Available:**
- **Test Contractor ID**: `test-contractor-123` 
- **Test Bid Card ID**: `test-bid-card-123`
- **Mock notifications** available in database for testing

## 🔧 INTEGRATION CHECKLIST

- [ ] **Fetch scope change notifications** for contractor
- [ ] **Display system messages** with special styling in messaging interface
- [ ] **Add "Updated" badges** to bid cards with recent scope changes
- [ ] **Handle notification read status** (mark as read when viewed)
- [ ] **Add "Review Changes" button** linking to updated bid card details
- [ ] **Test with mock data** to verify all functionality works
- [ ] **Optional: Add WebSocket** for real-time notification delivery

## 📞 SUPPORT

**Questions?** The intelligent messaging system is fully operational with:
- ✅ GPT-5 scope change detection
- ✅ Database storage for notifications  
- ✅ API endpoints for retrieval
- ✅ Homeowner approval workflow

**Integration should be straightforward** - just fetch the notifications and display them in your messaging interface with special formatting.

**API Base URL**: `http://localhost:8008/api/intelligent-messages/`

## 🎯 EXPECTED OUTCOME

After integration, contractors will:
1. **See scope change notifications** immediately in their messaging interface
2. **Know when bid requirements change** without having to guess
3. **Stay updated** on project modifications in real-time
4. **Have equal information** as all other contractors (fair bidding)

This ensures all contractors have the same project information and can provide accurate, competitive bids.