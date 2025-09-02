import requests
import time
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    """Create a session with retry strategy and realistic headers"""
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Realistic browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    return session

def download_with_session(session, url, filename):
    """Download a file using the session"""
    print(f"Downloading {filename}...")
    
    try:
        # First, visit the main page to establish session
        main_page = session.get('https://www.cde.ca.gov/ds/si/ps/', timeout=30)
        time.sleep(random.uniform(2, 5))  # Random delay
        
        # Then try to download the file
        response = session.get(url, timeout=60)
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('content-type', '')
            
            if 'html' in content_type.lower():
                print(f"  Got HTML response (likely blocked) for {filename}")
                with open(f"blocked_{filename}.html", 'wb') as f:
                    f.write(response.content)
                return False
            
            # Check if it's actually an Excel file
            if len(response.content) < 50000:  # Files should be much larger
                print(f"  File too small ({len(response.content)} bytes), likely not the actual data")
                return False
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"  Success! Downloaded {len(response.content):,} bytes")
            return True
            
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    return False

def try_alternative_urls():
    """Try different URL patterns that might work"""
    base_patterns = [
        'https://www.cde.ca.gov/ds/si/ps/documents/privateschooldata{year}.xlsx',
        'https://cde.ca.gov/ds/si/ps/documents/privateschooldata{year}.xlsx',
        'https://www.cde.ca.gov/ds/si/ps/privateschooldata{year}.xlsx',
    ]
    
    years = ['2122', '2223', '2324', '2425']
    session = create_session()
    
    for pattern in base_patterns:
        print(f"\nTrying URL pattern: {pattern}")
        success_count = 0
        
        for year in years:
            url = pattern.format(year=year)
            filename = f"cde_data_{year}.xlsx"
            
            if download_with_session(session, url, filename):
                success_count += 1
            
            # Random delay between downloads
            time.sleep(random.uniform(3, 8))
        
        if success_count > 0:
            print(f"Pattern worked for {success_count} files!")
            return True
        
        # Longer delay between trying different patterns
        time.sleep(random.uniform(5, 10))
    
    return False

if __name__ == "__main__":
    print("Attempting to download CDE Private School data files...")
    print("Using session-based approach with realistic browser behavior...")
    
    success = try_alternative_urls()
    
    if not success:
        print("\nAutomatic download failed. Alternative approaches:")
        print("1. Manual download: Visit https://www.cde.ca.gov/ds/si/ps/ in your browser")
        print("2. Contact CDE directly at privateschools@cde.ca.gov")
        print("3. Use a VPN or different network")
        print("4. Try downloading during off-peak hours")