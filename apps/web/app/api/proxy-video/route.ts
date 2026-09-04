import { NextRequest, NextResponse } from "next/server";
import { hasToken, loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";
import { readFile, stat } from "fs/promises";
import { existsSync } from "fs";
import { join, normalize, relative, resolve } from "path";

// Only allow /local-assets/ paths for security.
const ALLOWED_PREFIX = "/local-assets/";

// Storage root — must match the backend's local_storage_root.
function getStorageRoot(): string {
  if (process.env.STORAGE_ROOT) return process.env.STORAGE_ROOT;
  if (process.env.DOCKER_CONTAINER === "true") return "/app/.local-storage";
  return join(process.cwd(), ".local-storage");
}

const CONTENT_TYPES: Record<string, string> = {
  mp4: "video/mp4",
  webm: "video/webm",
  mov: "video/quicktime",
  mkv: "video/x-matroska",
  m4a: "audio/mp4",
  mp3: "audio/mpeg",
  aac: "audio/aac",
  wav: "audio/wav",
  flac: "audio/flac",
  ogg: "audio/ogg",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  srt: "text/plain; charset=utf-8",
  vtt: "text/vtt; charset=utf-8",
};

function contentTypeFor(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return CONTENT_TYPES[ext] ?? "application/octet-stream";
}

function safeResolve(storageRoot: string, storageKey: string): string | null {
  // Normalize both sides so `..` segments are collapsed, then verify the
  // candidate is still under the root. `relative()` returns a value that
  // starts with `..` whenever the candidate escapes the root.
  const root = resolve(storageRoot);
  const candidate = normalize(resolve(join(root, storageKey)));
  const rel = relative(root, candidate);
  // Empty `rel` means candidate === root (we still return it; the existence
  // check downstream will reject). Otherwise the rel must not begin with
  // `..` (escape) and must not be absolute.
  if (rel.startsWith("..")) return null;
  return candidate;
}

function parseRange(range: string | null, size: number): { start: number; end: number } | null {
  if (!range) return null;
  const match = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
  if (!match) return null;
  const startStr = match[1];
  const endStr = match[2];
  let start: number;
  let end: number;
  if (startStr === "" && endStr !== "") {
    // Suffix range: bytes=-N → last N bytes
    const n = Number(endStr);
    if (Number.isNaN(n) || n <= 0) return null;
    start = Math.max(0, size - n);
    end = size - 1;
  } else {
    start = startStr === "" ? 0 : Number(startStr);
    end = endStr === "" ? size - 1 : Number(endStr);
  }
  if (Number.isNaN(start) || Number.isNaN(end) || start > end || start < 0 || end >= size) {
    return null;
  }
  return { start, end };
}

async function readLocalRange(
  filePath: string,
  range: { start: number; end: number } | null,
  size: number,
): Promise<{ body: Uint8Array; contentLength: number; contentType: string }> {
  const buffer = await readFile(filePath);
  if (!range) {
    return { body: new Uint8Array(buffer), contentLength: size, contentType: contentTypeFor(filePath) };
  }
  const slice = buffer.subarray(range.start, range.end + 1);
  return {
    body: new Uint8Array(slice),
    contentLength: range.end - range.start + 1,
    contentType: contentTypeFor(filePath),
  };
}

function validatePath(rawPath: string): { storageKey: string } | { error: string } {
  if (!rawPath) return { error: "Missing path parameter" };
  if (!rawPath.startsWith(ALLOWED_PREFIX)) {
    return { error: "Invalid path — only /local-assets/* allowed" };
  }
  return { storageKey: rawPath.slice(ALLOWED_PREFIX.length) };
}

async function fetchFromBackend(
  rawPath: string,
  rawRangeHeader: string | null,
): Promise<Response | null> {
  const backendUrl = `${API_BASE_URL}${rawPath}`;
  const headers: Record<string, string> = { Accept: "*/*" };
  if (hasToken()) {
    const token = loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  if (rawRangeHeader) headers.Range = rawRangeHeader;

  try {
    return await fetch(backendUrl, { headers });
  } catch {
    return null;
  }
}

function badRequest(message: string): NextResponse {
  return NextResponse.json({ error: message }, { status: 400 });
}

function buildFileResponse(
  body: Uint8Array,
  contentType: string,
  contentLength: number,
  range: { start: number; end: number } | null,
  size: number,
): NextResponse {
  const headers: Record<string, string> = {
    "Content-Type": contentType,
    "Content-Length": String(contentLength),
    "Accept-Ranges": "bytes",
    "Cache-Control": "public, max-age=3600",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Expose-Headers": "Content-Type, Content-Length, Accept-Ranges, Content-Range",
  };
  if (range) {
    headers["Content-Range"] = `bytes ${range.start}-${range.end}/${size}`;
  }
  return new NextResponse(body, {
    status: range ? 206 : 200,
    headers,
  });
}

async function handleRequest(request: NextRequest, method: "GET" | "HEAD"): Promise<NextResponse> {
  const rawPath = request.nextUrl.searchParams.get("path");
  const validated = validatePath(rawPath ?? "");
  if ("error" in validated) return badRequest(validated.error);

  const storageRoot = getStorageRoot();
  const filePath = safeResolve(storageRoot, validated.storageKey);
  if (!filePath) return badRequest("Invalid path");

  // Try local filesystem first.
  if (existsSync(filePath)) {
    try {
      const stats = await stat(filePath);
      const size = stats.size;
      const effectiveRange = parseRange(request.headers.get("range"), size);
      if (method === "HEAD") {
        return new NextResponse(null, {
          status: 200,
          headers: {
            "Content-Type": contentTypeFor(filePath),
            "Content-Length": String(size),
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
          },
        });
      }
      const { body, contentLength, contentType } = await readLocalRange(filePath, effectiveRange, size);
      return buildFileResponse(body, contentType, contentLength, effectiveRange, size);
    } catch (err) {
      console.error("[proxy-video] Failed to read file:", err);
      return NextResponse.json({ error: "Failed to read video file" }, { status: 500 });
    }
  }

  // Fallback: proxy to backend (forward raw Range header verbatim so the
  // backend can validate against its own size).
  const backendResponse = await fetchFromBackend(rawPath!, request.headers.get("range"));
  if (!backendResponse) {
    return NextResponse.json(
      { error: "Video not found and backend is unavailable" },
      { status: 502 },
    );
  }
  if (!backendResponse.ok) {
    return NextResponse.json(
      { error: `Backend returned ${backendResponse.status}: ${backendResponse.statusText}` },
      { status: backendResponse.status },
    );
  }

  const contentType = backendResponse.headers.get("content-type") || "video/mp4";
  const body = backendResponse.body;

  // If the upstream returned no body (rare), error out instead of buffering
  // a potentially huge file into memory.
  if (!body) {
    return NextResponse.json({ error: "Backend returned empty body" }, { status: 502 });
  }

  if (method === "HEAD") {
    return new NextResponse(null, {
      status: backendResponse.status,
      headers: {
        "Content-Type": contentType,
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }

  // Forward the upstream ReadableStream and headers (rewriting CORS).
  const headers = new Headers();
  headers.set("Content-Type", contentType);
  headers.set("Accept-Ranges", "bytes");
  headers.set("Cache-Control", "public, max-age=3600");
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("Access-Control-Expose-Headers", "Content-Type, Content-Length, Accept-Ranges, Content-Range");
  const contentRange = backendResponse.headers.get("content-range");
  if (contentRange) headers.set("Content-Range", contentRange);
  const contentLength = backendResponse.headers.get("content-length");
  if (contentLength) headers.set("Content-Length", contentLength);

  // Cast to NextResponse so Next's route handler type accepts the streamed
  // body — the runtime contract is identical to a global Response.
  return new Response(body, { status: backendResponse.status, headers }) as unknown as NextResponse;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  return handleRequest(request, "GET");
}

export async function HEAD(request: NextRequest): Promise<NextResponse> {
  return handleRequest(request, "HEAD");
}