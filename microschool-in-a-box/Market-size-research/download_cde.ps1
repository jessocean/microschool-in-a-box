# PowerShell script to download CDE Private School data files
# Bypasses basic bot detection with realistic browser behavior

$urls = @{
    "2021-22" = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2122.xlsx"
    "2022-23" = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2223.xlsx" 
    "2023-24" = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2324.xlsx"
    "2024-25" = "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2425.xlsx"
}

# Create a web session with realistic headers
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Set realistic headers
$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    "Accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    "Accept-Language" = "en-US,en;q=0.5"
    "Accept-Encoding" = "gzip, deflate, br"
    "DNT" = "1"
    "Connection" = "keep-alive"
    "Upgrade-Insecure-Requests" = "1"
}

Write-Host "Downloading CDE Private School data files..." -ForegroundColor Green

# First, visit the main page to establish session
try {
    Write-Host "Establishing session with CDE website..." -ForegroundColor Yellow
    $mainPage = Invoke-WebRequest -Uri "https://www.cde.ca.gov/ds/si/ps/" -WebSession $session -Headers $headers -TimeoutSec 30
    Start-Sleep -Seconds 3
    Write-Host "Session established successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not establish session, proceeding anyway..." -ForegroundColor Yellow
}

$successCount = 0

foreach ($year in $urls.Keys) {
    $url = $urls[$year]
    $filename = "cde_private_schools_$($year.Replace('-','_')).xlsx"
    
    Write-Host "`nDownloading $year data..." -ForegroundColor Cyan
    
    try {
        # Add random delay to appear more human
        $delay = Get-Random -Minimum 2 -Maximum 6
        Start-Sleep -Seconds $delay
        
        $response = Invoke-WebRequest -Uri $url -WebSession $session -Headers $headers -TimeoutSec 60 -OutFile $filename
        
        # Check file size
        $fileInfo = Get-Item $filename
        $fileSize = $fileInfo.Length
        
        if ($fileSize -lt 50000) {
            Write-Host "  Warning: File is only $fileSize bytes, likely not the actual data" -ForegroundColor Red
            
            # Check if it's HTML (blocked)
            $content = Get-Content $filename -Raw -Encoding UTF8 | Select-Object -First 1000
            if ($content -like "*html*" -or $content -like "*captcha*") {
                Write-Host "  File appears to be HTML/captcha page, download was blocked" -ForegroundColor Red
                Rename-Item $filename "blocked_$filename.html"
                continue
            }
        } else {
            Write-Host "  Successfully downloaded $filename ($($fileSize.ToString('N0')) bytes)" -ForegroundColor Green
            $successCount++
        }
        
    } catch {
        Write-Host "  Error downloading $year data: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nDownload Summary:" -ForegroundColor Yellow
Write-Host "Successfully downloaded: $successCount out of $($urls.Count) files" -ForegroundColor $(if ($successCount -gt 0) { "Green" } else { "Red" })

if ($successCount -eq 0) {
    Write-Host "`nAlternative approaches:" -ForegroundColor Yellow
    Write-Host "1. Try running this script from a different network/VPN" -ForegroundColor White
    Write-Host "2. Download manually from: https://www.cde.ca.gov/ds/si/ps/" -ForegroundColor White
    Write-Host "3. Contact CDE at: privateschools@cde.ca.gov or 916-319-0317" -ForegroundColor White
    Write-Host "4. Try during off-peak hours (early morning/late evening)" -ForegroundColor White
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")