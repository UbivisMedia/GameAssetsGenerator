Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting GameAssetGenerator Studio" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "Starting with Python Launcher py -3.10..." -ForegroundColor Green
    & py -3.10 main.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Starting with Python..." -ForegroundColor Green
    & python main.py
} else {
    Write-Host "ERROR: Neither 'py' nor 'python' was found in PATH!" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
