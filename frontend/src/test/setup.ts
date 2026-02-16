import '@testing-library/jest-dom'

// Mock scrollIntoView for tests
Element.prototype.scrollIntoView = () => {};

// Mock ResizeObserver
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = ResizeObserver;
