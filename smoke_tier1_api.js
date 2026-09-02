// Test API integration
const http = require("http");

function req(method, url, body) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const opts = {
      method,
      hostname: u.hostname,
      port: u.port,
      path: u.pathname + u.search,
      headers: { Accept: "application/json" },
    };
    if (body) {
      opts.headers["Content-Type"] = "application/json";
      opts.headers["Content-Length"] = Buffer.byteLength(body);
    }
    const r = http.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () =>
        resolve({
          status: res.statusCode,
          body: Buffer.concat(chunks).toString("utf8"),
        }),
      );
    });
    r.on("error", (e) => resolve({ status: 0, body: e.message }));
    if (body) r.write(body);
    r.end();
  });
}

async function main() {
  console.log("API INTEGRATION TEST");
  console.log("=".repeat(70));
  let pass = 0,
    fail = 0;

  // 1. List projects
  let r = await req("GET", "http://localhost:8000/projects");
  let ok = r.status === 200;
  let count = 0;
  try {
    count = JSON.parse(r.body).total ?? 0;
  } catch {}
  console.log(`${ok ? "✓" : "✗"} GET /projects              ${r.status}  total=${count}`);
  ok ? pass++ : fail++;

  // 2. Create project
  const title = `SmokeTest-${Date.now()}`;
  r = await req(
    "POST",
    "http://localhost:8000/projects",
    JSON.stringify({
      title,
      source_language: "zh",
      target_language: "vi",
      quality_mode: "balanced",
      language_profile: "zh-vi-balanced",
    }),
  );
  ok = r.status === 200 || r.status === 201;
  let projectId;
  try {
    projectId = JSON.parse(r.body).id;
  } catch {}
  console.log(`${ok ? "✓" : "✗"} POST /projects             ${r.status}  id=${projectId}`);
  ok ? pass++ : fail++;

  // 3. Get that project
  if (projectId) {
    r = await req("GET", `http://localhost:8000/projects/${projectId}`);
    ok = r.status === 200;
    let title2;
    try {
      title2 = JSON.parse(r.body).title;
    } catch {}
    console.log(
      `${ok ? "✓" : "✗"} GET /projects/{id}         ${r.status}  title="${title2}"`,
    );
    ok ? pass++ : fail++;
  }

  // 4. Workflow steps empty for fresh project
  if (projectId) {
    r = await req(
      "GET",
      `http://localhost:8000/projects/${projectId}/workflows`,
    );
    ok = r.status === 200;
    console.log(
      `${ok ? "✓" : "✗"} GET /projects/{id}/workflows ${r.status}  empty=${(r.body || "").includes("[]")}`,
    );
    ok ? pass++ : fail++;
  }

  // 5. Provider configs (empty)
  if (projectId) {
    r = await req(
      "GET",
      `http://localhost:8000/projects/${projectId}/provider-configs`,
    );
    ok = r.status === 200;
    console.log(
      `${ok ? "✓" : "✗"} GET provider-configs        ${r.status}  body=${r.body.slice(0, 80)}`,
    );
    ok ? pass++ : fail++;
  }

  // 6. Transcript (empty)
  if (projectId) {
    r = await req("GET", `http://localhost:8000/projects/${projectId}/transcript`);
    ok = r.status === 200;
    console.log(
      `${ok ? "✓" : "✗"} GET transcript              ${r.status}  body=${r.body.slice(0, 80)}`,
    );
    ok ? pass++ : fail++;
  }

  // 7. Voices (empty)
  if (projectId) {
    r = await req("GET", `http://localhost:8000/projects/${projectId}/voices`);
    ok = r.status === 200;
    console.log(
      `${ok ? "✓" : "✗"} GET voices                  ${r.status}  body=${r.body.slice(0, 80)}`,
    );
    ok ? pass++ : fail++;
  }

  // 8. Admin voice-profiles via web proxy
  r = await req("GET", "http://localhost:3000/api/admin/voice-profiles");
  ok = r.status === 200 || r.status === 404;
  console.log(
    `${ok ? "✓" : "✗"} GET /api/admin/voice-profiles ${r.status}  body=${r.body.slice(0, 100)}`,
  );
  ok ? pass++ : fail++;

  // 9. Admin datasets via web proxy
  r = await req("GET", "http://localhost:3000/api/admin/datasets");
  ok = r.status === 200 || r.status === 404;
  console.log(
    `${ok ? "✓" : "✗"} GET /api/admin/datasets     ${r.status}  body=${r.body.slice(0, 100)}`,
    );
  ok ? pass++ : fail++;

  // 10. Delete the project (cleanup)
  if (projectId) {
    r = await req("DELETE", `http://localhost:8000/projects/${projectId}`);
    ok = r.status === 204 || r.status === 200;
    console.log(`${ok ? "✓" : "✗"} DELETE /projects/{id}      ${r.status}`);
    ok ? pass++ : fail++;
  }

  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  process.exit(fail > 0 ? 1 : 0);
}
main();
