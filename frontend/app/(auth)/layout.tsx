/**
 * Layout for authentication pages.
 * Simple layout without navigation for login/register pages.
 */

import { ThemeProvider } from '@/components/theme/ThemeProvider';
import { ToastContainer } from '@/components/ui/Toast';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background">
        {children}
      </div>
      <ToastContainer />
    </ThemeProvider>
  );
}