import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// Mock Supabase client for testing
const mockSupabase = {
  auth: {
    getUser: vi.fn().mockResolvedValue({ data: { user: null } }),
    getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
    signOut: vi.fn().mockResolvedValue({ error: null }),
    onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
  },
  from: vi.fn().mockReturnValue({
    select: vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        execute: vi.fn().mockResolvedValue({ data: [], error: null })
      })
    }),
    insert: vi.fn().mockReturnValue({
      execute: vi.fn().mockResolvedValue({ data: [], error: null })
    }),
    update: vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        execute: vi.fn().mockResolvedValue({ data: [], error: null })
      })
    }),
    delete: vi.fn().mockReturnValue({
      eq: vi.fn().mockReturnValue({
        execute: vi.fn().mockResolvedValue({ data: [], error: null })
      })
    })
  })
}

// Mock the supabase module
vi.mock('../lib/supabase', () => ({
  supabase: mockSupabase
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  },
  Toaster: () => null,
}))

// Custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
export { mockSupabase }

// Helper functions for common test patterns
export const createMockUser = (overrides = {}) => ({
  id: 'test-user-id',
  email: 'test@example.com',
  user_metadata: { full_name: 'Test User' },
  ...overrides,
})

export const createMockProject = (overrides = {}) => ({
  id: 'test-project-id',
  title: 'Test Project',
  description: 'Test project description',
  project_type: 'home_improvement',
  status: 'active',
  created_at: new Date().toISOString(),
  ...overrides,
})

export const createMockBidCard = (overrides = {}) => ({
  id: 'test-bid-card-id',
  bid_card_number: 'BC-TEST-123',
  project_type: 'home_improvement',
  status: 'generated',
  contractor_count_needed: 4,
  bids_received_count: 0,
  created_at: new Date().toISOString(),
  ...overrides,
})

// User interaction helpers
export const fillFormField = async (user: any, fieldLabelOrRole: string, value: string) => {
  const field = document.querySelector(`[aria-label="${fieldLabelOrRole}"], [placeholder="${fieldLabelOrRole}"], input[name="${fieldLabelOrRole}"]`)
  if (field) {
    await user.clear(field)
    await user.type(field, value)
  }
}

export const clickButtonByText = async (user: any, buttonText: string) => {
  const button = document.querySelector(`button:contains("${buttonText}")`)
  if (button) {
    await user.click(button)
  }
}