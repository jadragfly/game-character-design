# Remove All Black Lines from pig-soldier frames (Fixed GDI+)
# 智能移除黑色线条，只移除"贯穿性"的线条

$Threshold = 50
$MinStreak = 30

$RUN_DIR = "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"
$FRAMES_DIR = Join-Path $RUN_DIR "frames"
$FINAL_DIR = Join-Path $RUN_DIR "final"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Removing black lines from frames" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Add-Type -AssemblyName System.Drawing

$rows = @("idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup")
$totalRemoved = 0
$totalLines = 0

foreach ($row in $rows) {
    $rowRemoved = 0
    $rowLines = 0

    Write-Host "=== [$row] ===" -ForegroundColor Yellow

    for ($i = 0; $i -lt 8; $i++) {
        $framePath = Join-Path $FRAMES_DIR "${row}_${i}.png"

        if (Test-Path $framePath) {
            # Load image
            $img = [System.Drawing.Image]::FromFile($framePath)
            $bmp = New-Object System.Drawing.Bitmap($img)
            $w = $bmp.Width
            $h = $bmp.Height

            # Find all dark opaque pixels
            $darkPixels = New-Object System.Collections.ArrayList

            for ($y = 0; $y -lt $h; $y++) {
                for ($x = 0; $x -lt $w; $x++) {
                    $pixel = $bmp.GetPixel($x, $y)
                    if ($pixel.A -gt 200 -and $pixel.R -lt $Threshold -and $pixel.G -lt $Threshold -and $pixel.B -lt $Threshold) {
                        $null = $darkPixels.Add([PSCustomObject]@{X=$x; Y=$y})
                    }
                }
            }

            $img.Dispose()

            if ($darkPixels.Count -eq 0) {
                $bmp.Dispose()
                continue
            }

            # Count per column and per row
            $colCounts = @{}
            $rowCounts = @{}

            foreach ($p in $darkPixels) {
                if (-not $colCounts.ContainsKey($p.X)) { $colCounts[$p.X] = 0 }
                if (-not $rowCounts.ContainsKey($p.Y)) { $rowCounts[$p.Y] = 0 }
                $colCounts[$p.X]++
                $rowCounts[$p.Y]++
            }

            # Find spanning lines (lines that go from one edge to the other)
            $colsToRemove = @()
            $rowsToRemove = @()

            foreach ($col in $colCounts.Keys) {
                $count = $colCounts[$col]
                if ($count -ge $MinStreak -and $count -ge $h * 0.85) {
                    $colsToRemove += $col
                }
            }

            foreach ($r in $rowCounts.Keys) {
                $count = $rowCounts[$r]
                if ($count -ge $MinStreak -and $count -ge $w * 0.85) {
                    $rowsToRemove += $r
                }
            }

            $pixelsRemoved = 0
            $linesRemoved = $colsToRemove.Count + $rowsToRemove.Count

            # Remove only the detected lines
            foreach ($col in $colsToRemove) {
                for ($y = 0; $y -lt $h; $y++) {
                    $pixel = $bmp.GetPixel($col, $y)
                    if ($pixel.A -gt 200) {
                        $bmp.SetPixel($col, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
                        $pixelsRemoved++
                    }
                }
            }

            foreach ($r in $rowsToRemove) {
                for ($x = 0; $x -lt $w; $x++) {
                    $pixel = $bmp.GetPixel($x, $r)
                    if ($pixel.A -gt 200) {
                        $bmp.SetPixel($x, $r, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
                        $pixelsRemoved++
                    }
                }
            }

            # Save to a temp file first, then move (avoids GDI+ error)
            $tempPath = $framePath + ".tmp"
            $bmp.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
            $bmp.Dispose()

            # Replace original with temp
            Remove-Item $framePath -Force
            Move-Item $tempPath $framePath -Force

            if ($pixelsRemoved -gt 0) {
                Write-Host "  Frame $i : removed $pixelsRemoved pixels, $linesRemoved lines" -ForegroundColor White
                $rowRemoved += $pixelsRemoved
                $rowLines += $linesRemoved
            }
        }
    }

    if ($rowRemoved -gt 0) {
        Write-Host "  [$row] Total: $rowRemoved pixels, $rowLines lines" -ForegroundColor Cyan
        $totalRemoved += $rowRemoved
        $totalLines += $rowLines
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total: $totalRemoved pixels removed, $totalLines lines removed" -ForegroundColor Green

# Rebuild spritesheet
Write-Host ""
Write-Host "Rebuilding spritesheet..." -ForegroundColor Yellow

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
            $frameImg = [System.Drawing.Image]::FromFile($framePath)
            $graphics.DrawImage($frameImg, $x, $y)
            $frameImg.Dispose()
        }
    }
}

$graphics.Dispose()

# Generate version
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$versionStr = "v=$timestamp"

# Save spritesheet
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

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Refresh browser (Ctrl+F5) to see changes" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
