# Instabids GitHub Push Helper (PowerShell Version)
# This script helps push the complete Instabids project to GitHub while avoiding 'nul' files

param(
    [string]$Mode = "Interactive"  # Can be "Interactive", "Quick", or "Check"
)

$ErrorActionPreference = "Continue"

# Colors for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }

# Navigate to instabids directory
$instabidsPath = "C:\Users\Not John Or Justin\Documents\instabids"
Set-Location $instabidsPath

Write-Host "`n=======================================" -ForegroundColor Blue
Write-Host "   Instabids GitHub Push Helper" -ForegroundColor Blue
Write-Host "=======================================`n" -ForegroundColor Blue

# Verify we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Error "ERROR: Not in a git repository!"
    Write-Error "Current directory: $(Get-Location)"
    exit 1
}

Write-Info "Current directory: $(Get-Location)"

# Function to get git status summary
function Get-GitStatusSummary {
    $status = git status --porcelain
    $staged = ($status | Where-Object { $_ -match "^A" }).Count
    $modified = ($status | Where-Object { $_ -match "^M" }).Count
    $untracked = ($status | Where-Object { $_ -match "^\?\?" }).Count
    
    Write-Info "`nGit Status Summary:"
    Write-Host "  Staged files: $staged" -ForegroundColor Green
    Write-Host "  Modified files: $modified" -ForegroundColor Yellow
    Write-Host "  Untracked files: $untracked" -ForegroundColor Cyan
    
    return @{
        Staged = $staged
        Modified = $modified
        Untracked = $untracked
        Total = $status.Count
    }
}

# Function to add files systematically
function Add-ProjectFiles {
    Write-Info "`nAdding project files systematically..."
    
    # Reset first
    git reset HEAD | Out-Null
    Write-Success "✓ Reset complete"
    
    # Root files
    $rootPatterns = @(
        ".gitignore", "README.md", "LICENSE", 
        "package.json", "package-lock.json",
        "*.md", "*.sql", "*.py", "*.json", "*.bat", "*.sh"
    )
    
    Write-Info "`nAdding root files..."
    foreach ($pattern in $rootPatterns) {
        $files = Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue
        if ($files) {
            git add $pattern 2>$null
            Write-Host "  ✓ Added $($files.Count) files matching '$pattern'" -ForegroundColor Green
        }
    }
    
    # Directories
    $directories = @(
        "web", "ai-agents", "additional_projects", "agent_specifications",
        "assets", "database", "demos", "docs", "frontend", "knowledge",
        "mobile", "scripts", "shared", "supabase", "test-images", "test-sites",
        ".github", ".husky"
    )
    
    Write-Info "`nAdding directories..."
    foreach ($dir in $directories) {
        if (Test-Path $dir) {
            git add "$dir/" 2>$null
            $addedCount = (git status --porcelain "$dir/" | Where-Object { $_ -match "^A" }).Count
            if ($addedCount -gt 0) {
                Write-Success "  ✓ Added $addedCount files from $dir/"
            } else {
                Write-Host "  - No new files in $dir/" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ⚠ Directory not found: $dir" -ForegroundColor DarkGray
        }
    }
}

# Main execution based on mode
switch ($Mode) {
    "Quick" {
        Write-Info "Running in QUICK mode..."
        
        # Add all files
        Add-ProjectFiles
        
        # Get status
        $status = Get-GitStatusSummary
        
        if ($status.Staged -gt 0) {
            # Commit
            Write-Info "`nCommitting changes..."
            git commit -m "Complete Instabids platform with 8 AI agents, web/mobile frontends, and 5 expansion projects"
            
            # Push
            Write-Info "`nPushing to GitHub..."
            git push -u origin main
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "`n✓ Successfully pushed to GitHub!"
            } else {
                Write-Error "`n✗ Push failed. You may need to pull first or force push."
            }
        } else {
            Write-Warning "`nNo files to commit."
        }
    }
    
    "Check" {
        Write-Info "Checking repository status..."
        Get-GitStatusSummary
        
        Write-Info "`nRemote configuration:"
        git remote -v
        
        Write-Info "`nLatest commits:"
        git log --oneline -5
    }
    
    "Interactive" {
        # Show current status
        $status = Get-GitStatusSummary
        
        # Menu
        Write-Host "`nWhat would you like to do?" -ForegroundColor Yellow
        Write-Host "1. Add all files and push"
        Write-Host "2. Add files step-by-step"
        Write-Host "3. Check detailed status"
        Write-Host "4. Reset all staged files"
        Write-Host "5. Exit"
        
        $choice = Read-Host "`nEnter your choice (1-5)"
        
        switch ($choice) {
            "1" {
                # Quick push
                & $PSCommandPath -Mode "Quick"
            }
            "2" {
                # Step by step
                Add-ProjectFiles
                $newStatus = Get-GitStatusSummary
                
                if ($newStatus.Staged -gt 0) {
                    Write-Info "`nReady to commit $($newStatus.Staged) files."
                    $commitMsg = Read-Host "Enter commit message (or press Enter for default)"
                    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
                        $commitMsg = "Update Instabids platform"
                    }
                    
                    git commit -m $commitMsg
                    
                    $push = Read-Host "`nPush to GitHub? (y/n)"
                    if ($push -eq 'y') {
                        git push -u origin main
                    }
                }
            }
            "3" {
                # Detailed status
                Write-Info "`nDetailed Git Status:"
                git status
                
                Write-Info "`nStaged files:"
                git diff --cached --name-only
            }
            "4" {
                # Reset
                git reset HEAD
                Write-Success "✓ All files unstaged"
            }
            "5" {
                Write-Info "Goodbye!"
                exit 0
            }
            default {
                Write-Warning "Invalid choice"
            }
        }
    }
}

Write-Host "`n=======================================" -ForegroundColor Blue
Write-Host "        Process Complete!" -ForegroundColor Blue  
Write-Host "=======================================`n" -ForegroundColor Blue
