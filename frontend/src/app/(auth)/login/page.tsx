'use client';

/**
 * Login page for ADN Contact Center.
 * Handles user authentication with session-based cookies.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoginCredentials, LoginSchema } from '@/lib/auth';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { FormField } from '@/components/forms/FormField';
import { toast } from '@/components/feedback/Toast';
import { BrandLogoLarge } from '@/components/layout/BrandLogo';
import { getProductName, getCompanyName } from '@/lib/branding';
import { ApiError } from '@/lib/http';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginCredentials>({
    resolver: zodResolver(LoginSchema),
    mode: 'onBlur',
  });

  useEffect(() => {
    // Prefetch dashboard to minimize transition flash
    router.prefetch('/conversations');
    try {
      if (typeof window !== 'undefined' && sessionStorage.getItem('sessionExpired') === '1') {
        toast.info('Your session has expired. Please log in again.');
        sessionStorage.removeItem('sessionExpired');
      }
    } catch {}
  }, [router]);

  const onSubmit = async (data: LoginCredentials) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await login(data.email, data.password);
      router.replace('/conversations');
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.errorCode === 'REQUEST_TIMEOUT') {
          setErrorMessage('The request timed out while authenticating. Please try again.');
        } else if (error.errorCode === 'NETWORK_ERROR') {
          setErrorMessage('Error connecting to server. Please contact your administrator if it persists.');
        } else if (error.statusCode === 401 || error.statusCode === 403) {
          setErrorMessage('Incorrect email or password. Please try again.');
        } else {
          setErrorMessage(error.userMessage || 'We could not authenticate you at this time. Please contact your administrator.');
        }
      } else {
        setErrorMessage('We could not authenticate you at this time. Please contact your administrator.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <BrandLogoLarge />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-2xl font-bold text-primary-500">{getProductName()}</CardTitle>
            <CardDescription>Sign in to your account to manage conversations</CardDescription>
            <p className="text-xs text-muted-foreground">Powered by {getCompanyName()}</p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              label="Email Address"
              type="email"
              placeholder="Enter your email address"
              error={errors.email?.message}
              required
              autoComplete="email"
              {...register('email')}
            />

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-foreground">
                Password
                <span className="text-error ml-1">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className={`flex h-10 w-full rounded-lg border pr-10 px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
                    errors.password ? 'border-error focus-visible:ring-error bg-background' : 'border-border bg-background'
                  }`}
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-error">{errors.password.message}</p>}
            </div>

            {errorMessage && <p className="text-sm text-error">{errorMessage}</p>}

            <Button type="submit" className="w-full" loading={isLoading || isSubmitting} disabled={isLoading || isSubmitting}>
              {isLoading || isSubmitting ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">Need access? Contact your administrator to create an account.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}