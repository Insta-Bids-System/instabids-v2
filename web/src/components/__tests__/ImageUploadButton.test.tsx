import { describe, it, expect, beforeEach, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen, waitFor } from '../../test/test-utils'
import ImageUploadButton from '../ImageUploadButton'
import toast from 'react-hot-toast'

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}))

// Mock FileReader
const mockFileReader = {
  readAsDataURL: vi.fn(),
  result: 'data:image/jpeg;base64,mockbase64data',
  onloadend: null as any,
}

global.FileReader = vi.fn(() => mockFileReader) as any

describe('ImageUploadButton', () => {
  const user = userEvent.setup()
  const mockOnUpload = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockFileReader.onloadend = null
  })

  it('renders upload button with default props', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    expect(screen.getByText('Upload Image')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('renders with custom button text and upload icon', () => {
    render(
      <ImageUploadButton 
        onUpload={mockOnUpload} 
        buttonText="Add Photo"
        buttonIcon="upload"
      />
    )
    
    expect(screen.getByText('Add Photo')).toBeInTheDocument()
  })

  it('opens file dialog when button is clicked', async () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const button = screen.getByText('Upload Image')
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    
    // Mock click method
    const clickSpy = vi.spyOn(fileInput, 'click').mockImplementation(() => {})
    
    await user.click(button)
    
    expect(clickSpy).toHaveBeenCalled()
    clickSpy.mockRestore()
  })

  it('accepts valid image file and shows preview', async () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test image'], 'test.jpg', { type: 'image/jpeg' })
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    // Trigger change event
    await user.upload(fileInput, file)
    
    // Simulate FileReader onloadend
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      // Should show preview with Send and Cancel buttons
      expect(screen.getByAltText('Preview')).toBeInTheDocument()
      expect(screen.getByText('Send')).toBeInTheDocument()
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })
  })

  it('validates file type and shows error for invalid files', async () => {
    render(<ImageUploadButton onUpload={mockOnUpload} accept="image/jpeg,image/png" />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('Invalid file type'))
  })

  it('validates file size and shows error for oversized files', async () => {
    render(<ImageUploadButton onUpload={mockOnUpload} maxSize={1} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    
    // Create a file larger than 1MB (1MB = 1024 * 1024 bytes)
    const largeFile = new File(['x'.repeat(2 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [largeFile],
      configurable: true,
    })
    
    await user.upload(fileInput, largeFile)
    
    expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('File size exceeds 1MB limit'))
  })

  it('calls onUpload when Send button is clicked', async () => {
    const mockUpload = vi.fn().mockResolvedValue(undefined)
    render(<ImageUploadButton onUpload={mockUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    // Trigger FileReader onloadend
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      expect(screen.getByText('Send')).toBeInTheDocument()
    })
    
    const sendButton = screen.getByText('Send')
    await user.click(sendButton)
    
    expect(mockUpload).toHaveBeenCalledWith(file)
  })

  it('clears preview when Cancel button is clicked', async () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })
    
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)
    
    // Preview should be cleared
    await waitFor(() => {
      expect(screen.queryByAltText('Preview')).not.toBeInTheDocument()
      expect(screen.getByText('Upload Image')).toBeInTheDocument()
    })
  })

  it('shows loading state during upload', async () => {
    const slowUpload = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
    render(<ImageUploadButton onUpload={slowUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      expect(screen.getByText('Send')).toBeInTheDocument()
    })
    
    const sendButton = screen.getByText('Send')
    await user.click(sendButton)
    
    // Should show loading state
    expect(screen.getByText('Uploading...')).toBeInTheDocument()
    expect(sendButton).toBeDisabled()
  })

  it('handles upload errors gracefully', async () => {
    const failingUpload = vi.fn().mockRejectedValue(new Error('Upload failed'))
    render(<ImageUploadButton onUpload={failingUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      expect(screen.getByText('Send')).toBeInTheDocument()
    })
    
    const sendButton = screen.getByText('Send')
    await user.click(sendButton)
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to upload image')
    })
  })

  it('is disabled when loading prop is true', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} loading={true} />)
    
    const button = screen.getByText('Upload Image')
    expect(button).toBeDisabled()
  })

  it('clears preview after successful upload', async () => {
    const successfulUpload = vi.fn().mockResolvedValue(undefined)
    render(<ImageUploadButton onUpload={successfulUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    await user.upload(fileInput, file)
    
    if (mockFileReader.onloadend) {
      mockFileReader.onloadend()
    }
    
    await waitFor(() => {
      expect(screen.getByText('Send')).toBeInTheDocument()
    })
    
    const sendButton = screen.getByText('Send')
    await user.click(sendButton)
    
    // After successful upload, should return to initial state
    await waitFor(() => {
      expect(screen.queryByAltText('Preview')).not.toBeInTheDocument()
      expect(screen.getByText('Upload Image')).toBeInTheDocument()
    })
  })
})