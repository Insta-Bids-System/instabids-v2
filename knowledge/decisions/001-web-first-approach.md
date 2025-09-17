# ADR-001: Web-First Development Approach

## Status
Accepted

## Context
Instabids needs to launch quickly with an MVP that serves both homeowners and contractors. We need to decide between:
1. Mobile-first development
2. Web-first development  
3. Parallel web and mobile development

## Decision
We will pursue a **web-first development approach** for Phase 1 (Weeks 1-4), with only basic authentication shells for mobile apps.

## Rationale
1. **Faster Development**: Single codebase to maintain initially
2. **Wider Reach**: Web works on all devices immediately
3. **Easier Testing**: No app store approval process for iterations
4. **Contractor Usage**: Contractors often use tablets/laptops for business
5. **Progressive Enhancement**: Can add mobile apps in Phase 2

## Consequences
### Positive
- Faster time to market
- Lower initial development cost
- Easier to iterate based on user feedback
- Can validate product-market fit before mobile investment

### Negative
- May lose some mobile-first users initially
- Will need responsive design for mobile browsers
- Push notifications limited without native apps

## Implementation
1. Build responsive React web app
2. Use mobile-first CSS (Tailwind)
3. Create PWA for app-like experience
4. Set up React Native project structure for Phase 2