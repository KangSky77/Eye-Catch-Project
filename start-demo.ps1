param([int]$Port = 8002)
$ErrorActionPreference = 'Stop'
$demoRoot = $PSScriptRoot
$demoPython = Join-Path $demoRoot '.venv\Scripts\python.exe'

# The regular launcher reads .env and never stops an existing process.
& (Join-Path $demoRoot 'start.ps1') -Port $Port
if ($LASTEXITCODE -ne 0) { throw 'The app did not pass its ready checks.' }
$demoBase = "http://127.0.0.1:$Port"
$demoGate = Invoke-RestMethod -Uri "$demoBase/api/admission/status" -TimeoutSec 5
if (-not $demoGate.enabled -or $demoGate.capacity -notin @(12, 16, 18, 20, 24)) {
    throw 'This demo expects a 12-, 16-, 18-, 20-, or 24-visitor waiting room. The repeat-tested presentation target is 24. Check .env and the running server.'
}
$demoCapacity = $demoGate.capacity
& $demoPython (Join-Path $demoRoot 'scripts\check_demo_workers.py')
if ($LASTEXITCODE -ne 0) { throw 'Demo worker checks failed; the public endpoint was left unchanged.' }
$demoPublicUrl = & $demoPython -c "from dotenv import dotenv_values; from pathlib import Path; import sys; print(dotenv_values(Path(sys.argv[1]) / '.env').get('PRESENTATION_PUBLIC_URL', ''))" $demoRoot
if ($LASTEXITCODE -ne 0 -or -not $demoPublicUrl) { throw 'PRESENTATION_PUBLIC_URL is missing from .env.' }
$demoPublicUrl = $demoPublicUrl.Trim()
if ($demoPublicUrl -notmatch '^https://[a-zA-Z0-9.-]+/?$') { throw 'Invalid PRESENTATION_PUBLIC_URL.' }

$demoAgent = $null
try { $demoAgent = Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/endpoints' -TimeoutSec 3 } catch { }
if ($null -ne $demoAgent) {
    $demoEndpoint = @($demoAgent.endpoints | Where-Object { $_.url.TrimEnd('/') -eq $demoPublicUrl.TrimEnd('/') })
    if ($demoEndpoint.Count -ne 1) {
        throw 'The running ngrok agent does not have this public URL. Its other endpoints were left unchanged.'
    }
    $demoTarget = $demoEndpoint[0]
    $demoChanged = $false
    try {
        if ($demoTarget.upstream.url.TrimEnd('/') -ne $demoBase) {
            $demoBody = @{
                name = $demoTarget.name
                url = $demoTarget.url
                upstream = @{ url = $demoBase }
                inspect = $demoTarget.inspect
            }
            if ($null -ne $demoTarget.pooling_enabled) { $demoBody.pooling_enabled = $demoTarget.pooling_enabled }
            if ($demoTarget.traffic_policy) { $demoBody.traffic_policy = $demoTarget.traffic_policy }
            $demoChanged = $true
            Invoke-RestMethod -Method Put -Uri 'http://127.0.0.1:4040/api/endpoints' -ContentType 'application/json' -Body ($demoBody | ConvertTo-Json -Depth 8) -TimeoutSec 15 | Out-Null
        }
        $demoPublicGate = Invoke-RestMethod -Uri "$($demoPublicUrl.TrimEnd('/'))/api/admission/status" -Headers @{ 'ngrok-skip-browser-warning' = '1' } -TimeoutSec 15
        if (-not $demoPublicGate.enabled -or $demoPublicGate.capacity -ne $demoCapacity) {
            throw 'The public endpoint did not return the configured waiting room.'
        }
    } catch {
        $demoSwitchError = $_
        if ($demoChanged) {
            try {
                $demoRestore = @{ name = $demoTarget.name; url = $demoTarget.url; upstream = $demoTarget.upstream; inspect = $demoTarget.inspect }
                if ($null -ne $demoTarget.pooling_enabled) { $demoRestore.pooling_enabled = $demoTarget.pooling_enabled }
                if ($demoTarget.traffic_policy) { $demoRestore.traffic_policy = $demoTarget.traffic_policy }
                Invoke-RestMethod -Method Put -Uri 'http://127.0.0.1:4040/api/endpoints' -ContentType 'application/json' -Body ($demoRestore | ConvertTo-Json -Depth 8) -TimeoutSec 15 | Out-Null
                Write-Warning 'The previous public upstream was restored after the verification failure.'
            } catch { Write-Warning 'Automatic upstream restore could not be confirmed. Check the ngrok endpoint.' }
        }
        throw $demoSwitchError
    }
    Write-Host "Public site: $demoPublicUrl"
    Write-Host "Backend: $demoBase ($demoCapacity active visitors, others wait)"
    Write-Host 'Public waiting room verified.'
} else {
    $demoNgrok = Join-Path $demoRoot 'ngrok.exe'
    if (-not (Test-Path -LiteralPath $demoNgrok)) { throw 'ngrok.exe is missing.' }
    Write-Host "Starting the public site: $demoPublicUrl"
    Write-Host 'Keep this window open while visitors use the app.'
    & $demoNgrok http $demoBase --url $demoPublicUrl
    exit $LASTEXITCODE
}
