# Enhanced Line Analysis for pig-soldier
# 分析线条的厚度、长度和位置

$Threshold = 50

# Main
$RUN_DIR = "D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier"
$FRAMES_DIR = Join-Path $RUN_DIR "frames"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Analyzing pig-soldier frames for lines" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Add-Type -AssemblyName System.Drawing

$rows = @("idle", "walk-right", "walk-left", "jump", "crouch", "attack", "pickup")

foreach ($row in $rows) {
    Write-Host "=== [$row] ===" -ForegroundColor Yellow

    for ($i = 0; $i -lt 8; $i++) {
        $framePath = Join-Path $FRAMES_DIR "${row}_${i}.png"

        if (Test-Path $framePath) {
            $img = [System.Drawing.Image]::FromFile($framePath)
            $bmp = New-Object System.Drawing.Bitmap($img)
            $w = $bmp.Width
            $h = $bmp.Height

            $colCounts = @{}
            $rowCounts = @{}
            $totalDark = 0

            for ($y = 0; $y -lt $h; $y++) {
                for ($x = 0; $x -lt $w; $x++) {
                    $pixel = $bmp.GetPixel($x, $y)
                    $a = $pixel.A
                    $r = $pixel.R
                    $g = $pixel.G
                    $b = $pixel.B

                    if ($a -gt 200 -and $r -lt $Threshold -and $g -lt $Threshold -and $b -lt $Threshold) {
                        $totalDark++
                        if (-not $colCounts.ContainsKey($x)) { $colCounts[$x] = 0 }
                        if (-not $rowCounts.ContainsKey($y)) { $rowCounts[$y] = 0 }
                        $colCounts[$x]++
                        $rowCounts[$y]++
                    }
                }
            }

            $bmp.Dispose()
            $img.Dispose()

            if ($totalDark -gt 0) {
                # Detect horizontal lines
                $hLines = @()
                $sortedRows = @($rowCounts.Keys | Sort-Object)
                $start = $null
                foreach ($y in $sortedRows) {
                    if ($rowCounts[$y] -gt 0) {
                        if ($null -eq $start) { $start = $y }
                    } else {
                        if ($null -ne $start) {
                            $length = $y - $start
                            if ($length -ge 5) {
                                $hLines += [PSCustomObject]@{
                                    Start = $start
                                    End = $y - 1
                                    Length = $length
                                    AvgDark = [math]::Round(($sortedRows | Where-Object { $_ -ge $start -and $_ -lt $y } | ForEach-Object { $rowCounts[$_] } | Measure-Object -Average).Average, 1)
                                }
                            }
                            $start = $null
                        }
                    }
                }

                # Detect vertical lines
                $vLines = @()
                $sortedCols = @($colCounts.Keys | Sort-Object)
                $start = $null
                foreach ($x in $sortedCols) {
                    if ($colCounts[$x] -gt 0) {
                        if ($null -eq $start) { $start = $x }
                    } else {
                        if ($null -ne $start) {
                            $length = $x - $start
                            if ($length -ge 5) {
                                $vLines += [PSCustomObject]@{
                                    Start = $start
                                    End = $x - 1
                                    Length = $length
                                    AvgDark = [math]::Round(($sortedCols | Where-Object { $_ -ge $start -and $_ -lt $x } | ForEach-Object { $colCounts[$_] } | Measure-Object -Average).Average, 1)
                                }
                            }
                            $start = $null
                        }
                    }
                }

                $significantHLines = $hLines | Where-Object { $_.Length -ge 10 -or $_.AvgDark -gt 20 }
                $significantVLines = $vLines | Where-Object { $_.Length -ge 10 -or $_.AvgDark -gt 20 }

                if ($significantHLines.Count -gt 0 -or $significantVLines.Count -gt 0) {
                    Write-Host "  Frame $i : $totalDark dark pixels, W=$w H=$h" -ForegroundColor White
                    if ($significantHLines.Count -gt 0) {
                        Write-Host "    H-lines: $($significantHLines.Count)" -ForegroundColor Red
                        foreach ($line in ($significantHLines | Select-Object -First 3)) {
                            Write-Host "      y=$($line.Start)-$($line.End), len=$($line.Length), avg=$($line.AvgDark)" -ForegroundColor Gray
                        }
                    }
                    if ($significantVLines.Count -gt 0) {
                        Write-Host "    V-lines: $($significantVLines.Count)" -ForegroundColor Red
                        foreach ($line in ($significantVLines | Select-Object -First 3)) {
                            Write-Host "      x=$($line.Start)-$($line.End), len=$($line.Length), avg=$($line.AvgDark)" -ForegroundColor Gray
                        }
                    }
                } else {
                    Write-Host "  Frame $i : $totalDark dark pixels - OK" -ForegroundColor Green
                }
            } else {
                Write-Host "  Frame $i : No dark pixels - OK" -ForegroundColor Green
            }
        }
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Analysis complete!" -ForegroundColor Cyan
Write-Host "To remove lines, run the batch file:" -ForegroundColor White
Write-Host "  scripts\run_remove_lines.bat" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
