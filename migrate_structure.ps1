# Family Smart Agent - File Structure Migration Script
# Run in PowerShell: .\migrate_structure.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  File Structure Optimization" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Step 1: Create new directories
Write-Host "[1/5] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "docs" | Out-Null
New-Item -ItemType Directory -Force -Path "scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "config" | Out-Null
New-Item -ItemType Directory -Force -Path "tests" | Out-Null
Write-Host "Done! Directories created." -ForegroundColor Green
Write-Host ""

# Step 2: Move documentation files
Write-Host "[2/5] Moving documentation files..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Filter "*.md" -File | Where-Object { $_.Name -ne "README_NEW.md" } | Move-Item -Destination "docs\" -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Filter "*.txt" -File | Move-Item -Destination "docs\" -Force -ErrorAction SilentlyContinue
Write-Host "Done! Documentation moved to docs/" -ForegroundColor Green
Write-Host ""

# Step 3: Move configuration files
Write-Host "[3/5] Moving configuration files..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Move-Item -Path ".env" -Destination "config\.env" -Force
    Write-Host "  - Moved .env" -ForegroundColor Gray
}
if (Test-Path ".env.example") {
    Move-Item -Path ".env.example" -Destination "config\.env.example" -Force
    Write-Host "  - Moved .env.example" -ForegroundColor Gray
}
Write-Host "Done! Config files moved to config/" -ForegroundColor Green
Write-Host ""

# Step 4: Copy startup scripts
Write-Host "[4/5] Updating startup scripts..." -ForegroundColor Yellow
if (Test-Path "run_fullstack.bat") {
    Copy-Item -Path "run_fullstack.bat" -Destination "scripts\start_old.bat" -Force
    Write-Host "  - Copied run_fullstack.bat to scripts/" -ForegroundColor Gray
}
Write-Host "Done! Scripts copied to scripts/" -ForegroundColor Green
Write-Host ""

# Step 5: Update README
Write-Host "[5/5] Updating README..." -ForegroundColor Yellow
if (Test-Path "README_NEW.md") {
    Copy-Item -Path "README_NEW.md" -Destination "README.md" -Force
    Write-Host "  - README updated" -ForegroundColor Gray
}
Write-Host "Done! README updated." -ForegroundColor Green
Write-Host ""

# Show results
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New structure:" -ForegroundColor Yellow
Write-Host "  backend/       - FastAPI backend" -ForegroundColor White
Write-Host "  frontend/      - React frontend" -ForegroundColor White
Write-Host "  family_agent/  - Core business logic" -ForegroundColor White
Write-Host "  docs/          - Documentation" -ForegroundColor White
Write-Host "  scripts/       - Scripts" -ForegroundColor White
Write-Host "  config/        - Configuration" -ForegroundColor White
Write-Host "  tests/         - Tests" -ForegroundColor White
Write-Host "  data/          - Data storage" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run scripts\start.bat to start services" -ForegroundColor White
Write-Host "  2. Check docs/ for detailed documentation" -ForegroundColor White
Write-Host "  3. Visit http://localhost:3000" -ForegroundColor White
Write-Host ""
