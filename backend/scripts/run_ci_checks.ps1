# PowerShell script for running CI checks locally via Docker Compose
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Running Local CI Checks in Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n1. Running Ruff Linter inside container..." -ForegroundColor Yellow
docker compose exec api ruff check app tests

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Ruff lint check passed!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Ruff lint check failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Running Pytest Suite with coverage..." -ForegroundColor Yellow
docker compose exec api pytest --cov=app --cov-report=term

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host " [SUCCESS] All CI checks passed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Test suite failed!" -ForegroundColor Red
    exit 1
}
