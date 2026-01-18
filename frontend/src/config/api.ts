/**
 * API Configuration
 * Centralized configuration for API endpoints and base URLs
 */

// Base API URL with environment variable fallbacks
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                           (import.meta.env.DEV ? 'http://localhost:8000' : '/api')

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  
  // Business endpoints
  SCHOOLS: '/schools',
  STUDENTS: '/students',
  INVOICES: '/invoices',
  PAYMENTS: '/payments',
  ACCOUNT_STATEMENTS: '/account-statements',
  
  // Health check
  HEALTH: '/health',
  ROOT: '/'
} as const

// Helper function to build full API URLs
export function buildApiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`
}

// Export for easy use in components
export default {
  API_BASE_URL,
  API_ENDPOINTS,
  buildApiUrl
}
