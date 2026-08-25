import React from 'react'
import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { AuthLayout } from '@/components/layout/AuthLayout'
import {
  AccountPage,
  ChatPage,
  CollectionsPage,
  DashboardPage,
  DocumentsPage,
  LoginPage,
  RegisterPage,
} from '@/pages'

const createTestRouter = (initialEntry = '/dashboard') => {
  return createMemoryRouter(
    [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
        ],
      },
      {
        element: <AppShell />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/documents', element: <DocumentsPage /> },
          { path: '/collections', element: <CollectionsPage /> },
          { path: '/chat', element: <ChatPage /> },
          { path: '/account', element: <AccountPage /> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  )
}

const renderWithProviders = (router: ReturnType<typeof createTestRouter>) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('AppShell and Navigation Routing', () => {
  it('renders AppShell with navigation links on dashboard route', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    expect(screen.getByRole('heading', { name: /^Dashboard$/i })).toBeDefined()
    expect(screen.getAllByText('Documents').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Collections').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Chat & RAG').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Account').length).toBeGreaterThan(0)
  })

  it('navigates to documents route when clicking Documents nav link', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const docLinks = screen.getAllByRole('link', { name: /Documents/i })
    fireEvent.click(docLinks[0])

    expect(screen.getByRole('heading', { name: /^Documents$/i })).toBeDefined()
    expect(screen.getByText(/Upload, inspect, OCR process/i)).toBeDefined()
  })

  it('navigates to chat route when clicking Chat nav link', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const chatLinks = screen.getAllByRole('link', { name: /Chat & RAG/i })
    fireEvent.click(chatLinks[0])

    expect(screen.getByRole('heading', { name: /Chat & Intelligence/i })).toBeDefined()
  })

  it('opens and closes mobile sidebar drawer', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const menuButton = screen.getByRole('button', { name: /Open mobile menu/i })
    fireEvent.click(menuButton)

    const closeButton = screen.getByRole('button', { name: /Close navigation/i })
    expect(closeButton).toBeDefined()

    fireEvent.click(closeButton)
    expect(screen.queryByRole('button', { name: /Close navigation/i })).toBeNull()
  })

  it('closes mobile drawer with Escape key', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const menuButton = screen.getByRole('button', { name: /Open mobile menu/i })
    fireEvent.click(menuButton)

    expect(screen.getByRole('button', { name: /Close navigation/i })).toBeDefined()

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('button', { name: /Close navigation/i })).toBeNull()
  })

  it('toggles desktop sidebar collapse and expand', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const collapseButton = screen.getByRole('button', { name: /Collapse sidebar/i })
    fireEvent.click(collapseButton)

    const expandButton = screen.getByRole('button', { name: /Expand sidebar/i })
    expect(expandButton).toBeDefined()

    fireEvent.click(expandButton)
    expect(screen.getByRole('button', { name: /Collapse sidebar/i })).toBeDefined()
  })

  it('toggles light and dark themes using ThemeToggle', () => {
    const router = createTestRouter('/dashboard')
    renderWithProviders(router)

    const darkButton = screen.getByRole('button', { name: /Dark/i })
    fireEvent.click(darkButton)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    const lightButton = screen.getByRole('button', { name: /Light/i })
    fireEvent.click(lightButton)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})

describe('Public Authentication Pages', () => {
  it('renders login page inside AuthLayout', () => {
    const router = createTestRouter('/login')
    renderWithProviders(router)

    expect(screen.getByRole('heading', { name: /Sign in to your account/i })).toBeDefined()
    expect(screen.getByPlaceholderText('name@company.com')).toBeDefined()
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeDefined()
  })

  it('renders register page inside AuthLayout', () => {
    const router = createTestRouter('/register')
    renderWithProviders(router)

    expect(screen.getByRole('heading', { name: /Create an account/i })).toBeDefined()
    expect(screen.getByPlaceholderText('Jane Doe')).toBeDefined()
  })
})
