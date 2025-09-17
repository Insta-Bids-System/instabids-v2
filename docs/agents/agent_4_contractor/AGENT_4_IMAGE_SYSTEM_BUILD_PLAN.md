# Agent 4 Contractor Image System - Build Plan & PRD
**Last Updated**: January 31, 2025  
**Status**: BUILD PLAN READY ✅

## Product Requirements Document (PRD) ✅

### **Objective**
Build a comprehensive contractor-only visual portfolio system that automatically collects, organizes, and analyzes contractor work images to improve project matching and showcase contractor capabilities.

### **Success Criteria**
- 80%+ of contractors have visual portfolios within 24 hours of onboarding
- 15%+ improvement in project-contractor match accuracy
- 60%+ homeowner engagement with contractor profiles increases

### **Non-Functional Requirements**
- Image processing latency <3 seconds
- Storage costs <$50/month for 1000 contractors
- 99.5% image availability uptime

## Build Plan - 8 Hour Implementation ✅

### **Phase 1: Database Foundation** (2 hours)
```sql
-- Create contractor image tables
-- Set up storage buckets 
-- Configure RLS policies
```

#### Tasks:
- [ ] Create `contractor_images` table with AI analysis fields
- [ ] Create `contractor_image_collections` table 
- [ ] Create `contractor_image_collection_items` junction table
- [ ] Set up Supabase storage bucket `contractor-media` with folders
- [ ] Configure RLS policies for contractor-only access

### **Phase 2: Backend API Development** (3 hours)
```python
# Core image management endpoints
# Integration with existing CoIA agent
# Automated scraping integration
```

#### Tasks:
- [ ] `/api/contractors/{id}/images` - GET/POST endpoints
- [ ] Image upload handling with thumbnail generation
- [ ] Integration with existing PlaywrightWebsiteEnricher for auto-collection
- [ ] AI image analysis using Claude Vision API
- [ ] Background job system for bulk image processing

### **Phase 3: Frontend Gallery Interface** (2 hours)
```typescript
// ContractorImageGallery component
// Upload interface
// Image management tools
```

#### Tasks:
- [ ] `ContractorImageGallery.tsx` - Main gallery component
- [ ] `ImageUploadZone.tsx` - Drag & drop upload interface
- [ ] `ContractorImageCard.tsx` - Individual image display
- [ ] Integration with existing contractor dashboard
- [ ] Mobile-responsive image grid

### **Phase 4: Integration Testing** (1 hour)
```bash
# End-to-end workflow testing
# Performance validation
# Security verification
```

#### Tasks:
- [ ] Test automated image collection during contractor onboarding
- [ ] Verify image categorization and AI analysis accuracy
- [ ] Performance testing with bulk image uploads
- [ ] Security testing for image access controls
- [ ] Mobile compatibility testing

## File Structure ✅

```
agent_specifications/agent_4_contractor_docs/
├── AGENT_4_IMAGE_SYSTEM_BUILD_PLAN.md     # This file
├── AGENT_4_CONTRACTOR_IMAGE_SYSTEM.md     # Technical specification
└── AGENT_4_DATABASE_ANALYSIS.md           # Database investigation results

ai-agents/
├── agents/coia/
│   ├── image_collector.py                 # NEW: Automated image collection
│   └── image_analyzer.py                  # NEW: AI image analysis
├── api/
│   └── contractor_images.py               # NEW: Image management endpoints
└── database/migrations/
    └── 011_contractor_images.sql          # NEW: Database schema

web/src/components/contractor/
├── ContractorImageGallery.tsx             # NEW: Main gallery interface
├── ImageUploadZone.tsx                    # NEW: Upload interface
├── ContractorImageCard.tsx                # NEW: Image display component
└── ImageCollectionManager.tsx             # NEW: Portfolio organization
```

## Implementation Notes ✅

### **Database Migration Priority**
1. Create tables first (contractor_images is foundation)
2. Set up storage buckets with proper folder structure
3. Configure RLS policies to match existing contractors table

### **Integration Points**
- **CoIA Agent**: Trigger image collection after profile creation
- **PlaywrightWebsiteEnricher**: Enhanced to collect portfolio images
- **ContractorDashboard**: Add image gallery tab
- **Project Matching**: Use image analysis in contractor selection

### **Performance Considerations**
- Lazy load images in gallery interface
- Generate thumbnails during upload process
- Cache AI analysis results in database
- Use background jobs for bulk operations

### **Security Requirements**
- Contractor-only access to their own images
- Image URL signing for secure access
- Malware scanning for uploaded files
- GDPR compliance for scraped images

This focused build plan keeps everything within Agent 4's domain and provides a complete contractor visual portfolio system.