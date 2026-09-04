/**
 * Error message utilities.
 *
 * Centralises the translation of low-level errors (HTTP status, fetch
 * failures, ApiError detail strings) into short, user-friendly Vietnamese
 * messages so individual panels can render consistent copy.
 *
 * Usage:
 *   try { await api.foo(); }
 *   catch (err) {
 *     toast(humanizeError(err, "Không thể tạo voice"), "danger");
 *   }
 */
import { ApiError } from "@/lib/api";

/** Network failure (fetch rejected, no response). */
function isNetworkError(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  // DOMException with name "AbortError" is a user-initiated cancel.
  if (err.name === "AbortError") return false;
  const msg = (err.message || "").toLowerCase();
  return (
    msg.includes("failed to fetch") ||
    msg.includes("networkerror") ||
    msg.includes("network request failed") ||
    msg.includes("load failed") ||
    msg.includes("err_network")
  );
}

function extractDetail(err: unknown): string {
  if (err instanceof ApiError) {
    if (typeof err.detail === "string") return err.detail;
    if (err.detail && typeof err.detail === "object") {
      try {
        return JSON.stringify(err.detail);
      } catch {
        return "";
      }
    }
    return err.message || "";
  }
  if (err instanceof Error) return err.message;
  return typeof err === "string" ? err : "";
}

/**
 * Map a status code to a short Vietnamese label.
 * Returns `null` if the status code is not in the well-known set so the
 * caller can fall back to the raw detail.
 */
function statusLabel(status: number): string | null {
  switch (status) {
    case 400:
      return "Yêu cầu không hợp lệ";
    case 401:
      return "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại";
    case 403:
      return "Bạn không có quyền thực hiện thao tác này";
    case 404:
      return "Không tìm thấy dữ liệu yêu cầu, có thể đã bị xoá";
    case 408:
    case 504:
      return "Máy chủ phản hồi quá chậm, vui lòng thử lại";
    case 409:
      return "Dữ liệu đã được cập nhật bởi phiên khác, vui lòng tải lại";
    case 413:
      return "File quá lớn, vui lòng chọn file nhỏ hơn";
    case 415:
      return "Định dạng file không được hỗ trợ";
    case 422:
      return "Dữ liệu chưa hợp lệ, vui lòng kiểm tra lại";
    case 429:
      return "Bạn đã gửi quá nhiều yêu cầu, vui lòng đợi một chút";
    case 500:
    case 502:
    case 503:
      return "Máy chủ gặp sự cố, vui lòng thử lại sau";
    default:
      if (status >= 500) return "Máy chủ gặp sự cố, vui lòng thử lại sau";
      if (status >= 400) return null;
      return null;
  }
}

export interface HumanizedError {
  /** Short headline shown in toast / banner. */
  title: string;
  /** Optional longer explanation. */
  hint?: string;
  /** Optional technical detail (kept for the "Details" expandable). */
  detail?: string;
  /** Original error for logging / reporting. */
  raw: unknown;
}

const FALLBACK_GENERIC = "Đã xảy ra lỗi, vui lòng thử lại";

/**
 * Build a user-friendly error description.
 *
 * @param err          - The thrown value (Error, ApiError, anything).
 * @param fallback     - Contextual fallback action, e.g. "Không thể tạo voice".
 *                       Used when no specific message can be derived.
 */
export function humanizeError(err: unknown, fallback?: string): HumanizedError {
  // Network / fetch failure (no HTTP response at all)
  if (isNetworkError(err)) {
    return {
      title: "Không thể kết nối tới máy chủ",
      hint: "Kiểm tra kết nối mạng hoặc thử lại sau vài giây.",
      detail: extractDetail(err),
      raw: err,
    };
  }

  // ApiError carries HTTP status + server-provided detail
  if (err instanceof ApiError) {
    const label = statusLabel(err.status);
    if (label) {
      return {
        title: fallback ? `${fallback}: ${label.toLowerCase()}` : label,
        detail: extractDetail(err),
        raw: err,
      };
    }
    // Unknown status, fall through to raw detail if present
    const detail = extractDetail(err);
    if (detail && detail.length < 200) {
      return {
        title: fallback ?? FALLBACK_GENERIC,
        hint: detail,
        detail,
        raw: err,
      };
    }
  }

  // Plain Error or string
  const detail = extractDetail(err);
  if (detail && detail.length < 200) {
    return {
      title: fallback ?? FALLBACK_GENERIC,
      hint: detail,
      detail,
      raw: err,
    };
  }

  return {
    title: fallback ?? FALLBACK_GENERIC,
    detail: detail || undefined,
    raw: err,
  };
}

/**
 * Convenience helper for toast() calls. Returns a single-line string that
 * combines fallback + headline.
 */
export function humanizeErrorMessage(err: unknown, fallback?: string): string {
  return humanizeError(err, fallback).title;
}
