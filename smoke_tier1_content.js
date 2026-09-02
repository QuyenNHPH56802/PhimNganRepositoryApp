// Verify HTML content render đầy đủ
const http = require("http");

function fetchUrl(url) {
  return new Promise((resolve) => {
    http
      .get(url, (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            body: Buffer.concat(chunks).toString("utf8"),
          }),
        );
      })
      .on("error", (err) => resolve({ status: 0, body: "", error: err.message }));
  });
}

const checks = [
  // [path, regex cần tồn tại, label]
  ["/", /Bảng điều khiển|Quản lý project|Dashboard/, "Dashboard có title VI"],
  ["/", /Tổng project|Đang xử lý/, "Dashboard có stat cards"],
  ["/projects", /Dự án|Chưa có project|Project gần đây/, "Projects page có content"],
  ["/projects/new", /Tạo|Tiêu đề|Source|chất lượng/, "Form tạo project có field"],
  ["/voice", /Giọng nói|Voice|Tạo voice/, "Voice page render"],
  ["/settings", /Cài đặt|Setting|theme/, "Settings render"],
  ["/admin", /Quản trị|Admin|audit|dataset/, "Admin render"],
];

async function main() {
  console.log("CONTENT VERIFICATION");
  console.log("=".repeat(70));
  let pass = 0,
    fail = 0;
  for (const [path, re, label] of checks) {
    const r = await fetchUrl(`http://localhost:3000${path}`);
    const m = re.test(r.body);
    const length = r.body.length;
    console.log(
      `${m ? "✓" : "✗"} ${path.padEnd(20)} len=${String(length).padStart(6)}  ${label}`,
    );
    if (!m) {
      console.log(`    Pattern: ${re}`);
      console.log(`    Body excerpt: ${r.body.slice(0, 300).replace(/\s+/g, " ")}`);
      fail++;
    } else pass++;
  }
  console.log("=".repeat(70));
  console.log(`PASS: ${pass}   FAIL: ${fail}`);
  process.exit(fail > 0 ? 1 : 0);
}
main();
