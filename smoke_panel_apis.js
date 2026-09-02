// Test panel-data endpoints
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
        resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf8") }),
      );
    });
    r.on("error", (e) => resolve({ status: 0, body: e.message }));
    if (body) r.write(body);
    r.end();
  });
}

async function main() {
  console.log("PANEL ENDPOINT PROBE");
  console.log("=".repeat(70));
  // Pick the first existing project to avoid creating one
  const r = await req("GET", "http://localhost:8000/projects");
  const data = JSON.parse(r.body);
  const pid = data.items[0].id;
  console.log(`Using project: ${pid} (${data.items[0].title})`);
  console.log("-".repeat(70));

  const endpoints = [
    ["asset-url", `GET`, `/projects/${pid}/asset-url`],
    ["transcript", `GET`, `/projects/${pid}/transcript`],
    ["translation", `GET`, `/projects/${pid}/translation`],
    ["speakers", `GET`, `/projects/${pid}/speakers`],
    ["voices", `GET`, `/projects/${pid}/voices`],
    ["subtitles", `GET`, `/projects/${pid}/subtitles`],
    ["audio", `GET`, `/projects/${pid}/audio`],
    ["provider-configs", `GET`, `/projects/${pid}/provider-configs`],
    ["quality-mode", `GET`, `/projects/${pid}/quality-mode`],
  ];

  let pass = 0,
    fail = 0;
  for (const [label, method, path] of endpoints) {
    const r = await req(method, `http://localhost:8000${path}`);
    const ok = r.status >= 200 && r.status < 300;
    const excerpt = r.body.slice(0, 80).replace(/\s+/g, " ");
    console.log(
      `${ok ? "✓" : "✗"} ${label.padEnd(18)} ${method.padEnd(4)} ${r.status}  ${excerpt}`,
    );
    ok ? pass++ : fail++;
  }
  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  process.exit(fail > 0 ? 1 : 0);
}
main();
