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
  // Create project
  let r = await req("POST", "http://localhost:8000/projects", JSON.stringify({ title: "Test", source_language: "en", target_language: "vi" }));
  const pid = JSON.parse(r.body).id;
  console.log(`Project: ${pid}`);

  // Upload asset
  r = await req("POST", `http://localhost:8000/projects/${pid}/assets:presign`, JSON.stringify({ filename: "test.mp4", size: 1000 }));
  const key = JSON.parse(r.body).key;
  await req("POST", `http://localhost:8000/projects/${pid}/assets:uploaded`, JSON.stringify({ key }));

  // Create workflow
  r = await req("POST", `http://localhost:8000/projects/${pid}/workflows`, JSON.stringify({ phases: ["transcribe"] }));
  const wid = JSON.parse(r.body).id;
  console.log(`Workflow: ${wid}`);

  // Get asset ID
  r = await req("GET", `http://localhost:8000/projects/${pid}`, null);
  const assetId = JSON.parse(r.body).asset_id;

  // Create transcript
  r = await req("POST", "http://localhost:8000/admin/dataset/transcripts", JSON.stringify({ 
    asset_id: assetId, 
    language: "en", 
    segments: [
      { start_ms: 0, end_ms: 2000, text: "Hello world" },
      { start_ms: 2000, end_ms: 4000, text: "This is a test" }
    ]
  }));
  const transcriptId = JSON.parse(r.body).id;
  console.log(`Transcript: ${transcriptId}`);

  // Create translation version
  r = await req("POST", `http://localhost:8000/projects/${pid}/translation`, JSON.stringify({ 
    transcript_id: transcriptId, 
    target_language: "vi" 
  }));
  const versionId = JSON.parse(r.body).id;
  console.log(`Translation version: ${versionId}`);

  // Get transcript segments
  r = await req("GET", `http://localhost:8000/admin/dataset/transcripts/${transcriptId}`, null);
  const transcript = JSON.parse(r.body);
  const segIds = transcript.segments.slice(0, 2).map(s => s.id);

  // Update translation segments
  for (let i = 0; i < segIds.length; i++) {
    await req("PATCH", `http://localhost:8000/projects/${pid}/translation/${versionId}/segments/${segIds[i]}`, 
      JSON.stringify({ text: `Translated ${i + 1}` }));
  }

  console.log(`Translation segment IDs: ${segIds.join(", ")}`);
  console.log("Setup complete!");
})();
