# 🎨 InstaBids Universal Design System

## Core Philosophy
Following shadcn/ui principles - we own the code, not locked into a library.

## 1. Design Tokens (The Foundation)

### Colors
```typescript
// Primary Palette - Blue (Trust & Professionalism)
export const colors = {
  primary: {
    50: '#eff6ff',   // Lightest backgrounds
    100: '#dbeafe',  // Hover states
    200: '#bfdbfe',  // Borders
    300: '#93c5fd',  // Accents
    400: '#60a5fa',  // Interactive
    500: '#3b82f6',  // Primary actions
    600: '#2563eb',  // Hover primary
    700: '#1d4ed8',  // Active states
    800: '#1e40af',  // Deep emphasis
    900: '#1e3a8a',  // Darkest
  },
  
  // Semantic Colors
  success: {
    50: '#f0fdf4',
    500: '#22c55e',
    700: '#15803d'
  },
  warning: {
    50: '#fefce8',
    500: '#eab308',
    700: '#a16207'
  },
  danger: {
    50: '#fef2f2',
    500: '#ef4444',
    700: '#b91c1c'
  },
  
  // Neutral (Gray)
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  }
};

// Spacing Scale (Consistent rhythm)
export const spacing = {
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
};

// Typography Scale
export const typography = {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '1.875rem', // 30px
  '4xl': '2.25rem',  // 36px
};

// Border Radius
export const radius = {
  none: '0',
  sm: '0.125rem',   // 2px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',
};

// Shadows (Elevation)
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
};
```

## 2. Component Architecture

### Layer 1: Primitives (Atoms)
The smallest building blocks - pure, single-purpose components.

```typescript
// Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}

// Input.tsx
interface InputProps {
  variant?: 'default' | 'filled' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  error?: boolean;
  icon?: React.ReactNode;
}

// Card.tsx (Already created ✅)
// Badge.tsx (Already created ✅)
// LoadingSpinner.tsx (Already created ✅)
```

### Layer 2: Compounds (Molecules)
Components made from primitives.

```typescript
// FormField.tsx (Label + Input + Error)
// SearchBar.tsx (Input + Icon + Button)
// Notification.tsx (Card + Icon + Text + Close)
// Avatar.tsx (Image + Fallback + Status)
```

### Layer 3: Composites (Organisms)
Complex, feature-complete components.

```typescript
// BidCard.tsx (Card + Badge + Button + Avatar)
// ContractorProfile.tsx (Avatar + Card + Stats + Actions)
// ProjectWorkspace.tsx (Multiple Cards + Navigation + Actions)
```

## 3. Component Patterns

### Variant Pattern
```typescript
const variants = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
  ghost: 'bg-transparent hover:bg-gray-100',
  danger: 'bg-red-600 text-white hover:bg-red-700'
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg'
};
```

### Composition Pattern
```typescript
// Instead of one mega-component, compose smaller ones
<Card>
  <CardHeader>
    <CardTitle>Project Details</CardTitle>
    <CardDescription>Manage your project</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content here */}
  </CardContent>
  <CardFooter>
    <Button>Save Changes</Button>
  </CardFooter>
</Card>
```

## 4. Migration Strategy

### Phase 1: Core Primitives (Week 1)
- [x] Card
- [x] Badge  
- [x] LoadingSpinner
- [ ] Button (enhance existing)
- [ ] Input
- [ ] Select
- [ ] Checkbox/Radio
- [ ] Modal/Dialog
- [ ] Tooltip
- [ ] Dropdown

### Phase 2: Compound Components (Week 2)
- [ ] FormField
- [ ] SearchBar
- [ ] DataTable
- [ ] Navigation
- [ ] Tabs
- [ ] Accordion
- [ ] Alert/Toast

### Phase 3: Domain Components (Week 3)
- [ ] BidCard (unified)
- [ ] ContractorCard
- [ ] ProjectCard
- [ ] MessagingThread
- [ ] DashboardWidget

### Phase 4: Page Templates (Week 4)
- [ ] DashboardLayout
- [ ] FormLayout
- [ ] MarketplaceLayout
- [ ] ChatLayout

## 5. Implementation Rules

### DO's:
✅ Use Tailwind utility classes
✅ Follow variant/size pattern
✅ Make components composable
✅ Support dark mode from start
✅ Use forwardRef for all inputs
✅ Include proper TypeScript types
✅ Add loading/disabled states

### DON'Ts:
❌ No inline styles
❌ No custom CSS files
❌ No !important
❌ No hardcoded colors (use tokens)
❌ No pixel values (use spacing scale)
❌ No breaking existing props

## 6. File Structure

```
src/components/ui/
├── primitives/           # Basic building blocks
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   └── ...
├── compounds/           # Composed from primitives
│   ├── FormField.tsx
│   ├── SearchBar.tsx
│   └── ...
├── utils/              # Helper functions
│   ├── cn.ts
│   └── variants.ts
├── tokens/             # Design tokens
│   ├── colors.ts
│   ├── spacing.ts
│   └── typography.ts
└── index.ts           # Barrel export
```

## 7. Usage Examples

### Basic Usage
```tsx
import { Button, Card, Input } from '@/components/ui';

<Card variant="elevated">
  <Input placeholder="Enter project name" />
  <Button variant="primary" size="lg">
    Create Project
  </Button>
</Card>
```

### With Composition
```tsx
<Card>
  <CardHeader>
    <CardTitle>Bathroom Remodel</CardTitle>
    <Badge variant="success">Active</Badge>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      {/* Project details */}
    </div>
  </CardContent>
  <CardFooter className="flex gap-2">
    <Button variant="secondary">Cancel</Button>
    <Button variant="primary">Submit Bid</Button>
  </CardFooter>
</Card>
```

## 8. Mobile Considerations

All components designed with mobile-first approach:
- Touch-friendly tap targets (min 44x44px)
- Responsive typography scales
- Stack layouts on small screens
- Gesture support where needed
- Performance optimized

## 9. Accessibility

Every component includes:
- Proper ARIA labels
- Keyboard navigation
- Focus indicators
- Screen reader support
- Color contrast compliance

## 10. Next Steps

1. **Immediate**: Fix broken imports with universal components
2. **This Week**: Build remaining primitives
3. **Next Week**: Create compound components
4. **Month 1**: Migrate all pages to new system
5. **Month 2**: Add mobile-specific variants
6. **Month 3**: Full mobile app using same components