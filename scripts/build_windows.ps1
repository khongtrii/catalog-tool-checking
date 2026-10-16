param(
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$uvCache = Join-Path $projectRoot ".cache\uv"
Set-Location -LiteralPath $projectRoot

if (-not [Environment]::Is64BitOperatingSystem) {
    throw "Catalog Price Checker requires 64-bit Windows."
}

if (-not $SkipSync) {
    uv sync --extra build --cache-dir $uvCache
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency synchronization failed with exit code $LASTEXITCODE."
    }
}

uv run --extra build --no-sync --cache-dir $uvCache pyinstaller --noconfirm --clean CatalogPriceChecker.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$exePath = Join-Path $projectRoot "dist\CatalogPriceChecker\CatalogPriceChecker.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Build finished but the executable was not found at $exePath"
}

$bundlePath = Split-Path -Parent $exePath
$archivePath = Join-Path $projectRoot "dist\CatalogPriceChecker-windows-x64.zip"
Compress-Archive `
    -Path (Join-Path $bundlePath "*") `
    -DestinationPath $archivePath `
    -CompressionLevel Optimal `
    -Force

Write-Host ""
Write-Host "Build succeeded: $exePath" -ForegroundColor Green
Write-Host "Distribution archive: $archivePath" -ForegroundColor Green
