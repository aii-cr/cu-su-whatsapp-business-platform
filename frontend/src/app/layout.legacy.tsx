/**
 * Root layout for the ADN Contact Center frontend.
 * Provides global styling, theme support, and authentication context.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/app/providers';
import { AuthWrapper } from '@/features/auth/components/AuthWrapper';
import { getPageTitle, getMetaDescription } from '@/lib/branding';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: getPageTitle(),
  description: getMetaDescription(),
  keywords: ['Contact Center', 'Customer Support', 'Messaging', 'WhatsApp', 'Business'],
  authors: [{ name: 'American Data Networks' }],
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <AuthWrapper>
            {children}
          </AuthWrapper>
        </Providers>
      </body>
    </html>
  );
}