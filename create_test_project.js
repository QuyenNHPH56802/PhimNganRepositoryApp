const http = require("http");

function req(method, url, body) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const opts = {
      method,
      hostname: u.hostname,
      port: u.port,
      path: u.pathname,
      headers: { "Content-Type": "application/json" },
    };
    const r = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => resolve({ status: res.statusCode, body: data }));
    });
    if (body) r.write(body);
    r.end();
  });
}

(async () => {
  let r = await req(
    "POST",
    "http://localhost:8000/projects",
    JSON.stringify({ title: "Test", source_language: "en", target_language: "vi" })
  );
  console.log("Create project response:", r.body);
  const pid = JSON.parse(r.body).id;
  console.log(`Project: ${pid}`);

  r = await req(
    "POST",
    `http://localhost:8000/projects/${pid}/assets:presign`,
    JSON.stringify({ filename: "test.mp4", size: 1000 })
  );
  const key = JSON.parse(r.body).key;

  await req(
    "POST",
    `http://localhost:8000/projects/${pid}/assets:uploaded`,
    JSON.stringify({ key })
  );

  r = await req(
    "POST",
    `http://localhost:8000/projects/${pid}/workflows`,
    JSON.stringify({ phases: ["transcribe"] })
  );
  console.log("Workflow created");
})();
