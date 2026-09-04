# Translator — One-shot smoke test
#
# Chạy sau khi `tools\run_all.ps1 -Frontend` đã start stack.
# Test end-to-end: login -> tạo project -> presign asset -> trigger workflow.
#
# Usage:
#   .\tools\smoke.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ApiBase = "http://localhost:8000"
$SystemUser = "00000000-0000-0000-0000-000000000001"

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "    OK: $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "    FAIL: $msg" -ForegroundColor Red; exit 1 }

Step 1 "Health check"
$h = Invoke-WebRequest -Uri "$ApiBase/healthz" -UseBasicParsing
if ($h.StatusCode -eq 200) { Ok "api up" } else { Fail "api down" }

Step 2 "Login (stub)"
$login = Invoke-WebRequest -Uri "$ApiBase/auth/login/stub" -Method POST `
    -ContentType "application/json" -UseBasicParsing `
    -Body (@{ email = "smoke@translator.local"; user_id = $SystemUser } | ConvertTo-Json)
$token = ($login.Content | ConvertFrom-Json).token
Ok "got token"

Step 3 "Create project"
$proj = Invoke-WebRequest -Uri "$ApiBase/projects" -Method POST `
    -ContentType "application/json" -UseBasicParsing `
    -Headers @{ Authorization = "Bearer $token" } `
    -Body (@{
        title = "Smoke Test $(Get-Date -Format 'HHmmss')"
        source_language = "zh"
        target_language = "vi"
        quality_mode = "balanced"
    } | ConvertTo-Json)
$project = $proj.Content | ConvertFrom-Json
Ok "project_id = $($project.id)"

Step 4 "Presign asset upload"
$pre = Invoke-WebRequest -Uri "$ApiBase/projects/$($project.id)/assets:presign" -Method POST `
    -ContentType "application/json" -UseBasicParsing `
    -Headers @{ Authorization = "Bearer $token" } `
    -Body (@{ filename = "smoke.mp4"; mime = "video/mp4"; size = 10MB } | ConvertTo-Json)
$preData = $pre.Content | ConvertFrom-Json
Ok "presigned key = $($preData.key)"

Step 5 "Trigger workflow"
$wf = Invoke-WebRequest -Uri "$ApiBase/projects/$($project.id)/workflows" -Method POST `
    -ContentType "application/json" -UseBasicParsing `
    -Headers @{ Authorization = "Bearer $token" } `
    -Body (@{ mode = "balanced" } | ConvertTo-Json)
$wfData = $wf.Content | ConvertFrom-Json
Ok "workflow_id = $($wfData.workflow_id), status = $($wfData.status)"

Step 6 "Check workflow status after 5s"
Start-Sleep -Seconds 5
$st = Invoke-WebRequest -Uri "$ApiBase/projects/$($project.id)/workflows/$($wfData.workflow_id)" -UseBasicParsing `
    -Headers @{ Authorization = "Bearer $token" }
Ok "status: $($st.Content)"

Write-Host "`nALL OK — stack is healthy." -ForegroundColor Green
