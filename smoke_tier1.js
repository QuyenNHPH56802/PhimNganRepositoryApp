// Smoke test Tầng 1: Foundation
// Probe các page web xem có render 200 và có HTML hợp lệ không.
// Đồng thời probe backend qua web proxy.

const http = require("http");

const probes = [
  // [path, expectedStatus, mô tả]
  ["GET", "/", 200, "Dashboard"],
  ["GET", "/projects", 200, "Projects list"],
  ["GET", "/projects/new", 200, "New project form"],
  ["GET", "/voice", 200, "Voice library"],
  ["GET", "/settings", 200, "Settings"],
  ["GET", "/admin", 200, "Admin"],
  ["GET", "/api/healthz", 200, "Healthz proxy"],
];

const BACKEND = "http://localhost:8000";

function fetchUrl(url) {
  return new Promise((resolve) => {
    const start = Date.now();
    http
      .get(url, (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks).toString("utf8"),
            ms: Date.now() - start,
          }),
        );
      })
      .on("error", (err) =>
        resolve({ status: 0, body: "", ms: Date.now() - start, error: err.message }),
      );
  });
}

async function main() {
  console.log("=".repeat(70));
  console.log("SMOKE TEST TẦNG 1 — FOUNDATION");
  console.log("=".repeat(70));
  let pass = 0,
    fail = 0;
  const errors = [];

  for (const [method, path, expect, desc] of probes) {
    const url = path.startsWith("/api/")
      ? `http://localhost:3000${path}`
      : `http://localhost:3000${path}`;
    const r = await fetchUrl(url);
    const ok = r.status === expect;
    console.log(
      `${ok ? "✓" : "✗"} ${method} ${path.padEnd(28)} ${r.status} ${desc.padEnd(30)} (${r.ms}ms)`,
    );
    if (!ok) {
      fail++;
      errors.push({ path, status: r.status, expect, body: r.body.slice(0, 300) });
    } else {
      pass++;
    }
  }

  console.log("-".repeat(70));
  console.log(`Backend direct probe:`);
  const backendProbes = ["/healthz", "/capabilities", "/auth-debug"];
  for (const p of backendProbes) {
    const r = await fetchUrl(`${BACKEND}${p}`);
    const ok = r.status >= 200 && r.status < 400;
    console.log(
      `${ok ? "✓" : "✗"} GET ${p.padEnd(28)} ${r.status} (${r.ms}ms)`.padEnd(70),
    );
    if (ok) pass++;
    else {
      fail++;
      errors.push({ path: `backend${p}`, status: r.status, body: r.body.slice(0, 200) });
    }
  }

  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  if (errors.length) {
    console.log("Failures:");
    for (const e of errors) {
      console.log(`  ${e.path}: status=${e.status} body=${e.body.slice(0, 200)}`);
    }
  }
  process.exit(fail > 0 ? 1 : 0);
}

main();
