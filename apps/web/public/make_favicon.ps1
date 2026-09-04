$b64 = Get-Content "$PSScriptRoot\favicon.b64" -Raw
$bytes = [Convert]::FromBase64String($b64.Trim())
[IO.File]::WriteAllBytes("$PSScriptRoot\favicon.ico", $bytes)
Write-Host "Done"
