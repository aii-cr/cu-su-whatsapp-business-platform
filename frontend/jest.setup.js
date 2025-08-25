// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock performance API for tests
global.performance = {
  now: jest.fn(() => Date.now()),
}

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
} 