import { NextRequest, NextResponse } from "next/server";

/**
 * Error reporting endpoint for client-side errors caught by ErrorBoundary.
 *
 * Errors are forwarded to Sentry if SENTRY_DSN / NEXT_PUBLIC_SENTRY_DSN is configured.
 * If no DSN is set the error is logged to the server console for local development.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    if (!body.error) {
      return NextResponse.json(
        { success: false, message: "Missing error field" },
        { status: 400 }
      );
    }

    const error = new Error(body.error);
    error.stack = body.stack;

    // Forward to Sentry if DSN is configured
    const sentryDsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (sentryDsn) {
      try {
        const { captureException } = await import("@sentry/nextjs");
        captureException(error, {
          contexts: {
            react: { componentStack: body.componentStack },
          },
          extra: {
            url: body.url,
            timestamp: body.timestamp,
            userAgent: body.userAgent,
          },
          tags: { source: "error-boundary" },
        });
      } catch {
        // Sentry import/build failed — fall through to console log
        console.error("Client error (Sentry unavailable):", {
          error: body.error,
          stack: body.stack,
          componentStack: body.componentStack,
          timestamp: body.timestamp,
          userAgent: body.userAgent,
          url: body.url,
        });
      }
    } else {
      // No DSN — log locally (development)
      console.error("Client error reported:", {
        error: body.error,
        stack: body.stack,
        componentStack: body.componentStack,
        timestamp: body.timestamp,
        userAgent: body.userAgent,
        url: body.url,
      });
    }

    return NextResponse.json({ success: true, message: "Error reported" });
  } catch (error) {
    console.error("Failed to process error report:", error);
    return NextResponse.json(
      { success: false, message: "Failed to process error report" },
      { status: 500 }
    );
  }
}
