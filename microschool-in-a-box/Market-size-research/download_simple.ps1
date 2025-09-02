# Simple PowerShell download script for CDE data
param(
    [switch]$UseWget = $false
)

$urls = @(
    @{Year = "2021-22"; Url = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2122.xlsx"}
    @{Year = "2022-23"; Url = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2223.xlsx"}
    @{Year = "2023-24"; Url = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2324.xlsx"}
    @{Year = "2024-25"; Url = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2425.xlsx"}
)

Write-Host "CDE Private School Data Downloader" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$successCount = 0

foreach ($item in $urls) {
    $year = $item.Year
    $url = $item.Url
    $filename = "cde_data_$($year.Replace('-','_')).xlsx"
    
    Write-Host "`nDownloading $year..." -ForegroundColor Cyan
    
    try {
        # Method 1: Use Invoke-WebRequest with minimal headers
        $webClient = New-Object System.Net.WebClient
        $webClient.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        Write-Host "  Attempting download..." -ForegroundColor Yellow
        $webClient.DownloadFile($url, $filename)
        
        # Check file
        if (Test-Path $filename) {
            $size = (Get-Item $filename).Length
            
            # Check if it's HTML (indicates blocking)
            $firstBytes = [System.IO.File]::ReadAllBytes($filename) | Select-Object -First 100
            $firstText = [System.Text.Encoding]::UTF8.GetString($firstBytes)
            
            if ($firstText -like "*html*" -or $size -lt 20000) {
                Write-Host "  File appears to be HTML/blocked ($size bytes)" -ForegroundColor Red
                Move-Item $filename "blocked_$filename.html" -Force
            } else {
                Write-Host "  Success! Downloaded $($size.ToString('N0')) bytes" -ForegroundColor Green
                $successCount++
            }
        }
        
        $webClient.Dispose()
        Start-Sleep -Seconds 2
        
    } catch {
        Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=================================" -ForegroundColor Green
Write-Host "Results: $successCount/$($urls.Count) files downloaded successfully" -ForegroundColor $(if ($successCount -gt 0) { "Green" } else { "Red" })

if ($successCount -eq 0) {
    Write-Host "`nTroubleshooting suggestions:" -ForegroundColor Yellow
    Write-Host "1. The site may be using advanced bot detection" -ForegroundColor White
    Write-Host "2. Try downloading manually from your web browser" -ForegroundColor White  
    Write-Host "3. Check if you need to access from a different IP/network" -ForegroundColor White
    Write-Host "4. Contact CDE directly: privateschools@cde.ca.gov" -ForegroundColor White
}