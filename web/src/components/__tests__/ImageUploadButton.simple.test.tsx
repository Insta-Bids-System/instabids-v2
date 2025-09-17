import { describe, it, expect, beforeEach, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen } from '../../test/test-utils'
import ImageUploadButton from '../ImageUploadButton'

describe('ImageUploadButton - Basic Tests', () => {
  const mockOnUpload = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload button with default props', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    expect(screen.getByText('Upload Image')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('renders with custom button text', () => {
    render(
      <ImageUploadButton 
        onUpload={mockOnUpload} 
        buttonText="Add Photo"
      />
    )
    
    expect(screen.getByText('Add Photo')).toBeInTheDocument()
  })

  it('renders with upload icon when specified', () => {
    const { container } = render(
      <ImageUploadButton 
        onUpload={mockOnUpload} 
        buttonIcon="upload"
      />
    )
    
    // Check for SVG element (Lucide Upload icon)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders with camera icon by default', () => {
    const { container } = render(
      <ImageUploadButton onUpload={mockOnUpload} />
    )
    
    // Check for SVG element (Lucide Camera icon)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('has hidden file input element', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
    expect(fileInput).toHaveClass('hidden')
  })

  it('file input has correct accept attribute', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} accept="image/png,image/jpeg" />)
    
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toHaveAttribute('accept', 'image/png,image/jpeg')
  })

  it('applies custom className', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} className="custom-class" />)
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('is disabled when loading prop is true', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} loading={true} />)
    
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('button has correct styling classes', () => {
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const button = screen.getByRole('button')
    expect(button).toHaveClass('flex', 'items-center', 'gap-2', 'px-3', 'py-2')
  })

  it('renders both icon and text', () => {
    const { container } = render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    // Should have both SVG icon and text
    const svg = container.querySelector('svg')
    const text = screen.getByText('Upload Image')
    
    expect(svg).toBeInTheDocument()
    expect(text).toBeInTheDocument()
  })

  // Test the button click triggering file dialog (mocked)
  it('attempts to trigger file dialog when clicked', async () => {
    const user = userEvent.setup()
    render(<ImageUploadButton onUpload={mockOnUpload} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const clickSpy = vi.spyOn(fileInput, 'click').mockImplementation(() => {})
    
    const button = screen.getByRole('button')
    await user.click(button)
    
    expect(clickSpy).toHaveBeenCalled()
    clickSpy.mockRestore()
  })
})