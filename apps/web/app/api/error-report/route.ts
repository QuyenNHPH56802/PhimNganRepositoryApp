import { NextRequest, NextResponse } from "next/server";

/**
 * Error reporting endpoint for client-side errors caught by ErrorBoundary.
 * 
 * Logs errors to console (in production, this should send to a monitoring service
 * like Sentry, Datadog, or a custom error tracking system).
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

    // Log to console (in production, send to monitoring service)
    console.error("Client error reported:", {
      error: body.error,
      stack: body.stack,
      componentStack: body.componentStack,
      timestamp: body.timestamp,
      userAgent: body.userAgent,
      url: body.url,
    });

    // TODO: Send to monitoring service
    // Example with Sentry:
    // Sentry.captureException(new Error(body.error), {
    //   contexts: {
    //     react: { componentStack: body.componentStack },
    //   },
    //   tags: {
    //     source: 'error-boundary',
    //   },
    // });

    return NextResponse.json({ success: true, message: "Error reported" });
  } catch (error) {
    console.error("Failed to process error report:", error);
    return NextResponse.json(
      { success: false, message: "Failed to process error report" },
      { status: 500 }
    );
  }
}
