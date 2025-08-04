/**
 * Branding configuration for ADN Contact Center.
 * Centralized configuration for company branding and customization.
 */

export interface BrandingConfig {
  companyName: string;
  productName: string;
  logoPath: string;
  logoAlt: string;
  primaryColor: string;
  secondaryColor: string;
  contactEmail: string;
  supportPhone?: string;
  website?: string;
}

// Main branding configuration
export const brandingConfig: BrandingConfig = {
  companyName: 'American Data Networks',
  productName: 'ADN Contact Center',
  logoPath: '/images/business/logoADN2.svg',
  logoAlt: 'American Data Networks Logo',
  primaryColor: '#2563eb', // blue-600
  secondaryColor: '#1d4ed8', // blue-700
  contactEmail: 'support@americandatanetworks.com',
  supportPhone: '+1 (555) 123-4567',
  website: 'https://americandatanetworks.com',
};

// Branding utility functions
export function getCompanyName(): string {
  return brandingConfig.companyName;
}

export function getProductName(): string {
  return brandingConfig.productName;
}

export function getFullProductName(): string {
  return `${brandingConfig.productName} by ${brandingConfig.companyName}`;
}

export function getLogoPath(): string {
  return brandingConfig.logoPath;
}

export function getLogoAlt(): string {
  return brandingConfig.logoAlt;
}

// Theme-aware logo styling
export function getLogoClassName(className?: string): string {
  return `filter brightness-0 dark:brightness-100 ${className || ''}`;
}

// Page titles with branding
export function getPageTitle(pageName?: string): string {
  const baseTitle = getProductName();
  return pageName ? `${pageName} - ${baseTitle}` : baseTitle;
}

// Meta descriptions
export function getMetaDescription(pageDescription?: string): string {
  const baseDescription = 'Professional contact center platform for customer support and messaging';
  return pageDescription || baseDescription;
} 