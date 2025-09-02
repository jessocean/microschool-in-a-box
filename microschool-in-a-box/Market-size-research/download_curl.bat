@echo off
echo CDE Private School Data Download - Advanced Method
echo ================================================

set "REFERER=https://www.cde.ca.gov/ds/si/ps/"
set "USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

echo.
echo Method 1: Using curl with session simulation...

REM First, establish a session by visiting the main page
echo Establishing session...
curl -s -L -c cookies.txt -b cookies.txt ^
  -H "User-Agent: %USER_AGENT%" ^
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" ^
  -H "Accept-Language: en-US,en;q=0.5" ^
  -H "Accept-Encoding: gzip, deflate" ^
  -H "DNT: 1" ^
  -H "Connection: keep-alive" ^
  -H "Upgrade-Insecure-Requests: 1" ^
  "%REFERER%" > nul

timeout /t 3 > nul

REM Now try to download each file
echo.
echo Downloading 2021-22 data...
curl -L -c cookies.txt -b cookies.txt ^
  -H "User-Agent: %USER_AGENT%" ^
  -H "Referer: %REFERER%" ^
  -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*" ^
  -o "cde_2021_22.xlsx" ^
  "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2122.xlsx"

timeout /t 4 > nul

echo Downloading 2022-23 data...
curl -L -c cookies.txt -b cookies.txt ^
  -H "User-Agent: %USER_AGENT%" ^
  -H "Referer: %REFERER%" ^
  -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*" ^
  -o "cde_2022_23.xlsx" ^
  "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2223.xlsx"

timeout /t 4 > nul

echo Downloading 2023-24 data...
curl -L -c cookies.txt -b cookies.txt ^
  -H "User-Agent: %USER_AGENT%" ^
  -H "Referer: %REFERER%" ^
  -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*" ^
  -o "cde_2023_24.xlsx" ^
  "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2324.xlsx"

timeout /t 4 > nul

echo Downloading 2024-25 data...
curl -L -c cookies.txt -b cookies.txt ^
  -H "User-Agent: %USER_AGENT%" ^
  -H "Referer: %REFERER%" ^
  -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*" ^
  -o "cde_2024_25.xlsx" ^
  "https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2425.xlsx"

echo.
echo Checking downloaded files...
echo ========================

for %%f in (cde_*.xlsx) do (
  echo File: %%f
  for %%A in (%%f) do (
    if %%~zA lss 50000 (
      echo   Size: %%~zA bytes - LIKELY BLOCKED
      findstr /i "html\|captcha\|blocked" "%%f" > nul && echo   Contains HTML - definitely blocked
    ) else (
      echo   Size: %%~zA bytes - SUCCESS
    )
  )
  echo.
)

echo.
echo If all files show as blocked, try these alternatives:
echo 1. Download manually in your web browser
echo 2. Use a VPN or different network connection  
echo 3. Contact CDE: privateschools@cde.ca.gov
echo 4. Try again during off-peak hours

del cookies.txt 2>nul
pause