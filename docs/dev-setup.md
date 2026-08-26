# Dev Setup

Mục tiêu: chạy toàn bộ stack dev trong < 15 phút. Phase 1 chỉ scaffold; chưa có provider thật.

## Yêu cầu

- Docker 24+ và Docker Compose v2.
- Node 20 LTS + pnpm 9 (`corepack enable`).
- Python 3.11+ (chỉ cần khi chạy API/worker local ngoài Docker).

## Khởi động stack dev

```bash
docker compose -f infra/docker-compose.yml up -d
```

Các service dựng lên:

| Service | Port | Mục đích |
|---|---|---|
| postgres | 5432 | Business DB |
| minio | 9000 / 9001 | S3-compatible dev storage |
| temporal-postgresql | 5433 | Temporal persistence |
| temporal | 7233 | Workflow engine |
| temporal-ui | 8088 | Temporal UI |
| api | 8000 | FastAPI |
| worker | — | Temporal worker (background) |
| web | 3000 | Next.js |

## Cài dependency local

```bash
pnpm install
pip install -e packages/shared -e apps/api -e apps/worker
```

## Migration

```bash
TRANSLATOR_DATABASE_URL=postgresql+psycopg://translator:translator@localhost:5432/translator \
  alembic -c infra/migrations/alembic.ini upgrade head
```

Phase 1 chỉ có một migration `0001_phase1_baseline` ánh xạ đúng `docs/ERD.md`.

## Chạy từng phần (tùy chọn)

```bash
pnpm api:dev      # uvicorn trên :8000
pnpm worker:dev   # temporal worker
pnpm web:dev      # next dev trên :3000
```

## Smoke test

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:3000/api/healthz
```

Tạo project:

```bash
curl -X POST http://localhost:8000/projects \
  -H 'content-type: application/json' \
  -d '{"title":"smoke","quality_mode":"standard_dubbing"}'
```

Trigger workflow:

```bash
curl -X POST http://localhost:8000/projects/<PROJECT_ID>/workflows \
  -H 'content-type: application/json' \
  -d '{}'
```

Worker sẽ log activity checkpoints trên console.

## Truy cập UI

- Web app: http://localhost:3000
- Temporal UI: http://localhost:8088
- MinIO console: http://localhost:9001 (`minioadmin` / `minioadmin`)
- Swagger API: http://localhost:8000/docs

## Lưu ý Phase 1

- Chưa có provider thật: activity stub trả `ArtifactSignature` rỗng và log checkpoint.
- Auth là stub. KHÔNG dùng cho bất kỳ môi trường nào có data thật.
- MinIO chỉ là dev adapter theo S3 API contract; production phải thay bằng deployment S3-compatible có license rõ ràng (xem `docs/licenses.md`).
- Phase 2 sẽ thay placeholder models bằng ORM thật và migration tiếp theo nếu schema cần tinh chỉnh.