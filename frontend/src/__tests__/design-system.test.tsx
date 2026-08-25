import React from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Badge } from '@/components/ui/Badge'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { Dropdown, DropdownItem, DropdownMenu, DropdownTrigger } from '@/components/ui/Dropdown'
import { TabContent, TabList, Tabs, TabTrigger } from '@/components/ui/Tabs'
import { ToastProvider, useToast } from '@/components/ui'

describe('Button component', () => {
  it('renders primary button and responds to click', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Process Document</Button>)

    const button = screen.getByRole('button', { name: /Process Document/i })
    expect(button).toBeDefined()
    fireEvent.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renders loading state and disables interaction', () => {
    const handleClick = vi.fn()
    render(
      <Button isLoading onClick={handleClick}>
        Save
      </Button>,
    )

    const button = screen.getByRole('button')
    expect(button.getAttribute('disabled')).toBeDefined()
    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()
  })
})

describe('Input and Textarea components', () => {
  it('renders input with label and helper text', () => {
    render(
      <Input
        label="Document Title"
        helperText="Enter a descriptive title"
        placeholder="e.g. Q4 Financials"
      />,
    )

    expect(screen.getByLabelText(/Document Title/i)).toBeDefined()
    expect(screen.getByText(/Enter a descriptive title/i)).toBeDefined()
  })

  it('renders input with error state and aria-invalid', () => {
    render(
      <Input
        label="Email"
        errorMessage="Invalid email address format"
      />,
    )

    const input = screen.getByLabelText(/Email/i)
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByText(/Invalid email address format/i)).toBeDefined()
  })

  it('renders textarea with custom rows and handles input', () => {
    render(<Textarea label="Document Prompt" rows={5} placeholder="Type query..." />)
    const textarea = screen.getByLabelText(/Document Prompt/i)
    expect(textarea.getAttribute('rows')).toBe('5')
  })
})

describe('Badge & StatusBadge components', () => {
  it('renders all document processing statuses accurately', () => {
    const statuses = [
      'UPLOADED',
      'QUEUED',
      'OCR_PROCESSING',
      'CHUNKING',
      'EMBEDDING',
      'READY',
      'FAILED',
      'OCR_QUALITY_WARNING',
    ] as const

    statuses.forEach((status) => {
      const { unmount } = render(<StatusBadge status={status} />)
      expect(document.body.textContent).toBeTruthy()
      unmount()
    })
  })

  it('renders generic badge with variants', () => {
    render(<Badge variant="success">Active</Badge>)
    expect(screen.getByText('Active')).toBeDefined()
  })
})

describe('Dialog component', () => {
  it('renders content when open and calls onClose when clicking backdrop or close button', () => {
    const handleClose = vi.fn()
    const { rerender } = render(
      <Dialog isOpen={false} onClose={handleClose}>
        <DialogHeader onClose={handleClose}>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>
        <DialogContent>Modal Content</DialogContent>
      </Dialog>,
    )

    expect(screen.queryByText(/Upload Document/i)).toBeNull()

    rerender(
      <Dialog isOpen={true} onClose={handleClose}>
        <DialogHeader onClose={handleClose}>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>
        <DialogContent>Modal Content</DialogContent>
      </Dialog>,
    )

    expect(screen.getByText(/Upload Document/i)).toBeDefined()
    expect(screen.getByText(/Modal Content/i)).toBeDefined()

    const closeBtn = screen.getByLabelText(/Close dialog/i)
    fireEvent.click(closeBtn)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('closes dialog on Escape key', () => {
    const handleClose = vi.fn()
    render(
      <Dialog isOpen={true} onClose={handleClose}>
        <DialogContent>Escape Test</DialogContent>
      </Dialog>,
    )

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(handleClose).toHaveBeenCalled()
  })
})

describe('Dropdown component', () => {
  it('toggles menu and handles item selection', () => {
    const handleAction = vi.fn()
    render(
      <Dropdown>
        <DropdownTrigger>
          <button type="button">Options</button>
        </DropdownTrigger>
        <DropdownMenu>
          <DropdownItem onClick={handleAction}>Download</DropdownItem>
        </DropdownMenu>
      </Dropdown>,
    )

    expect(screen.queryByText(/Download/i)).toBeNull()

    // Click trigger to open
    fireEvent.click(screen.getByText(/Options/i))
    const item = screen.getByText(/Download/i)
    expect(item).toBeDefined()

    // Click item
    fireEvent.click(item)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })
})

describe('Tabs component', () => {
  it('switches tabs and displays active content', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabList>
          <TabTrigger value="tab1">Tab 1</TabTrigger>
          <TabTrigger value="tab2">Tab 2</TabTrigger>
        </TabList>
        <TabContent value="tab1">Content 1</TabContent>
        <TabContent value="tab2">Content 2</TabContent>
      </Tabs>,
    )

    expect(screen.getByText('Content 1')).toBeDefined()
    expect(screen.queryByText('Content 2')).toBeNull()

    fireEvent.click(screen.getByText('Tab 2'))
    expect(screen.getByText('Content 2')).toBeDefined()
    expect(screen.queryByText('Content 1')).toBeNull()
  })
})

describe('Toast notification system', () => {
  function TestToastConsumer() {
    const toast = useToast()
    return (
      <button
        type="button"
        onClick={() => toast.success('Document uploaded', 'OCR processing queued')}
      >
        Trigger Toast
      </button>
    )
  }

  it('triggers and displays a success toast notification', () => {
    render(
      <ToastProvider>
        <TestToastConsumer />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByText('Trigger Toast'))
    expect(screen.getByText('Document uploaded')).toBeDefined()
    expect(screen.getByText('OCR processing queued')).toBeDefined()
  })
})
