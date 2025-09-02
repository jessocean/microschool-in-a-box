import requests
import os
from time import sleep

# URLs for the CDE Private School data files
urls = {
    '2021-22': 'https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2122.xlsx',
    '2022-23': 'https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2223.xlsx', 
    '2023-24': 'https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2324.xlsx',
    '2024-25': 'https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata2425.xlsx'
}

# Headers to simulate browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

print("Downloading CDE Private School data files...")

for year, url in urls.items():
    filename = f"cde_private_schools_{year.replace('-', '_')}.xlsx"
    print(f"Downloading {year} data...")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Check if we got an actual Excel file
        content_type = response.headers.get('content-type', '')
        if 'html' in content_type:
            print(f"  Warning: Got HTML response for {year}, likely blocked by captcha")
            with open(f"error_{filename}.html", 'wb') as f:
                f.write(response.content)
            continue
            
        # Save the file
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content)
        print(f"  Successfully downloaded {filename} ({file_size:,} bytes)")
        
        # Brief delay between downloads
        sleep(2)
        
    except requests.RequestException as e:
        print(f"  Error downloading {year}: {e}")

print("Download complete!")