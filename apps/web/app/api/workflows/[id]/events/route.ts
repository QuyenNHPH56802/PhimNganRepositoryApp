import { NextRequest } from "next/server";
import { hasToken, loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

const SSE_HEADERS = {
  "Content-Type": "text/event-stream",
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "X-Accel-Buffering": "no",
};

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } },
): Promise<Response> {
  const { id } = params;
  const backendUrl = `${API_BASE_URL}/workflows/${id}/events`;

  const headers: Record<string, string> = {};
  if (hasToken()) {
    const token = loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  // Forward Accept so the backend emits SSE even when its default is JSON.
  headers.Accept = "text/event-stream";

  let upstream: Response;
  try {
    upstream = await fetch(backendUrl, { headers, signal: request.signal });
  } catch (err) {
    const isAbort = err instanceof DOMException && err.name === "AbortError";
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: isAbort ? "client-disconnected" : "backend-unreachable" })}\n\n`,
      { status: isAbort ? 499 : 502, headers: SSE_HEADERS },
    );
  }

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", message: `HTTP ${upstream.status}`, status: upstream.status })}\n\n`,
      { status: upstream.status, headers: SSE_HEADERS },
    );
  }

  const reader = upstream.body.getReader();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const cleanup = () => {
        try {
          controller.close();
        } catch {
          // already closed
        }
        try {
          reader.cancel();
        } catch {
          // ignore
        }
      };

      // When the client aborts, cancel the upstream reader so the backend
      // SSE connection is released promptly.
      const onAbort = () => cleanup();
      if (request.signal.aborted) {
        cleanup();
        return;
      }
      request.signal.addEventListener("abort", onAbort, { once: true });

      try {
        while (true) {
          if (request.signal.aborted) break;
          const { value, done } = await reader.read();
          if (done) break;
          if (value) controller.enqueue(value);
        }
      } catch (err) {
        const isAbort = err instanceof DOMException && err.name === "AbortError";
        if (!isAbort) {
          const errPayload = `data: ${JSON.stringify({ type: "error", message: "stream-error" })}\n\n`;
          controller.enqueue(new TextEncoder().encode(errPayload));
        }
      } finally {
        request.signal.removeEventListener("abort", onAbort);
        cleanup();
      }
    },
  });

  return new Response(stream, { headers: SSE_HEADERS });
}