const http = require("http");

function req(method, path) {
  return new Promise((resolve) => {
    const opts = {
      hostname: "localhost",
      port: 8000,
      path,
      method,
      headers: { Accept: "application/json" }
    };
    const r = http.request(opts, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks).toString()));
    });
    r.on("error", (e) => resolve(e.message));
    r.end();
  });
}

req("GET", "/projects/98157c3e-8899-493b-9cef-37b88ac46d89/translation").then((body) => {
  const data = JSON.parse(body);
  const seg = data.segments.find(s => s.id === "f7cf954b-ee25-463f-8d27-5be851499717");
  console.log("Segment:", JSON.stringify(seg, null, 2));
});
