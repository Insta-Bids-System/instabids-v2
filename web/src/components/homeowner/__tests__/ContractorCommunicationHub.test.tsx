import { describe, it, expect, beforeEach, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '../../../test/test-utils'
import ContractorCommunicationHub from '../ContractorCommunicationHub'

// Mock the API functions
const mockFetch = vi.fn()
global.fetch = mockFetch

const mockBidCardId = 'test-bid-card-123'

const mockProposals = [
  {
    id: 'proposal-1',
    contractor_id: 'contractor-1',
    contractor_name: 'Elite Kitchen Designs',
    contractor_email: 'elite@example.com',
    bid_amount: 15000,
    timeline: 'January 15 - February 28',
    proposal_details: 'Complete kitchen renovation with high-end materials',
    created_at: '2025-01-01T10:00:00Z',
  },
  {
    id: 'proposal-2', 
    contractor_id: 'contractor-2',
    contractor_name: 'Premier Renovations',
    contractor_email: 'premier@example.com',
    bid_amount: 12500,
    timeline: 'January 20 - March 10',
    proposal_details: 'Kitchen renovation with premium finishes',
    created_at: '2025-01-02T14:30:00Z',
  }
]

const mockConversations = [
  {
    id: 'conv-1',
    contractor_id: 'contractor-1',
    contractor_alias: 'Contractor A',
    last_message: 'Looking forward to working on your kitchen project!',
    last_message_at: '2025-01-03T09:15:00Z',
    unread_count: 2,
  },
  {
    id: 'conv-2',
    contractor_id: 'contractor-2', 
    contractor_alias: 'Contractor B',
    last_message: 'I have some questions about your timeline.',
    last_message_at: '2025-01-03T11:20:00Z',
    unread_count: 0,
  }
]

describe('ContractorCommunicationHub', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock successful API responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/proposals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProposals)
        })
      }
      if (url.includes('/api/conversations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockConversations)
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    })
  })

  it('renders contractor communication hub with loading state', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    // Should show loading initially
    expect(screen.getByText(/Loading contractors/i)).toBeInTheDocument()
  })

  it('displays contractors after loading', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    // Wait for contractors to load
    await waitFor(() => {
      expect(screen.getByText('Elite Kitchen Designs')).toBeInTheDocument()
      expect(screen.getByText('Premier Renovations')).toBeInTheDocument()
    })

    // Should display contractor aliases
    expect(screen.getByText('Contractor A')).toBeInTheDocument()
    expect(screen.getByText('Contractor B')).toBeInTheDocument()
  })

  it('shows bid amounts and timelines correctly', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      // Check bid amounts are formatted correctly
      expect(screen.getByText('$15,000')).toBeInTheDocument()
      expect(screen.getByText('$12,500')).toBeInTheDocument()
      
      // Check timelines
      expect(screen.getByText('January 15 - February 28')).toBeInTheDocument()
      expect(screen.getByText('January 20 - March 10')).toBeInTheDocument()
    })
  })

  it('displays unread message indicators', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      // Should show unread count for Contractor A
      expect(screen.getByText('2')).toBeInTheDocument()
      
      // Should not show unread indicator for Contractor B (0 unread)
      const unreadBadges = screen.getAllByTestId(/unread-badge/)
      expect(unreadBadges).toHaveLength(1) // Only one contractor has unread messages
    })
  })

  it('expands contractor details when clicked', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Elite Kitchen Designs')).toBeInTheDocument()
    })

    // Click on the first contractor
    const contractorButton = screen.getByText('Elite Kitchen Designs').closest('button')
    expect(contractorButton).toBeInTheDocument()
    
    await user.click(contractorButton!)
    
    // Should expand to show proposal details
    await waitFor(() => {
      expect(screen.getByText('Complete kitchen renovation with high-end materials')).toBeInTheDocument()
    })
  })

  it('shows messaging interface when contractor is expanded', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Elite Kitchen Designs')).toBeInTheDocument()
    })

    // Click to expand contractor
    const contractorButton = screen.getByText('Elite Kitchen Designs').closest('button')
    await user.click(contractorButton!)
    
    // Should show messaging interface
    await waitFor(() => {
      expect(screen.getByText('Looking forward to working on your kitchen project!')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/Send a message/i)).toBeInTheDocument()
    })
  })

  it('handles date formatting gracefully for invalid dates', async () => {
    // Mock proposals with invalid date
    const invalidDateProposals = [{
      ...mockProposals[0],
      created_at: 'invalid-date-string'
    }]
    
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/proposals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(invalidDateProposals)
        })
      }
      return Promise.resolve({
        ok: true, 
        json: () => Promise.resolve([])
      })
    })

    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      // Should show fallback text instead of crashing
      expect(screen.getByText(/Invalid date|No date/i)).toBeInTheDocument()
    })
  })

  it('allows sending messages to contractors', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Elite Kitchen Designs')).toBeInTheDocument()
    })

    // Expand contractor
    const contractorButton = screen.getByText('Elite Kitchen Designs').closest('button')
    await user.click(contractorButton!)
    
    // Wait for messaging interface
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Send a message/i)).toBeInTheDocument()
    })

    const messageInput = screen.getByPlaceholderText(/Send a message/i)
    const sendButton = screen.getByRole('button', { name: /send/i })
    
    // Type a message
    await user.type(messageInput, 'Hello, I have some questions about your proposal')
    
    // Mock successful message send
    mockFetch.mockImplementationOnce(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ success: true })
    }))
    
    // Send message
    await user.click(sendButton)
    
    // Should clear the input after sending
    await waitFor(() => {
      expect(messageInput).toHaveValue('')
    })
  })

  it('handles API errors gracefully', async () => {
    // Mock API failure
    mockFetch.mockRejectedValue(new Error('Network error'))
    
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    // Should show error state
    await waitFor(() => {
      expect(screen.getByText(/error loading|failed to load/i)).toBeInTheDocument()
    })
  })

  it('collapses expanded contractor when clicked again', async () => {
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      expect(screen.getByText('Elite Kitchen Designs')).toBeInTheDocument()
    })

    const contractorButton = screen.getByText('Elite Kitchen Designs').closest('button')
    
    // Expand contractor
    await user.click(contractorButton!)
    await waitFor(() => {
      expect(screen.getByText('Complete kitchen renovation with high-end materials')).toBeInTheDocument()
    })
    
    // Collapse contractor
    await user.click(contractorButton!)
    await waitFor(() => {
      expect(screen.queryByText('Complete kitchen renovation with high-end materials')).not.toBeInTheDocument()
    })
  })

  it('shows appropriate empty state when no contractors available', async () => {
    // Mock empty responses
    mockFetch.mockImplementation(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve([])
    }))
    
    render(<ContractorCommunicationHub bidCardId={mockBidCardId} />)
    
    await waitFor(() => {
      expect(screen.getByText(/no contractors|no proposals/i)).toBeInTheDocument()
    })
  })
})