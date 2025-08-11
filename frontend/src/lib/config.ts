import { env } from '@/lib/env';

/**
 * Centralized configuration system supporting multiple environments.
 * Handles API endpoints and WebSocket URLs based on current environment.
 */

export interface AppConfig {
  baseUrl: string;
  apiPrefix: string;
  wsUrl: string;
}

const defaults: Record<string, AppConfig> = {
  development: {
    baseUrl: 'http://localhost:8000',
    apiPrefix: '/api/v1',
    wsUrl: 'ws://localhost:8000/api/v1/ws',
  },
  test: {
    baseUrl: 'http://localhost:8000',
    apiPrefix: '/api/v1',
    wsUrl: 'ws://localhost:8000/api/v1/ws',
  },
  production: {
    baseUrl: 'https://api.yourdomain.com',
    apiPrefix: '/api/v1',
    wsUrl: 'wss://api.yourdomain.com/api/v1/ws',
  },
};

/**
 * Get the current environment configuration
 */
export const getCurrentConfig = (): AppConfig => {
  const mode = env.NODE_ENV || 'development';
  const base = defaults[mode] || defaults.development;
  return {
    baseUrl: env.NEXT_PUBLIC_API_BASE_URL || base.baseUrl,
    apiPrefix: env.NEXT_PUBLIC_API_PREFIX || base.apiPrefix,
    wsUrl: env.NEXT_PUBLIC_WS_URL || base.wsUrl,
  };
};

/**
 * Build API URL for a specific endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  const currentConfig = getCurrentConfig();
  if (!endpoint) return `${currentConfig.baseUrl}${currentConfig.apiPrefix}`;
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  return `${currentConfig.baseUrl}${currentConfig.apiPrefix}/${cleanEndpoint}`;
};

/**
 * Get WebSocket URL
 */
export const getWsUrl = (): string => getCurrentConfig().wsUrl;

/**
 * Get base URL for the current environment
 */
export const getBaseUrl = (): string => getCurrentConfig().baseUrl;