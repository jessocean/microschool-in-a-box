#!/usr/bin/env python3
"""
Simple test of EIN automation - non-interactive
"""

import json
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import time

class SimpleEINTest:
    def __init__(self):
        self.data = self.load_data()
        
    def load_data(self):
        """Load data from ein_data.json"""
        try:
            with open('ein_data.json', 'r') as f:
                data = json.load(f)
            print("Data loaded successfully from ein_data.json")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def show_data_summary(self):
        """Show data summary"""
        print("\\n" + "="*50)
        print("EIN APPLICATION DATA LOADED:")
        print("="*50)
        print(f"Business Name: {self.data['business_info']['legal_name']}")
        print(f"Entity Type: {self.data['entity_info']['entity_type']}")
        print(f"Responsible Party: {self.data['responsible_party']['name']}")
        print(f"City, State: {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']}")
        print("="*50)
    
    async def test_site_access(self):
        """Test if we can access the IRS site"""
        print("\\nTesting site access...")
        
        playwright = await async_playwright().start()
        
        try:
            # Launch browser
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Test URLs
            urls = [
                "https://sa.www4.irs.gov/applyein/",
                "https://sa.www4.irs.gov/modiein/individual/index.jsp",
                "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online"
            ]
            
            success_count = 0
            for i, url in enumerate(urls, 1):
                try:
                    print(f"Testing URL {i}: {url}")
                    response = await page.goto(url, timeout=30000)
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        print("  Result: SUCCESS")
                        success_count += 1
                        
                        # Take screenshot
                        screenshot_path = f'screenshots/test_url_{i}_{int(time.time())}.png'
                        await page.screenshot(path=screenshot_path)
                        print(f"  Screenshot saved: {screenshot_path}")
                        
                        # Wait a moment to see the page
                        await asyncio.sleep(3)
                        
                    elif response.status == 403:
                        print("  Result: BLOCKED (403 Forbidden)")
                    elif response.status == 503:
                        print("  Result: MAINTENANCE (503 Service Unavailable)")
                    else:
                        print(f"  Result: UNEXPECTED STATUS {response.status}")
                        
                except PlaywrightTimeoutError:
                    print("  Result: TIMEOUT")
                except Exception as e:
                    print(f"  Result: ERROR - {e}")
                
                print()
                await asyncio.sleep(2)  # Brief pause between tests
            
            print(f"\\nTEST SUMMARY:")
            print(f"URLs tested: {len(urls)}")
            print(f"Successful: {success_count}")
            print(f"Failed: {len(urls) - success_count}")
            
            if success_count > 0:
                print("\\nAt least one URL is working! The automation should be able to proceed.")
            else:
                print("\\nAll URLs failed. The IRS site may be down or blocking automated access.")
            
            print("\\nBrowser will stay open for 10 seconds for manual inspection...")
            await asyncio.sleep(10)
            
            await browser.close()
            return success_count > 0
            
        except Exception as e:
            print(f"Test failed: {e}")
            return False
        finally:
            await playwright.stop()

async def main():
    print("EIN Automation Simple Test")
    print("=" * 30)
    
    try:
        test = SimpleEINTest()
        test.show_data_summary()
        
        result = await test.test_site_access()
        
        if result:
            print("\\nTEST PASSED: Ready for full automation!")
        else:
            print("\\nTEST FAILED: Site access issues detected")
            
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())