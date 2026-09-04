const http = require("http");

const body = JSON.stringify({
  segment_ids: ["f7cf954b-ee25-463f-8d27-5be851499717"],
  voice_id: "zh-CN-XiaoxiaoNeural"  // Chinese voice
});

const opts = {
  hostname: "localhost",
  port: 8000,
  path: "/projects/98157c3e-8899-493b-9cef-37b88ac46d89/tts/generate",
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body)
  }
};

const req = http.request(opts, (res) => {
  const chunks = [];
  res.on("data", (c) => chunks.push(c));
  res.on("end", () => {
    console.log(`Status: ${res.statusCode}`);
    console.log(`Body: ${Buffer.concat(chunks).toString()}`);
  });
});

req.on("error", (e) => console.error(e));
req.write(body);
req.end();
