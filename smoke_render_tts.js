// Test render, tts, audio mix, subtitle endpoints
const http = require("http");

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
  console.log("RENDER + TTS + AUDIO + SUBTITLE FLOW");
  console.log("=".repeat(70));
  let r = await req("GET", "http://localhost:8000/projects");
  const pid = JSON.parse(r.body).items[0].id;
  console.log(`Using: ${pid}`);
  console.log("-".repeat(70));

  // Pre-fetch translation segment IDs for TTS
  const tr = await req("GET", `http://localhost:8000/projects/${pid}/translation`);
  const segs = JSON.parse(tr.body).segments || [];
  const ids = segs.slice(0, 3).map((s) => s.id);
  console.log(`Translation IDs: ${ids.join(", ") || "(none)"}`);

  let pass = 0, fail = 0;

  // 1. TTS generate (use real segment IDs or skip if none)
  const ttsPayload = ids.length > 0
    ? { segment_ids: ids, voice_id: "vi-VN-HoaiMyNeural" }
    : { segment_ids: [], voice_id: "vi-VN-HoaiMyNeural" };
  r = await req("POST", `http://localhost:8000/projects/${pid}/tts/generate`, JSON.stringify(ttsPayload));
  const ttsOk = r.status >= 200 && r.status < 300;
  console.log(`${ttsOk ? "✓" : "✗"} POST TTS generate${ids.length === 0 ? " (empty=will 400)" : ""} ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  ttsOk ? pass++ : fail++;

  // 2. TTS preview (always works)
  r = await req("POST", `http://localhost:8000/projects/${pid}/tts/preview`, JSON.stringify({ text: "Xin chào", voice_id: "vi-VN-HoaiMyNeural" }));
  const previewOk = r.status >= 200 && r.status < 300;
  console.log(`${previewOk ? "✓" : "✗"} POST TTS preview               ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  previewOk ? pass++ : fail++;

  // 3. Subtitle generate
  r = await req("POST", `http://localhost:8000/projects/${pid}/subtitles/generate`, "{}");
  const subOk = r.status >= 200 && r.status < 300;
  console.log(`${subOk ? "✓" : "✗"} POST subtitles generate     ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  subOk ? pass++ : fail++;

  // 4. Auto-mix
  r = await req("POST", `http://localhost:8000/projects/${pid}/audio/auto-mix`, JSON.stringify({ gains: { speaker1: 0.8 } }));
  const mixOk = r.status >= 200 && r.status < 300;
  console.log(`${mixOk ? "✓" : "✗"} POST audio auto-mix        ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  mixOk ? pass++ : fail++;

  // 5. Audio render
  r = await req("POST", `http://localhost:8000/projects/${pid}/audio/render`, JSON.stringify({ gains: { speaker1: 0.8 } }));
  const audioOk = r.status >= 200 && r.status < 300;
  console.log(`${audioOk ? "✓" : "✗"} POST audio render         ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  audioOk ? pass++ : fail++;

  // 6. Video render (do last, after TTS / subtitles created)
  r = await req("POST", `http://localhost:8000/projects/${pid}/render`, JSON.stringify({ resolution: "1080p", codec: "h264", audio_mode: "dubbed", burn_subtitle: true, quality_mode: "fast" }));
  const renderOk = r.status >= 200 && r.status < 300;
  console.log(`${renderOk ? "✓" : "✗"} POST render                 ${r.status}  ${r.body.slice(0, 80).replace(/\s+/g, " ")}`);
  renderOk ? pass++ : fail++;

  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  process.exit(fail > 0 ? 1 : 0);
}
main();
