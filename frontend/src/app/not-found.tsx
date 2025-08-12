"use client";
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function NotFound() {
  const router = useRouter();
  return (
    <main className="min-h-screen flex items-center justify-center bg-background px-6">
      <section className="mx-auto w-full max-w-xl text-center">
        <p className="text-sm font-medium text-muted-foreground">Error 404</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Page not found
        </h1>
        <p className="mt-3 text-base text-muted-foreground">
          The page you are looking for doesn&apos;t exist or has been moved.
        </p>

        <div className="mt-8 flex items-center justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
            style={{
              backgroundColor: 'rgb(var(--primary))',
              color: 'rgb(var(--primary-foreground))',
              // Tailwind tokens for ring use CSS vars via inline style fallback
            }}
          >
            Go to home
          </Link>

          <button
            type="button"
            onClick={() => router.back()}
            className="inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium text-foreground border-[rgb(var(--border))] hover:bg-[rgb(var(--surface))]"
            aria-label="Go back"
          >
            Go back
          </button>
        </div>
      </section>
    </main>
  );
}


