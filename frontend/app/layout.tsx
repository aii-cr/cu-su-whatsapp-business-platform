/**
 * Root layout for the WhatsApp Business Platform frontend.
 * Provides global styling, theme support, and authentication context.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers/Providers';
import { AuthWrapper } from '@/components/auth/AuthWrapper';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'WhatsApp Business Platform',
  description: 'Professional WhatsApp Business messaging platform for customer support',
  keywords: ['WhatsApp', 'Business', 'Customer Support', 'Messaging'],
  authors: [{ name: 'WhatsApp Business Platform Team' }],
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