import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders Moon AI title', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /Moon AI/i, level: 1 })).toBeInTheDocument()
  })

  it('renders connection status component', () => {
    render(<App />)
    // There might be multiple status indicators now (header + chat panel)
    const statusElements = screen.getAllByText(/Backend Connected|Connecting|Disconnected/i)
    expect(statusElements.length).toBeGreaterThan(0)
  })
})
