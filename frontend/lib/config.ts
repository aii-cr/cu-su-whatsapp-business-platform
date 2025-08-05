/**
 * Centralized configuration system supporting multiple environments.
 * Handles API endpoints and WebSocket URLs based on current environment.
 */

export interface AppConfig {
  baseUrl: string;
  apiPrefix: string;
  wsUrl: string;
}

export const config: Record<string, AppConfig> = {
  development: {
    baseUrl: 'http://localhost:8000',
    apiPrefix: '/api/v1',
    wsUrl: 'ws://localhost:8000/api/v1/ws'
  },
  staging: {
    baseUrl: process.env.NEXT_PUBLIC_STAGING_BASE_URL || 'https://staging-api.yourdomain.com',
    apiPrefix: '/api/v1',
    wsUrl: process.env.NEXT_PUBLIC_STAGING_WS_URL || 'wss://staging-api.yourdomain.com/api/v1/ws'
  },
  production: {
    baseUrl: process.env.NEXT_PUBLIC_PRODUCTION_BASE_URL || 'https://api.yourdomain.com',
    apiPrefix: '/api/v1',
    wsUrl: process.env.NEXT_PUBLIC_PRODUCTION_WS_URL || 'wss://api.yourdomain.com/api/v1/ws'
  }
};

/**
 * Get the current environment configuration
 */
export const getCurrentConfig = (): AppConfig => {
  const env = process.env.NODE_ENV || 'development';
  
  // Use environment-specific overrides if available
  if (env === 'development') {
    return {
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || config.development.baseUrl,
      apiPrefix: process.env.NEXT_PUBLIC_API_PREFIX || config.development.apiPrefix,
      wsUrl: process.env.NEXT_PUBLIC_WS_URL || config.development.wsUrl
    };
  }
  
  return config[env as keyof typeof config] || config.development;
};

/**
 * Build API URL for a specific endpoint
 */
export const getApiUrl = (endpoint: string): string => {
  const currentConfig = getCurrentConfig();
  
  // If no endpoint provided, return base URL + API prefix
  if (!endpoint) {
    return `${currentConfig.baseUrl}${currentConfig.apiPrefix}`;
  }
  
  // Clean the endpoint - remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  return `${currentConfig.baseUrl}${currentConfig.apiPrefix}/${cleanEndpoint}`;
};

/**
 * Get WebSocket URL
 */
export const getWsUrl = (): string => {
  const currentConfig = getCurrentConfig();
  return currentConfig.wsUrl;
};

/**
 * Get base URL for the current environment
 */
export const getBaseUrl = (): string => {
  const currentConfig = getCurrentConfig();
  return currentConfig.baseUrl;
};