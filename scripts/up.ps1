# PowerShell wrapper for Windows. Run from repo root.

param(
    [string]$Command = "up"
)

$PROJECT = "translator"
$composeArgs = @("compose", "-f", "infra/docker/docker-compose.yml")

switch ($Command) {
    "up"   { docker @composeArgs up -d --build }
    "down" { docker @composeArgs down }
    "logs" { docker @composeArgs logs -f --tail=100 }
    "build" { docker @composeArgs build --pull }
    "restart" { docker @composeArgs restart api worker web }
    "ps"   { docker @composeArgs ps }
    default {
        Write-Host "Unknown command: $Command"
        Write-Host "Usage: scripts/up.ps1 [up|down|logs|build|restart|ps]"
        exit 1
    }
}
