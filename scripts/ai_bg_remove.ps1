# AI Background Removal for pig-soldier using RemoveBgSkill
# 使用 AI 背景移除技能处理帧图片

$DEBUG = $true

$SKILL_DIR = "C:\Users\HP\.trae-cn\skills\背景移除技能"
$FRAMES_DIR = "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier\frames"
$FINAL_DIR = "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier\final"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Background Removal for pig-soldier" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find Python
$python = $null
if (Test-Path "$SKILL_DIR\.bg_env\Scripts\python.exe") {
    $python = "$SKILL_DIR\.bg_env\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python = "python3"
} else {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Gray

# Import the skill module
Write-Host "Loading skill module..." -ForegroundColor Gray

$skillCode = @"
import sys
import os
sys.path.insert(0, r'$($SKILL_DIR.replace('\', '\\'))')
os.environ['NETRC'] = ''
from skill import RemoveBgSkill

skill = RemoveBgSkill(model_name='u2netp')

rows = ['idle', 'walk-right', 'walk-left', 'jump', 'crouch', 'attack', 'pickup']
total = 0
success = 0

for row in rows:
    for i in range(8):
        input_file = r'$($FRAMES_DIR.replace('\', '\\'))' + '\\' + row + '_' + str(i) + '.png'
        try:
            result = skill.remove_background(input_file)
            total += 1
            if result:
                success += 1
                print('SUCCESS')
            else:
                print('FAILED')
        except Exception as e:
            print('ERROR: ' + str(e))

print('DONE:' + str(success) + '/' + str(total))
"@

# Run the Python script
Write-Host "Processing frames..." -ForegroundColor Yellow
$output = & $python -c $skillCode 2>&1

$success = 0
$total = 0

foreach ($line in $output) {
    if ($line -match "SUCCESS") {
        Write-Host "." -NoNewline -ForegroundColor Green
        $success++
    } elseif ($line -match "FAILED|ERROR") {
        Write-Host "X" -NoNewline -ForegroundColor Red
    } elseif ($line -match "DONE:(\d+)/(\d+)") {
        $success = [int]$matches[1]
        $total = [int]$matches[2]
    } elseif ($line -match "Downloading|Download|Model") {
        Write-Host ""
        Write-Host $line -ForegroundColor Cyan
    } elseif ($DEBUG -and $line -match "\[DEBUG\]|OK!") {
        Write-Host ""
        Write-Host $line -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Processed: $success/$total frames" -ForegroundColor Green

# Rebuild spritesheet
if ($success -gt 0) {
    Write-Host ""
    Write-Host "Rebuilding spritesheet..." -ForegroundColor Yellow

    Add-Type -AssemblyName System.Drawing

    $rows = @("idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup")
    $frameSizeW = 192
    $frameSizeH = 234
    $cols = 8

    $totalHeight = $rows.Count * $frameSizeH
    $totalWidth = $cols * $frameSizeW

    $spritesheet = New-Object System.Drawing.Bitmap($totalWidth, $totalHeight)
    $graphics = [System.Drawing.Graphics]::FromImage($spritesheet)
    $graphics.Clear([System.Drawing.Color]::Transparent)

    foreach ($rowIdx in 0..($rows.Count - 1)) {
        $row = $rows[$rowIdx]
        $y = $rowIdx * $frameSizeH

        for ($colIdx = 0; $colIdx -lt 8; $colIdx++) {
            $framePath = Join-Path $FRAMES_DIR "${row}_${colIdx}.png"
            if (Test-Path $framePath) {
                $x = $colIdx * $frameSizeW
                try {
                    $frameImg = [System.Drawing.Image]::FromFile($framePath)
                    $graphics.DrawImage($frameImg, $x, $y)
                    $frameImg.Dispose()
                } catch {
                    Write-Host "Warning: Could not load $framePath" -ForegroundColor Yellow
                }
            }
        }
    }

    $graphics.Dispose()

    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $versionStr = "v=$timestamp"

    $spritesheetPath = Join-Path $FINAL_DIR "spritesheet.png"
    $tempSheet = $spritesheetPath + ".tmp"
    $spritesheet.Save($tempSheet, [System.Drawing.Imaging.ImageFormat]::Png)
    $spritesheet.Dispose()

    Move-Item $tempSheet $spritesheetPath -Force

    Write-Host "  Saved: $spritesheetPath" -ForegroundColor Green
    Write-Host "  Version: $versionStr" -ForegroundColor Cyan

    # Update engine.js
    $enginePath = "D:\impotent\skills\make_game\pig-contra-game\js\engine.js"
    if (Test-Path $enginePath) {
        $content = Get-Content $enginePath -Raw
        $newContent = $content -replace 'ASSET_VERSION\s*=\s*["\x27][^"\x27]+["\x27]', "ASSET_VERSION = `"$versionStr`""
        if ($content -ne $newContent) {
            Set-Content -Path $enginePath -Value $newContent -NoNewline -Encoding UTF8
            Write-Host "  Updated engine.js" -ForegroundColor Green
        }
    }

    # Update enemy.js and player.js
    $enemyPath = "D:\impotent\skills\make_game\pig-contra-game\js\enemy.js"
    if (Test-Path $enemyPath) {
        $content = Get-Content $enemyPath -Raw
        $newContent = $content -replace 'engine\.js\?v=\d+', "engine.js?$versionStr"
        if ($content -ne $newContent) {
            Set-Content -Path $enemyPath -Value $newContent -NoNewline -Encoding UTF8
        }
    }

    $playerPath = "D:\impotent\skills\make_game\pig-contra-game\js\player.js"
    if (Test-Path $playerPath) {
        $content = Get-Content $playerPath -Raw
        $newContent = $content -replace 'engine\.js\?v=\d+', "engine.js?$versionStr"
        if ($content -ne $newContent) {
            Set-Content -Path $playerPath -Value $newContent -NoNewline -Encoding UTF8
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Refresh browser (Ctrl+F5) to see changes" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
