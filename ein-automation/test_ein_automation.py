#!/usr/bin/env python3
"""
Test version of EIN automation without GUI components
"""

import json
import time
import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ein_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EINAutomationTest:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        
    def load_data(self):
        """Load data from ein_data.json"""
        try:
            with open('ein_data.json', 'r') as f:
                data = json.load(f)
            logger.info("Data loaded successfully from ein_data.json")
            return data
        except FileNotFoundError:
            logger.error("ein_data.json file not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in ein_data.json: {e}")
            raise
    
    def show_data_summary(self):
        """Show data summary in console"""
        print("\\n" + "="*50)
        print("EIN APPLICATION DATA LOADED:")
        print("="*50)
        print(f"Business Name: {self.data['business_info']['legal_name']}")
        print(f"Entity Type: {self.data['entity_info']['entity_type']}")
        print(f"Responsible Party: {self.data['responsible_party']['name']}")
        print(f"Business Address: {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']}")
        print("="*50)
        
        # Ask for confirmation
        response = input("\\nProceed with test? (y/N): ").lower().strip()
        return response == 'y'
    
    async def check_site_availability(self):
        """Check if IRS EIN site is accessible"""
        urls_to_check = [
            "https://sa.www4.irs.gov/applyein/",
            "https://sa.www4.irs.gov/modiein/individual/index.jsp"
        ]
        
        for url in urls_to_check:
            try:
                logger.info(f"Checking availability of {url}")
                response = await self.page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                if response.status == 200:
                    logger.info(f"✓ Site accessible at {url}")
                    return True, url
                elif response.status == 503:
                    logger.warning(f"⚠ Site maintenance (503) at {url}")
                    continue
                elif response.status == 403:
                    logger.warning(f"⚠ Access forbidden (403) at {url} - trying next URL")
                    continue
                else:
                    logger.warning(f"⚠ Unexpected status {response.status} at {url}")
                    continue
                    
            except PlaywrightTimeoutError:
                logger.warning(f"⚠ Timeout accessing {url}")
                continue
            except Exception as e:
                logger.warning(f"⚠ Error accessing {url}: {e}")
                continue
        
        logger.error("✗ All URLs failed - site appears to be down")
        return False, None
    
    async def setup_browser(self):
        """Setup browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        # Launch browser with realistic settings
        self.browser = await playwright.chromium.launch(
            headless=False,  # Always visible for testing
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with realistic user agent
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768},
            locale='en-US'
        )
        
        # Disable automation detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        
        # Set realistic navigation behavior
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        logger.info("✓ Browser setup complete")
    
    async def test_navigation(self):
        """Test navigation to EIN application"""
        logger.info("Testing navigation to EIN application...")
        
        available, working_url = await self.check_site_availability()
        
        if not available:
            print("\\n✗ SITE UNAVAILABLE - Cannot proceed with test")
            print("The IRS EIN application site appears to be down.")
            print("Try again later or check https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online")
            return False
        
        print(f"\\n✓ SITE ACCESSIBLE at {working_url}")
        print("Browser should now be open showing the IRS EIN application")
        print("You can manually test the form fields from here.")
        
        # Take a screenshot
        await self.page.screenshot(path=f'screenshots/test_navigation_{int(time.time())}.png')
        logger.info("Screenshot saved to screenshots folder")
        
        return True
    
    async def run_test(self):
        """Main test workflow"""
        try:
            # Show data summary and get confirmation
            if not self.show_data_summary():
                logger.info("Test cancelled by user")
                return False
            
            print("\\nSetting up browser...")
            await self.setup_browser()
            
            print("Testing site accessibility...")
            success = await self.test_navigation()
            
            if success:
                print("\\n" + "="*50)
                print("TEST RESULTS:")
                print("="*50)
                print("✓ Data loading: SUCCESS")
                print("✓ Browser setup: SUCCESS") 
                print("✓ Site access: SUCCESS")
                print("✓ Screenshot saved")
                print("="*50)
                print("\\nBrowser left open for manual testing.")
                print("Press Enter to close and finish test...")
                input()
            
            return success
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"\\n✗ TEST FAILED: {e}")
            return False
        finally:
            if self.browser:
                print("Closing browser...")
                await self.browser.close()

def main():
    """Main entry point"""
    print("EIN Automation Test Script")
    print("="*30)
    
    test = EINAutomationTest()
    
    try:
        result = asyncio.run(test.run_test())
        if result:
            print("\\n✓ Test completed successfully!")
        else:
            print("\\n✗ Test failed or was cancelled")
    except KeyboardInterrupt:
        print("\\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\\n✗ Unexpected error: {e}")

if __name__ == "__main__":
    main()