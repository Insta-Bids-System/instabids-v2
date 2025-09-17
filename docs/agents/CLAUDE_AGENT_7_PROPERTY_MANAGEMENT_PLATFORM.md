# Agent 7: Property Management Platform
**Domain**: Independent Property Management System  
**Agent Identity**: Property Management Platform Specialist  
**Last Updated**: August 8, 2025

## 🏢 **YOUR DOMAIN - PROPERTY MANAGEMENT PLATFORM**

You are **Agent 7** - responsible for building a **completely separate property management platform** that operates independently from the InstaBids contractor ecosystem.

---

## 🚨 **CRITICAL: CLEAN SLATE ARCHITECTURE**

### **THIS IS A SEPARATE PRODUCT**
- **NOT an extension** of InstaBids contractor platform
- **Different target audience**: Property managers vs contractors/homeowners
- **Independent infrastructure**: Separate UI, database, workflows
- **Professional B2B focus**: Multi-property, multi-tenant management

### **SEPARATE BUT RELATED**
- **Same tech stack**: React + Vite, FastAPI, Supabase, Docker
- **Shared infrastructure**: Can use same deployment and CI/CD
- **Reusable components**: Basic UI elements, auth patterns
- **Different domain**: Could be propertymanagers.com or instabids.com/pm

---

## 🏗️ **ARCHITECTURE FOUNDATION**

### **🆕 YOUR CODE STRUCTURE**
```
# Backend - Property Management System
ai-agents/agents/property_management/     # Property management logic
├── property_manager.py                   # Core property management
├── tenant_manager.py                     # Tenant lifecycle management  
├── maintenance_tracker.py               # Maintenance request system
├── financial_manager.py                 # Rent collection, reporting
└── notification_system.py               # Property manager notifications

# API Layer
ai-agents/api/property_api.py            # Property management APIs
ai-agents/routers/property_routes.py     # Property management endpoints

# Frontend - Property Management UI  
web/src/pages/property/                  # Property management pages
├── dashboard/                           # Property manager dashboard
├── properties/                          # Property listing and details
├── tenants/                             # Tenant management interface
├── maintenance/                         # Maintenance request tracking
├── financials/                          # Financial reporting and rent
└── settings/                            # Property manager preferences

web/src/components/property/             # Property-specific components  
├── PropertyCard.tsx                     # Individual property display
├── TenantList.tsx                       # Tenant management components
├── MaintenanceQueue.tsx                 # Maintenance request queue
├── FinancialDashboard.tsx              # Financial reporting widgets
└── PropertyManagerNav.tsx              # Navigation for property platform

web/src/services/property-api.ts         # Property management API calls
```

### **🗄️ DATABASE SCHEMA (TO BE DESIGNED)**
```sql
-- Core property management tables (fresh database design)
property_managers                        # Property manager profiles
properties                              # Property definitions and details
tenants                                 # Tenant information and lease data
lease_agreements                        # Lease terms and conditions
maintenance_requests                    # Maintenance and repair tracking
financial_transactions                  # Rent payments and expenses
property_documents                      # Lease documents, certificates
notifications                          # Property manager notifications
reports                                # Generated financial reports
```

---

## 📋 **WAITING FOR REQUIREMENTS**

### **CURRENT STATUS: READY FOR PRD**
You are ready to analyze Product Requirements Documents (PRDs) and build the property management platform according to specifications.

### **Expected PRD Documents:**
```
C:\Users\Not John Or Justin\Documents\instabids\docs\agent_7_property_docs\
├── PROPERTY_MANAGEMENT_PRD.md           # Main product requirements
├── USER_PERSONAS.md                     # Property manager personas  
├── FEATURE_SPECIFICATIONS.md            # Detailed feature specs
├── DATABASE_REQUIREMENTS.md             # Data model requirements
├── UI_UX_REQUIREMENTS.md                # Interface specifications
└── INTEGRATION_REQUIREMENTS.md         # External integrations needed
```

### **What I Need To Build:**
- **Property Management Core**: Property listings, tenant management
- **Financial Management**: Rent collection, expense tracking, reporting
- **Maintenance System**: Request tracking, vendor coordination  
- **Communication Tools**: Tenant communication, notifications
- **Reporting Dashboard**: Financial reports, occupancy analytics
- **Document Management**: Lease agreements, certificates, records

