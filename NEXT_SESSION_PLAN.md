# NEXT_SESSION_PLAN.md

Phiên này (28-Aug-2026, 8:02 → 9:11 UTC+7) làm đến đâu và phiên tới cần làm gì.

## ✅ Đã làm xong (commit `aa82d67`, đã push lên `develop`)

### Backend (apps/api)
1. **File mới**: `apps/api/python/translator_api/routers_editor.py`
   - 6 endpoint GET: `/projects/{id}/{transcript|translation|speakers|voices|subtitles|audio}`
   - Trả demo segments (3 câu tiếng Trung + dịch tiếng Việt) khi project chưa có asset/track → editor không bao giờ 404 nữa.
   - Khi worker đã chạy, trả dữ liệu thật từ DB.
2. **Wire router**: `main.py` include `editor_router`.
3. **Auth fix**: `infra/docker/docker-compose.yml` thêm `TRANSLATOR_SESSION_SECRET` — không có env này API đang 500 trên `/auth/login/stub`.
4. **Dockerfile fix**: `infra/docker/api.Dockerfile` copy `infra/migrations` để chạy được alembic bên trong container.

### Frontend (apps/web)
5. **`app/voice/page.tsx`**: route qua `/admin/voice-profiles` qua `lib/api.listAdminVoiceProfiles()` (sửa cả typo `display_name`/`speaker_id`).
6. **`lib/useAdminRole.ts`**: gọi `api.listProjects()` (đã auth) thay vì phantom `/api/me`.
7. **`app/settings/page.tsx`**: lấy project id thật t� `listProjects().items[0]` thay vì hardcoded `00000000-...`.

### Repo
8. `.gitignore` thêm `.next/` (build cache đang làm git status tới ~200 entries).

---

## ⏸️ Phiên này dừng ở đâu — phiên tới làm tiếp

### 1. Build image API/Worker + apply migrations (blocker)
Mục tiêu: backend phục vụ được `transcript/translation/...` với 200 + data thật.

```powershell
# Dọn container cũ (đã có conflict port 5432 / 8000 / 3099)
docker rm -f devstack-api-1 devstack-worker-1 devstack-db-1 devstack-temporal-1 devstack-tts-service-1

# Rebuild chỉ 2 service đổi code (image api/worker đã có sẵn migrations dir + session secret env)
docker compose -f infra/docker/docker-compose.yml -p devstack build api worker

# Start đủ stack
docker compose -f infra/docker/docker-compose.yml -p devstack up -d

# Verify
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Sau khi container lên, nếu DB chưa có tables:
```powershell
docker exec devstack-api-1 sh -c "cd /app/infra/migrations && alembic -c alembic.ini upgrade head"
```

Smoke test:
```powershell
python -c "
import urllib.request, json
r = urllib.request.urlopen(urllib.request.Request('http://localhost:8000/auth/login/stub',
  data=json.dumps({'email':'admin@translator.local'}).encode(),
  headers={'Content-Type':'application/json'})).read().decode()
T = json.loads(r)['token']
r = urllib.request.urlopen(urllib.request.Request('http://localhost:8000/projects',
  data=json.dumps({'title':'Smoke'}).encode(),
  headers={'Content-Type':'application/json','Authorization':f'Bearer {T}'})).read().decode()
PID = json.loads(r)['id']
for ep in ['transcript','translation','speakers','voices','subtitles','audio']:
    try:
        r = urllib.request.urlopen(urllib.request.Request(f'http://localhost:8000/projects/{PID}/{ep}',
          headers={'Authorization':f'Bearer {T}'})).read().decode()
        print(f'{ep}: OK -> {r[:120]}')
    except urllib.error.HTTPError as e:
        print(f'{ep}: {e.code}')
"
```

### 2. Cài Playwright + viết E2E headless
- File test: `apps/web/e2e/translation.spec.ts` (hoặc thư mục mới `apps/web/tests/e2e/`).
- Stack: `pnpm add -D @playwright/test`, `pnpm exec playwright install chromium`.
- Test case:
  - Mở `/login` → login stub → lưu token.
  - Mở `/projects` → click "New" → tạo project.
  - Mở `/projects/{id}/upload` → upload MP4 10s.
  - Trigger workflow → poll `/workflows/{id}/steps` cho tới khi `render` step xong.
  - Click "Render" → verify có URL MP4 output.

### 3. Tạo video 10s đầu vào + chạy pipeline thật
- File `generate_qwen3_sample.py` đã có — kiểm tra có tạo được MP4 không (cần ffmpeg).
- Upload qua endpoint:
  ```
  POST /projects/{id}/assets:presign → lấy presigned URL
  PUT  <presigned URL> → upload file
  POST /projects/{id}/workflows → trigger
  ```
- Wait cho workflow hoàn tất → render step sẽ xuất MP4 dịch sang VI.

### 4. Verify output MP4
- Download output về local → check:
  - `ffprobe -i output.mp4` có 2 stream (video gốc + audio VI)?
  - Duration ~10s?
  - Subtitle track có text tiếng Việt?

### 5. Fix React Fast Refresh `startTime undefined` crash
- Đây là dev-only bug, hot reload gặp race khi zustand store chưa mount.
- Cách 1: bỏ `import type { Panel }` khỏi `@/lib/store` (giữ export runtime + type riêng).
- Cách 2: thêm `if (typeof window !== 'undefined')` guard quanh `useEditor` selector.
- Test: save một file, quan sát console có còn `Cannot read properties of undefined (reading 'startTime')` không.

### 6. Cleanup
- `apps/web/.next/` đã ignore, nếu vẫn còn trong git status thì `git rm -r --cached apps/web/.next`.
- Container `docker-*` thừa → `docker rm -f docker-tts-service-1`.

---

## 🗂️ File quan trọng cần mở lại phiên sau

| File | Vai trò |
|---|---|
| `apps/api/python/translator_api/routers_editor.py` | Mới — 6 endpoint GET, trả demo data khi worker chưa chạy |
| `apps/api/python/translator_api/main.py` | Đã thêm `editor_router` include |
| `infra/docker/docker-compose.yml` | Thêm `TRANSLATOR_SESSION_SECRET` env |
| `infra/docker/api.Dockerfile` | Copy `infra/migrations` |
| `apps/web/app/voice/page.tsx` | Refactor sang lib/api |
| `apps/web/lib/useAdminRole.ts` | Gọi listProjects |
| `apps/web/app/settings/page.tsx` | Lấy project id thật |

## 📍 Trạng thái stack hiện tại (cần verify lại khi mở phiên)

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Kỳ vọng:
- `devstack-api-1` Up, port 8000
- `devstack-worker-1` Up
- `devstack-db-1` Up (port 5432 internal — KHÔNG exposed)
- `devstack-temporal-1` Up
- `devstack-tts-service-1` Up, port 3099
- Có thể thiếu `devstack-web-1` nếu build chưa xong lần trước.

## 📌 Branch

`develop` (push xong tại `aa82d67`).
URL: https://github.com/QuyenNHPH56802/PhimNganRepositoryApp

## ⚠️ Known gotcha

- `docker compose` cần `-p devstack` để tránh xung đột với container `translator-dev-*` cũ (đã xóa hết ở phiên này nhưng có thể recreate khi user chạy lại script khác).
- Web container cần build image từ `apps/web/package.json` (Next.js) — build lần đầu mất ~3-5 phút vì `pnpm install`.
- Backend Python build ~2 phút vì `pip install -e ".[api,shared]"`.
