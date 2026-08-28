# Translator Stack — one-shot launcher
#
# Start toàn bộ stack: Postgres + MinIO + Temporal + API + Worker + Web
# (tts-service nằm ở compose stack riêng ở infra/docker/docker-compose.yml)
#
# Usage:
#   .\tools\run_all.ps1           # build + start tất cả services
#   .\tools\run_all.ps1 -Rebuild  # force rebuild images trước khi start
#   .\tools\run_all.ps1 -Frontend # đồng thời start web UI

[CmdletBinding()]
param(
    [switch]$Rebuild,
    [switch]$Frontend,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Require-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "docker not found in PATH. Install Docker Desktop first."
    }
}

Require-Docker

Write-Step "1/5 Bring down any leftover containers from previous runs"
docker compose -f infra/docker-compose.yml down --remove-orphans 2>&1 | Out-Null
docker compose -f infra/docker/docker-compose.yml down --remove-orphans 2>&1 | Out-Null

Write-Step "2/5 Start core stack (postgres + minio + temporal + api + worker)"
$BuildFlag = if ($Rebuild) { "--build" } else { "" }
docker compose -f infra/docker-compose.yml up -d $BuildFlag postgres minio minio-init temporal-postgresql temporal temporal-ui api worker

Write-Step "3/5 Wait for Postgres + Temporal to become healthy"
$maxWait = 90
$elapsed = 0
while ($elapsed -lt $maxWait) {
    $pg = docker ps --filter "name=postgres-1$" --format "{{.Names}} {{.Status}}"
    $t = docker ps --filter "name=temporal-1$" --format "{{.Names}} {{.Status}}"
    if (($pg -match "healthy") -and ($t -match "Up")) { break }
    Start-Sleep -Seconds 3
    $elapsed += 3
    Write-Host "    waiting... ${elapsed}s"
}

Write-Step "4/5 Run Alembic migrations on the API container"
docker compose -f infra/docker-compose.yml exec -T api bash -c "cd /app/infra/migrations && alembic upgrade head"
if ($LASTEXITCODE -ne 0) {
    Write-Host "    migrations failed — check api logs" -ForegroundColor Yellow
}

Write-Step "4b/5 Seed default system user (idempotent)"
$seedSql = @"
INSERT INTO users (id, email, display_name)
VALUES ('00000000-0000-0000-0000-000000000001','system@translator.local','System')
ON CONFLICT (id) DO NOTHING;
"@
docker compose -f infra/docker-compose.yml exec -T postgres psql -U translator -d translator -c $seedSql 2>&1 | Out-String | Write-Host

if ($Frontend) {
    Write-Step "5/5 Start web UI (Next.js on :3000)"
    docker compose -f infra/docker-compose.yml up -d $BuildFlag web
    Write-Host "    waiting for web..."
    $elapsed = 0
    while ($elapsed -lt 60) {
        $w = docker ps --filter "name=web-1$" --format "{{.Names}} {{.Status}}"
        if ($w -match "Up") { break }
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
}

Write-Host ""
Write-Host "================ Stack is up ================" -ForegroundColor Green
Write-Host "  API         http://localhost:8000" -ForegroundColor White
Write-Host "  Temporal UI http://localhost:8088" -ForegroundColor White
Write-Host "  MinIO UI    http://localhost:9001  (minioadmin / minioadmin)" -ForegroundColor White
if ($Frontend) {
    Write-Host "  Web         http://localhost:3000" -ForegroundColor White
}
Write-Host "=============================================" -ForegroundColor Green

if ($Logs) {
    Write-Host ""
    Write-Step "Tailing logs (Ctrl+C to stop)"
    docker compose -f infra/docker-compose.yml logs -f --tail=100 api worker temporal
}
