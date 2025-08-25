'use client';

/**
 * Combined providers for the application.
 * Includes theme provider, notification system, and query client for data fetching.
 */

import { ThemeProvider } from '@/components/theme/ThemeProvider';
import { ToastContainer } from '@/components/feedback/Toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: (failureCount, error: unknown) => {
              if (error && typeof error === 'object' && 'statusCode' in error) {
                const statusCode = (error as { statusCode: number }).statusCode;
                if (statusCode === 401 || statusCode === 403) {
                  return false;
                }
              }
              return failureCount < 3;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
        <ToastContainer />
        <ReactQueryDevtools initialIsOpen={false} />
      </ThemeProvider>
    </QueryClientProvider>
  );
}