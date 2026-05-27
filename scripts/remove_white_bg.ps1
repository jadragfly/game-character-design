# Remove White Background from pig-soldier frames
# 移除残留的白色背景

$Threshold = 240

$RUN_DIR = "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"
$FRAMES_DIR = Join-Path $RUN_DIR "frames"
$FINAL_DIR = Join-Path $RUN_DIR "final"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Removing white background from frames" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Add-Type -AssemblyName System.Drawing

$rows = @("idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup")
$totalRemoved = 0

foreach ($row in $rows) {
    Write-Host "=== [$row] ===" -ForegroundColor Yellow

    for ($i = 0; $i -lt 8; $i++) {
        $framePath = Join-Path $FRAMES_DIR "${row}_${i}.png"

        if (Test-Path $framePath) {
            $img = [System.Drawing.Image]::FromFile($framePath)
            $bmp = New-Object System.Drawing.Bitmap($img)
            $w = $bmp.Width
            $h = $bmp.Height
            $img.Dispose()

            $removed = 0

            for ($y = 0; $y -lt $h; $y++) {
                for ($x = 0; $x -lt $w; $x++) {
                    $pixel = $bmp.GetPixel($x, $y)
                    $r = $pixel.R
                    $g = $pixel.G
                    $b = $pixel.B
                    $a = $pixel.A

                    # 检测白色背景 (高亮度、低饱和度)
                    if ($a -gt 200 -and $r -gt $Threshold -and $g -gt $Threshold -and $b -gt $Threshold) {
                        $bmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
                        $removed++
                    }
                }
            }

            if ($removed -gt 0) {
                $tempPath = $framePath + ".tmp"
                $bmp.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
                $bmp.Dispose()
                Remove-Item $framePath -Force
                Move-Item $tempPath $framePath -Force
                Write-Host "  Frame $i : removed $removed white pixels" -ForegroundColor White
                $totalRemoved += $removed
            } else {
                $bmp.Dispose()
            }
        }
    }
}

Write-Host ""
Write-Host "Total: $totalRemoved white pixels removed" -ForegroundColor Green

# Rebuild spritesheet
if ($totalRemoved -gt 0) {
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
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Refresh browser (Ctrl+F5) to see changes" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
