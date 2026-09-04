/**
 * Sentry client-side configuration.
 *
 * Instrument the browser client for error tracking and performance monitoring.
 *
 * To enable:
 * 1. npm install @sentry/nextjs
 * 2. Set SENTRY_DSN in your .env.local
 * 3. Remove "disable": true from package.json's sentryConfig
 */
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Only send in production (or when DSN is set)
  enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Capture errors from React components
  replaysOnErrorSampleRate: 1.0,

  // Session replay for debugging user sessions
  replaysSessionSampleRate: 0.05,

  // Environment tag on every event
  environment: process.env.NODE_ENV,

  // Blur any PII fields automatically
  beforeSend(event) {
    // Remove potential PII from request bodies / query strings
    if (event.request?.data) {
      const data = event.request.data as Record<string, unknown>;
      delete data.password;
      delete data.token;
      delete data.authorization;
      event.request.data = data;
    }
    return event;
  },
});
