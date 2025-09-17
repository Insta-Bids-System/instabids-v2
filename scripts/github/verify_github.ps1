# Instabids GitHub Verification Script (PowerShell)

Write-Host "🔍 Verifying Instabids GitHub Repository..." -ForegroundColor Cyan
Write-Host "==========================================="

# Navigate to project directory
Set-Location "C:\Users\Not John Or Justin\Documents\instabids"

# Check current branch
Write-Host "`n📌 Current Branch:" -ForegroundColor Yellow
git branch --show-current

# Check remote
Write-Host "`n📡 Remote Repository:" -ForegroundColor Yellow
git remote -v

# Count files
Write-Host "`n📊 Repository Statistics:" -ForegroundColor Yellow
$totalFiles = (git ls-files | Measure-Object).Count
$agentFiles = (git ls-files ai-agents/agents | Measure-Object).Count
$frontendFiles = (git ls-files web/src | Measure-Object).Count
$dbFiles = (git ls-files supabase/migrations | Measure-Object).Count

Write-Host "Total files: $totalFiles"
Write-Host "AI Agent files: $agentFiles"
Write-Host "Frontend files: $frontendFiles"
Write-Host "Database migrations: $dbFiles"

# Check for secrets in committed files
Write-Host "`n🔒 Security Check:" -ForegroundColor Yellow
$secretsFound = git grep -i "sk-ant-api03" 2>$null
if ($secretsFound) {
    Write-Host "⚠️ WARNING: Found API keys in committed files!" -ForegroundColor Red
} else {
    Write-Host "✅ No API keys found in committed files" -ForegroundColor Green
}

# List key directories
Write-Host "`n📁 Key Directories:" -ForegroundColor Yellow
$keyDirs = @("ai-agents/agents", "web/src", "supabase/migrations", "agent_specifications")
foreach ($dir in $keyDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir missing!" -ForegroundColor Red
    }
}

# Check GitHub connectivity
Write-Host "`n🌐 GitHub Connectivity:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://api.github.com/repos/Insta-Bids-System/instabids" -UseBasicParsing
    $repoData = $response.Content | ConvertFrom-Json
    Write-Host "✅ Repository accessible" -ForegroundColor Green
    Write-Host "📅 Created at: $($repoData.created_at)"
    Write-Host "⭐ Size: $($repoData.size) KB"
} catch {
    Write-Host "❌ Could not access repository - check if it's private" -ForegroundColor Red
}

Write-Host "`n✅ Verification Complete!" -ForegroundColor Green
Write-Host "🔗 Repository URL: https://github.com/Insta-Bids-System/instabids" -ForegroundColor Cyan

Write-Host "`n⚠️ NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Add GitHub Secrets at: https://github.com/Insta-Bids-System/instabids/settings/secrets/actions"
Write-Host "2. Use values from: C:\Users\Not John Or Justin\Documents\instabids\SECRETS_DO_NOT_COMMIT.txt"
Write-Host "3. Test deployment with GitHub Actions"

pause