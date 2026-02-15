import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders Moon AI title', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /Moon AI/i })).toBeInTheDocument()
  })

  it('renders connection status component', () => {
    render(<App />)
    expect(screen.getByText(/Backend Connected|Connecting|Disconnected/i)).toBeInTheDocument()
  })
})
