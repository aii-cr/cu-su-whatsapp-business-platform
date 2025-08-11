'use client';

import Image from 'next/image';
import { getLogoPath, getLogoAlt, getLogoClassName } from '@/lib/branding';

interface BrandLogoProps {
  className?: string;
  width?: number;
  height?: number;
  priority?: boolean;
}

export function BrandLogo({ 
  className = '', 
  width = 120, 
  height = 40, 
  priority = false 
}: BrandLogoProps) {
  return (
    <div className={`flex items-center ${className}`}>
      <Image
        src={getLogoPath()}
        alt={getLogoAlt()}
        width={width}
        height={height}
        priority={priority}
        className={getLogoClassName('h-auto w-auto')}
      />
    </div>
  );
}

// Compact version for headers
export function BrandLogoCompact({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center ${className}`}>
      <Image
        src={getLogoPath()}
        alt={getLogoAlt()}
        width={80}
        height={32}
        className={getLogoClassName('h-8 w-auto')}
      />
    </div>
  );
}

// Large version for login pages
export function BrandLogoLarge({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <Image
        src={getLogoPath()}
        alt={getLogoAlt()}
        width={200}
        height={80}
        priority
        className={getLogoClassName('h-16 w-auto')}
      />
    </div>
  );
} 