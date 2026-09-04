# Translator Stack — shutdown script
#
# Dừng toàn bộ containers của cả 2 compose stack.
#
# Usage:
#   .\tools\stop_all.ps1           # stop giữ volumes
#   .\tools\stop_all.ps1 -Clean    # stop + xoá containers, networks, volumes

[CmdletBinding()]
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

Write-Host "==> Stopping translator stack..." -ForegroundColor Yellow

docker compose -f infra/docker-compose.yml down --remove-orphans 2>&1 | Out-String
docker compose -f infra/docker/docker-compose.yml down --remove-orphans 2>&1 | Out-String

if ($Clean) {
    Write-Host "==> Removing volumes + orphans..." -ForegroundColor Yellow
    docker volume prune -f 2>&1 | Out-String
}

Write-Host "==> Done." -ForegroundColor Green
