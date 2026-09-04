/**
 * Sentry server-side configuration for the Next.js API routes.
 *
 * Instruments server-side errors, including unhandled exceptions in route handlers.
 */
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN,

  enabled: !!process.env.SENTRY_DSN,

  // Profile async server-side transactions
  tracesSampler: (samplingContext) => {
    // Sample more heavily in development
    if (process.env.NODE_ENV === "development") return 0.5;
    // Default: capture 10% of server-side transactions
    return 0.1;
  },

  environment: process.env.NODE_ENV,

  // Don't send server errors in development
  enabled: !!process.env.SENTRY_DSN && process.env.NODE_ENV !== "development",
});
