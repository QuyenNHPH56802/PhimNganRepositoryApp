"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary to catch unhandled errors and prevent white screen crashes.
 * 
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * 
 * Or with custom fallback:
 * <ErrorBoundary fallback={(error, reset) => <CustomErrorUI error={error} onReset={reset} />}>
 *   <YourComponent />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // Send error to backend reporting endpoint (if available)
    try {
      fetch("/api/error-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          error: error.toString(),
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      }).catch((reportError) => {
        console.error("Failed to report error:", reportError);
      });
    } catch (reportError) {
      console.error("Error reporting failed:", reportError);
    }
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }

      // Default fallback UI
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            padding: "2rem",
            background: "#0B0E14",
            color: "#F8FAFC",
            fontFamily: "system-ui, -apple-system, sans-serif",
          }}
        >
          <div
            style={{
              maxWidth: "600px",
              background: "#1E293B",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "2rem",
            }}
          >
            <h1
              style={{
                fontSize: "24px",
                fontWeight: "600",
                marginBottom: "1rem",
                color: "#F87171",
              }}
            >
              ⚠️ Đã xảy ra lỗi
            </h1>
            <p style={{ fontSize: "14px", color: "#CBD5E1", marginBottom: "1.5rem" }}>
              Ứng dụng gặp lỗi không mong muốn. Bạn có thể thử tải lại trang hoặc liên hệ hỗ trợ nếu lỗi vẫn tiếp diễn.
            </p>

            <details
              style={{
                background: "#0F172A",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "1rem",
                marginBottom: "1.5rem",
                fontSize: "12px",
                fontFamily: "monospace",
                color: "#94A3B8",
                cursor: "pointer",
              }}
            >
              <summary style={{ marginBottom: "0.5rem", fontWeight: "600" }}>
                Chi tiết lỗi (dành cho developer)
              </summary>
              <pre
                style={{
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  margin: 0,
                  fontSize: "11px",
                }}
              >
                {this.state.error.toString()}
                {"\n\n"}
                {this.state.error.stack}
              </pre>
            </details>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <button
                onClick={this.reset}
                style={{
                  padding: "0.5rem 1rem",
                  background: "#3B82F6",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "background 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#2563EB")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#3B82F6")}
              >
                🔄 Thử lại
              </button>
              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: "0.5rem 1rem",
                  background: "#475569",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "background 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#334155")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#475569")}
              >
                🔁 Tải lại trang
              </button>
              <button
                onClick={() => (window.location.href = "/")}
                style={{
                  padding: "0.5rem 1rem",
                  background: "#475569",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: "pointer",
                  transition: "background 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#334155")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#475569")}
              >
                🏠 Về trang chủ
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
