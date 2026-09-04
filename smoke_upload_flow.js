// Test upload presign endpoint + integration
const http = require("http");
const fs = require("fs");

function req(method, url, body, headers = {}) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const opts = {
      method,
      hostname: u.hostname,
      port: u.port,
      path: u.pathname + u.search,
      headers: { Accept: "application/json", ...headers },
    };
    if (body) {
      opts.headers["Content-Type"] = "application/json";
      opts.headers["Content-Length"] = Buffer.byteLength(body);
    }
    const r = http.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () =>
        resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf8") }),
      );
    });
    r.on("error", (e) => resolve({ status: 0, body: e.message }));
    if (body) r.write(body);
    r.end();
  });
}

async function main() {
  console.log("UPLOAD + WORKFLOW FLOW");
  console.log("=".repeat(70));
  let pass = 0, fail = 0;

  // 1. Create project
  const title = `UploadTest-${Date.now()}`;
  let r = await req(
    "POST",
    "http://localhost:8000/projects",
    JSON.stringify({
      title,
      source_language: "zh",
      target_language: "vi",
      quality_mode: "fast",
      language_profile: "zh-vi-fast",
    }),
  );
  const pid = JSON.parse(r.body).id;
  console.log(`${r.status === 201 ? "✓" : "✗"} POST /projects -> ${pid}`);
  r.status === 201 ? pass++ : fail++;

  // 2. Presign
  r = await req(
    "POST",
    `http://localhost:8000/projects/${pid}/assets:presign`,
    JSON.stringify({
      filename: "test.mp4",
      mime: "video/mp4",
      size: 1024000,
    }),
  );
  const ok2 = r.status === 200 || r.status === 201;
  console.log(`${ok2 ? "✓" : "✗"} POST /projects/{id}/assets:presign -> ${r.status} ${r.body.slice(0, 100)}`);
  ok2 ? pass++ : fail++;

  // 3. Trigger workflow
  r = await req(
    "POST",
    `http://localhost:8000/projects/${pid}/workflows`,
    JSON.stringify({ quality_mode: "fast" }),
  );
  const ok3 = r.status === 200 || r.status === 201;
  let workflowId;
  try {
    workflowId = JSON.parse(r.body).workflow_id;
  } catch {}
  console.log(`${ok3 ? "✓" : "✗"} POST /projects/{id}/workflows -> ${r.status} workflow_id=${workflowId}`);
  ok3 ? pass++ : fail++;

  // 4. Get workflow
  if (workflowId) {
    r = await req("GET", `http://localhost:8000/projects/${pid}/workflows/${workflowId}`);
    const ok = r.status === 200;
    console.log(`${ok ? "✓" : "✗"} GET /projects/{id}/workflows/{wid} -> ${r.status}`);
    ok ? pass++ : fail++;
  }

  // 5. Get workflow steps
  if (workflowId) {
    r = await req("GET", `http://localhost:8000/projects/${pid}/workflows/${workflowId}/steps`);
    const ok = r.status === 200;
    console.log(`${ok ? "✓" : "✗"} GET .../steps -> ${r.status} body=${r.body.slice(0, 100)}`);
    ok ? pass++ : fail++;
  }

  // 6. SSE stream
  r = await new Promise((resolve) => {
    const u = new URL(`http://localhost:8000/workflows/${workflowId || "x"}/events`);
    const s = http.get(
      { hostname: u.hostname, port: u.port, path: u.pathname, headers: { Accept: "text/event-stream" } },
      (res) => {
        let data = "";
        res.on("data", (c) => {
          data += c.toString();
          if (data.length > 50) {
            res.destroy();
            resolve({ status: res.statusCode, body: data });
          }
        });
        setTimeout(() => {
          res.destroy();
          resolve({ status: res.statusCode, body: data || "(empty)" });
        }, 3000);
      },
    );
    s.on("error", (e) => resolve({ status: 0, body: e.message }));
  });
  console.log(`${r.status === 200 ? "✓" : "✗"} GET /workflows/{wid}/events -> ${r.status} first bytes: ${r.body.slice(0, 60).replace(/\s+/g, " ")}`);
  r.status === 200 ? pass++ : fail++;

  // 7. Cancel workflow
  if (workflowId) {
    r = await req("POST", `http://localhost:8000/workflows/${workflowId}/cancel`, "{}");
    const ok = r.status >= 200 && r.status < 300;
    console.log(`${ok ? "✓" : "✗"} POST /workflows/{wid}/cancel -> ${r.status}`);
    ok ? pass++ : fail++;
  }

  // 8. Delete project (cleanup)
  r = await req("DELETE", `http://localhost:8000/projects/${pid}`);
  console.log(`${r.status === 204 ? "✓" : "✗"} DELETE /projects/{id} -> ${r.status}`);
  r.status === 204 ? pass++ : fail++;

  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  process.exit(fail > 0 ? 1 : 0);
}
main();
