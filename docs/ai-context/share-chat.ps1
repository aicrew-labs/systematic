# ==============================================================================
# AI Selective Chat Sync Script (Method A - Windows PowerShell version)
# ==============================================================================
# This script selectively shares individual Antigravity chats via your OneDrive
# project directory, keeping other personal chats 100% private on Windows.
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = (Get-Item "$ScriptDir\..\..").FullName
$SharedDir = "$ProjectDir\docs\ai-context\shared-chats"
$LocalAppDir = "$HOME\.gemini\antigravity"

# Create directories if they do not exist
New-Item -ItemType Directory -Force -Path "$SharedDir\conversations" | Out-Null
New-Item -ItemType Directory -Force -Path "$SharedDir\brain" | Out-Null
New-Item -ItemType Directory -Force -Path "$LocalAppDir\conversations" | Out-Null
New-Item -ItemType Directory -Force -Path "$LocalAppDir\brain" | Out-Null

Write-Host "🎯 Project Directory: $ProjectDir" -ForegroundColor Cyan
Write-Host "📂 Shared Folder: $SharedDir" -ForegroundColor Cyan
Write-Host "💻 Local Windows AI App Directory: $LocalAppDir" -ForegroundColor Cyan
Write-Host "--------------------------------------------------"

# Function: Sync incoming chats from Git/OneDrive to Local App
function Sync-Incoming {
    Write-Host "🔍 Scanning for shared chats in the repository..." -ForegroundColor Yellow
    
    $sharedFiles = Get-ChildItem -Path "$SharedDir\conversations" -Filter "*.pb"
    
    if ($sharedFiles.Count -eq 0 -or $null -eq $sharedFiles) {
        Write-Host "ℹ️ No shared chats found in the repository folder yet." -ForegroundColor Gray
        return
    }
    
    foreach ($file in $sharedFiles) {
        $chatId = $file.BaseName
        $filename = $file.Name
        
        Write-Host "   Found shared chat ID: $chatId"
        
        # 1. Symlink the conversation file
        $localConvPath = "$LocalAppDir\conversations\$filename"
        $sharedPath = $file.FullName
        
        if (-not (Test-Path -Path $localConvPath)) {
            try {
                New-Item -ItemType SymbolicLink -Path $localConvPath -Value $sharedPath -Force | Out-Null
                Write-Host "   ✅ Symlinked conversation file to local app." -ForegroundColor Green
            } catch {
                Write-Host "   ⚠️ Failed to create file symlink directly. Trying file copy instead (standard Windows behavior)..." -ForegroundColor Yellow
                Copy-Item -Path $sharedPath -Destination $localConvPath -Force
                Write-Host "   ✅ Copied conversation file successfully." -ForegroundColor Green
            }
        } else {
            Write-Host "   ✓ Conversation file already synced." -ForegroundColor Gray
        }
        
        # 2. Junction the brain folder (Junctions don't require Admin privileges on Windows!)
        $localBrainPath = "$LocalAppDir\brain\$chatId"
        $sharedBrainPath = "$SharedDir\brain\$chatId"
        
        New-Item -ItemType Directory -Force -Path $sharedBrainPath | Out-Null
        
        if (-not (Test-Path -Path $localBrainPath)) {
            try {
                New-Item -ItemType Junction -Path $localBrainPath -Value $sharedBrainPath -Force | Out-Null
                Write-Host "   ✅ Symlinked brain context directory." -ForegroundColor Green
            } catch {
                Write-Host "   ❌ Failed to link brain folder: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "   ✓ Brain context already linked." -ForegroundColor Gray
        }
    }
    Write-Host "🎉 Sync complete! All shared chats are now available in your Windows sidebar history." -ForegroundColor Green
}

# Function: Share a local chat by ID
function Share-Chat-Id ($chatId) {
    $localPb = "$LocalAppDir\conversations\${chatId}.pb"
    $localBrain = "$LocalAppDir\brain\${chatId}"
    
    if (-not (Test-Path -Path $localPb)) {
        Write-Host "❌ Error: Conversation ID '$chatId' not found in your local history ($localPb)." -ForegroundColor Red
        Exit 1
    }
    
    Write-Host "📤 Sharing chat ID: $chatId" -ForegroundColor Yellow
    
    $sharedPb = "$SharedDir\conversations\${chatId}.pb"
    
    # 1. Handle conversation file
    if (-not (Test-Path -Path $sharedPb)) {
        Move-Item -Path $localPb -Destination $sharedPb -Force
        try {
            New-Item -ItemType SymbolicLink -Path $localPb -Value $sharedPb -Force | Out-Null
            Write-Host "   ✅ Moved and symlinked conversation file." -ForegroundColor Green
        } catch {
            Copy-Item -Path $sharedPb -Destination $localPb -Force
            Write-Host "   ✅ Moved and copied conversation file." -ForegroundColor Green
        }
    } else {
        Write-Host "   ✓ Conversation file is already shared." -ForegroundColor Gray
    }
    
    # 2. Handle brain directory
    $sharedBrain = "$SharedDir\brain\${chatId}"
    New-Item -ItemType Directory -Force -Path $sharedBrain | Out-Null
    
    if ((Test-Path -Path $localBrain) -and -not (Get-Item $localBrain).LinkType) {
        Copy-Item -Path "$localBrain\*" -Destination $sharedBrain -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $localBrain -Recurse -Force
        New-Item -ItemType Junction -Path $localBrain -Value $sharedBrain -Force | Out-Null
        Write-Host "   ✅ Moved and linked brain context." -ForegroundColor Green
    } elseif (-not (Test-Path -Path $localBrain)) {
        New-Item -ItemType Junction -Path $localBrain -Value $sharedBrain -Force | Out-Null
        Write-Host "   ✅ Created link for new empty brain context." -ForegroundColor Green
    } else {
        Write-Host "   ✓ Brain context is already shared." -ForegroundColor Gray
    }
    
    Write-Host "🎉 Successfully shared! Commit and push your changes to GitHub to sync." -ForegroundColor Green
}

# Function: Auto-detect the most recent local chat on Windows
function Detect-Latest-Chat {
    Write-Host "🔍 Scanning for your most recently active local chat..." -ForegroundColor Yellow
    
    $conversations = Get-ChildItem -Path "$LocalAppDir\conversations" -Filter "*.pb" | Sort-Object LastWriteTime -Descending
    
    $latestChat = $null
    foreach ($c in $conversations) {
        if (-not $c.LinkType) {
            $latestChat = $c
            break
        }
    }
    
    if ($null -ne $latestChat) {
        $chatId = $latestChat.BaseName
        Write-Host "💡 Detected latest local chat: $chatId" -ForegroundColor Magenta
        
        $confirm = Read-Host "❓ Do you want to share this chat with your partner? (y/n)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            Share-Chat-Id $chatId
        } else {
            Write-Host "❌ Canceled." -ForegroundColor Red
        }
    } else {
        Write-Host "ℹ️ No unshared local chats detected." -ForegroundColor Gray
    }
}

# Main execution routing
$arg = $args[0]

if ($arg -eq "--sync" -or [string]::IsNullOrEmpty($arg)) {
    Sync-Incoming
    if ($arg -eq "--sync") {
        Exit 0
    }
    Write-Host "--------------------------------------------------"
    Detect-Latest-Chat
} else {
    Share-Chat-Id $arg
}
