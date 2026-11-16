# Package Lost Empire for Windows (Win64), Steam-ready layout.
# Requires UE 5.8 installed. Steam client should be running for OSS tests.

param(
    [string]$Configuration = "Shipping",
    [string]$OutputDir = "C:\Users\Denni\Projects\LostEmpire\Packaged\Win64",
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$ErrorActionPreference = "Stop"
$Project = "C:\Users\Denni\Projects\LostEmpire\LostEmpire.uproject"
$UAT = Join-Path $EngineRoot "Engine\Build\BatchFiles\RunUAT.bat"

if (-not (Test-Path $UAT)) {
    throw "RunUAT not found at $UAT — set -EngineRoot"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Write-Host "Packaging LostEmpire Win64 $Configuration -> $OutputDir"
& $UAT BuildCookRun `
    "-project=$Project" `
    -noP4 `
    -platform=Win64 `
    "-clientconfig=$Configuration" `
    "-serverconfig=$Configuration" `
    -cook `
    -build `
    -stage `
    -pak `
    -archive `
    "-archivedirectory=$OutputDir" `
    -utf8output

if ($LASTEXITCODE -ne 0) {
    throw "BuildCookRun failed with $LASTEXITCODE"
}

# Local Steam OSS test helper (do not include in Steam depot upload)
$AppIdSrc = "C:\Users\Denni\Projects\LostEmpire\steam_appid.txt"
$BinCandidates = @(
    (Join-Path $OutputDir "Windows\LostEmpire\Binaries\Win64"),
    (Join-Path $OutputDir "Win64\LostEmpire\Binaries\Win64"),
    (Join-Path $OutputDir "LostEmpire\Binaries\Win64")
)
foreach ($Bin in $BinCandidates) {
    if (Test-Path $Bin) {
        Copy-Item $AppIdSrc (Join-Path $Bin "steam_appid.txt") -Force
        Write-Host "Copied steam_appid.txt -> $Bin (local test only)"
        break
    }
}

Write-Host "Package complete: $OutputDir"
Write-Host "Launch via Steam for shipping tests; replace App ID 480 before store upload."
