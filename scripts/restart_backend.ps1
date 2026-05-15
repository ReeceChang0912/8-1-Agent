param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -like "python*" -and
        (
            ($_.CommandLine -like "*uvicorn*" -and $_.CommandLine -like "*backend.main:app*") -or
            ($_.CommandLine -like "*multiprocessing.spawn*" -and $_.CommandLine -like "*multiprocessing-fork*")
        )
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($listener in $listeners) {
    $processId = $listener.OwningProcess
    if ($processId) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2
Start-Process `
    -FilePath python `
    -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$Port") `
    -WorkingDirectory $root `
    -WindowStyle Hidden

Start-Sleep -Seconds 5
Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 8 | ConvertTo-Json -Compress