---

## 🎯 **EXPECTED FEATURE CATEGORIES**

### **👤 Property Manager Dashboard**
- Portfolio overview with key metrics
- Recent activity and notifications
- Financial performance summaries
- Maintenance request status
- Occupancy rates and trends

### **🏠 Property Management** 
- Property listings and details
- Property photos and documents
- Maintenance history and scheduling
- Property-specific financial tracking
- Vacancy management and marketing

### **👥 Tenant Management**
- Tenant profiles and lease information
- Rent collection and payment tracking  
- Communication and messaging tools
- Lease renewal and termination processes
- Tenant screening and application processing

### **🔧 Maintenance & Repairs**
- Maintenance request submission and tracking
- Vendor management and coordination
- Work order management and approval
- Maintenance cost tracking and budgeting
- Preventive maintenance scheduling

### **💰 Financial Management**
- Rent collection and late fee management
- Expense tracking and categorization
- Financial reporting and analytics
- Budget planning and variance analysis
- Tax document generation and reporting

---

## 🚀 **DEVELOPMENT PHASES**

### **Phase 1: Requirements Analysis** 
- Analyze PRD documents and requirements
- Design database schema for property management
- Plan API architecture and data flows
- Create user flow diagrams and wireframes

### **Phase 2: MVP Core Features**
- Property manager authentication and profiles
- Basic property listing and management
- Simple tenant information tracking
- Basic maintenance request system
- Essential financial tracking

### **Phase 3: Advanced Property Management**
- Comprehensive tenant management with leases
- Advanced maintenance workflow automation
- Detailed financial reporting and analytics
- Document management and storage
- Notification and communication systems

### **Phase 4: Integration & Optimization**
- External service integrations (accounting, payments)
- Mobile-responsive property management
- Advanced reporting and business intelligence
- Workflow automation and optimization
- Multi-property portfolio management

---

## 📊 **SUCCESS METRICS**

### **Property Manager Efficiency**
- Time saved on property management tasks
- Reduction in manual data entry and paperwork
- Faster maintenance request resolution times
- Improved tenant satisfaction scores

### **Financial Performance**  
- Rent collection rates and on-time payments
- Maintenance cost tracking and optimization
- Vacancy rates and time-to-fill metrics
- Overall portfolio profitability analysis

### **System Performance**
- User adoption and engagement rates
- Platform uptime and reliability
- Response times for critical operations
- Customer support ticket resolution times

---

## 💡 **DESIGN PRINCIPLES**

### **Professional B2B Focus**
- Clean, professional interface design
- Efficient workflows for busy property managers
- Comprehensive data and reporting capabilities
- Reliable and scalable system architecture

### **Independent Platform**
- Separate user experience from InstaBids
- Dedicated property management workflows
- Professional property management terminology
- B2B-focused feature set and pricing

### **Scalable Architecture**
- Support for multiple properties per manager
- Multi-tenant SaaS architecture capability
- Integration-ready for external services
- Performance optimized for large portfolios

---

## ⚠️ **CRITICAL BOUNDARIES**

### **What You DON'T Touch**
- **InstaBids contractor platform**: Separate codebase sections
- **Existing 41 tables**: Property management uses fresh database schema
- **Contractor workflows**: Property management has different user journeys
- **Homeowner interfaces**: Property managers have different needs

### **What You DO Coordinate**
- **Shared infrastructure**: Use same Docker, CI/CD, deployment
- **UI component library**: Reuse basic components where logical  
- **Authentication patterns**: Consistent auth but separate user types
- **API architecture**: Follow same FastAPI patterns but separate endpoints

---

**Your mission: Build a professional property management platform that operates independently while leveraging the proven InstaBids technical foundation.**

## 🚨 **READY FOR PRD DOCUMENTS**

**Status**: Architecture foundation complete. Waiting for Product Requirements Documents to begin development.

When you provide PRD documents, I will:
1. **Analyze requirements** and map feature specifications  
2. **Design database schema** based on property management needs
3. **Build API architecture** for property management workflows
4. **Create user interface** optimized for property managers
5. **Implement core features** according to PRD priorities