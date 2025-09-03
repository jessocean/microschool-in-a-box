#!/usr/bin/env python3
"""
Auto-fill EIN form - bypasses initial review, focuses on form completion
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

class AutoFillEIN:
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
            logger.info("Data loaded successfully")
            print(f"Business: {data['business_info']['legal_name']}")
            print(f"Entity: {data['entity_info']['entity_type']}")
            print("Proceeding with form automation...")
            return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    async def setup_browser(self):
        """Setup browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--start-maximized'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768},
            locale='en-US'
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        await self.page.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9'})
        
        logger.info("Browser setup complete")
    
    async def human_delay(self, min_ms=200, max_ms=800):
        """Add human-like delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def type_human(self, element, text):
        """Type text with human-like delays"""
        if not text:
            return
        await element.clear()
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.randint(50, 150) / 1000)
    
    async def navigate_to_form(self):
        """Navigate to the EIN application form"""
        logger.info("Navigating to EIN application...")
        
        try:
            # Go to main application URL
            await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
            await self.human_delay(2000, 4000)
            
            # Take screenshot of landing page
            await self.page.screenshot(path=f'screenshots/landing_page_{int(time.time())}.png')
            
            # Look for "Begin Application" button or similar
            begin_selectors = [
                'input[value*="Begin"]',
                'button:has-text("Begin")',
                'a:has-text("Begin")',
                'input[type="submit"][value*="Apply"]',
                'button:has-text("Apply")',
                'a:has-text("Apply")'
            ]
            
            clicked = False
            for selector in begin_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        logger.info(f"Clicking begin button: {selector}")
                        await element.click()
                        await self.human_delay(3000, 5000)
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                # Try direct URL to individual application
                logger.info("Trying direct individual application URL")
                await self.page.goto('https://sa.www4.irs.gov/modiein/individual/index.jsp', timeout=60000)
                await self.human_delay(2000, 4000)
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def fill_current_page(self):
        """Fill out the current form page"""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            await self.human_delay(1000, 2000)
            
            # Take screenshot
            page_num = int(time.time())
            await self.page.screenshot(path=f'screenshots/page_{page_num}.png')
            logger.info(f"Screenshot saved: page_{page_num}.png")
            
            # Get page title to understand which page we're on
            title = await self.page.title()
            url = self.page.url
            logger.info(f"Current page: {title}")
            
            filled_any = False
            
            # Business name fields
            name_selectors = [
                'input[name*="name"]',
                'input[id*="name"]',
                'input[name*="legal"]',
                'input[id*="legal"]',
                'input[name*="entity"]',
                'input[id*="entity"]'
            ]
            
            for selector in name_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            current_value = await element.input_value()
                            if not current_value or current_value.strip() == "":
                                await self.type_human(element, self.data['business_info']['legal_name'])
                                logger.info(f"Filled business name in: {selector}")
                                filled_any = True
                                await self.human_delay(500, 1000)
                                break
                except:
                    continue
            
            # Address fields
            address_data = self.data['business_info']['mailing_address']
            address_mappings = [
                (['street', 'address', 'addr'], address_data['street']),
                (['city'], address_data['city']),
                (['zip', 'postal'], address_data['zip_code'])
            ]
            
            for field_names, value in address_mappings:
                if not value:
                    continue
                    
                for field_name in field_names:
                    selectors = [
                        f'input[name*="{field_name}"]',
                        f'input[id*="{field_name}"]'
                    ]
                    
                    filled_field = False
                    for selector in selectors:
                        try:
                            elements = await self.page.locator(selector).all()
                            for element in elements:
                                if await element.is_visible() and await element.is_enabled():
                                    current_value = await element.input_value()
                                    if not current_value or current_value.strip() == "":
                                        await self.type_human(element, value)
                                        logger.info(f"Filled {field_name}: {value}")
                                        filled_any = True
                                        filled_field = True
                                        await self.human_delay(500, 1000)
                                        break
                            if filled_field:
                                break
                        except:
                            continue
                    if filled_field:
                        break
            
            # State dropdown
            state_selectors = [
                'select[name*="state"]',
                'select[id*="state"]'
            ]
            
            for selector in state_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            await element.select_option(value=address_data['state'])
                            logger.info(f"Selected state: {address_data['state']}")
                            filled_any = True
                            await self.human_delay(500, 1000)
                            break
                except:
                    continue
            
            # Responsible party fields
            rp_data = self.data['responsible_party']
            rp_mappings = [
                (['responsible', 'contact', 'person'], rp_data['name']),
                (['ssn', 'tax', 'id', 'tin'], rp_data['ssn_itin']),
                (['title', 'position'], rp_data['title'])
            ]
            
            for field_names, value in rp_mappings:
                if not value:
                    continue
                    
                for field_name in field_names:
                    selectors = [
                        f'input[name*="{field_name}"]',
                        f'input[id*="{field_name}"]'
                    ]
                    
                    filled_field = False
                    for selector in selectors:
                        try:
                            elements = await self.page.locator(selector).all()
                            for element in elements:
                                if await element.is_visible() and await element.is_enabled():
                                    current_value = await element.input_value()
                                    if not current_value or current_value.strip() == "":
                                        await self.type_human(element, value)
                                        logger.info(f"Filled {field_name}: {value[:10]}...")
                                        filled_any = True
                                        filled_field = True
                                        await self.human_delay(500, 1000)
                                        break
                            if filled_field:
                                break
                        except:
                            continue
                    if filled_field:
                        break
            
            # Entity type selection
            entity_type = self.data['entity_info']['entity_type']
            if entity_type:
                # Try radio buttons first
                radio_selectors = [
                    f'input[type="radio"][value*="{entity_type}"]',
                    f'input[type="radio"][value*="LLC"]' if 'LLC' in entity_type else None,
                    'input[type="radio"]'
                ]
                
                for selector in [s for s in radio_selectors if s]:
                    try:
                        elements = await self.page.locator(selector).all()
                        for element in elements:
                            if await element.is_visible():
                                # Get the label text to see if it matches
                                label_text = ""
                                try:
                                    label = await element.locator('..').locator('label').first
                                    label_text = await label.inner_text()
                                except:
                                    pass
                                
                                if entity_type.lower() in label_text.lower() or 'llc' in label_text.lower():
                                    await element.click()
                                    logger.info(f"Selected entity type: {label_text}")
                                    filled_any = True
                                    await self.human_delay(500, 1000)
                                    break
                    except:
                        continue
                
                # Try dropdown
                dropdown_selectors = [
                    'select[name*="entity"]',
                    'select[id*="entity"]',
                    'select[name*="organization"]'
                ]
                
                for selector in dropdown_selectors:
                    try:
                        elements = await self.page.locator(selector).all()
                        for element in elements:
                            if await element.is_visible():
                                # Try to select by value or text
                                try:
                                    await element.select_option(label=entity_type)
                                    logger.info(f"Selected entity type from dropdown: {entity_type}")
                                    filled_any = True
                                    await self.human_delay(500, 1000)
                                    break
                                except:
                                    # Try selecting LLC option
                                    options = await element.locator('option').all()
                                    for option in options:
                                        option_text = await option.inner_text()
                                        if 'llc' in option_text.lower():
                                            await element.select_option(option_text)
                                            logger.info(f"Selected: {option_text}")
                                            filled_any = True
                                            await self.human_delay(500, 1000)
                                            break
                    except:
                        continue
            
            # Business details
            business_data = self.data['business_details']
            business_mappings = [
                (['activity', 'business', 'purpose'], business_data.get('principal_activity', '')),
                (['product', 'service'], business_data.get('principal_product_or_service', '')),
                (['start', 'date', 'began'], business_data.get('date_business_started', '')),
                (['employee', 'expect'], business_data.get('highest_number_employees_expected', ''))
            ]
            
            for field_names, value in business_mappings:
                if not value:
                    continue
                    
                for field_name in field_names:
                    selectors = [
                        f'input[name*="{field_name}"]',
                        f'input[id*="{field_name}"]',
                        f'textarea[name*="{field_name}"]',
                        f'textarea[id*="{field_name}"]'
                    ]
                    
                    filled_field = False
                    for selector in selectors:
                        try:
                            elements = await self.page.locator(selector).all()
                            for element in elements:
                                if await element.is_visible() and await element.is_enabled():
                                    current_value = await element.input_value() if 'input' in selector else await element.inner_text()
                                    if not current_value or current_value.strip() == "":
                                        await self.type_human(element, str(value))
                                        logger.info(f"Filled {field_name}: {str(value)[:20]}...")
                                        filled_any = True
                                        filled_field = True
                                        await self.human_delay(500, 1000)
                                        break
                            if filled_field:
                                break
                        except:
                            continue
                    if filled_field:
                        break
            
            if filled_any:
                logger.info("Successfully filled form fields on this page")
            else:
                logger.warning("No fillable fields found on this page")
            
            return filled_any
            
        except Exception as e:
            logger.error(f"Error filling page: {e}")
            return False
    
    async def find_and_click_next(self):
        """Find and click next/continue button"""
        next_selectors = [
            'input[value*="Next"]',
            'input[value*="Continue"]',
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'input[type="submit"]',
            'button[type="submit"]',
            'input[value*="Submit"]'
        ]
        
        for selector in next_selectors:
            try:
                elements = await self.page.locator(selector).all()
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        button_text = await element.inner_text() if 'button' in selector else await element.get_attribute('value')
                        logger.info(f"Clicking: {button_text}")
                        await element.click()
                        await self.human_delay(2000, 4000)
                        return True
            except:
                continue
        
        logger.warning("No next button found")
        return False
    
    async def check_if_final_page(self):
        """Check if we're at the final submission page"""
        try:
            page_text = await self.page.inner_text('body')
            final_keywords = [
                'submit application',
                'review and submit', 
                'final submission',
                'confirm and submit',
                'complete application'
            ]
            
            return any(keyword in page_text.lower() for keyword in final_keywords)
        except:
            return False
    
    async def run_automation(self):
        """Main automation workflow"""
        try:
            await self.setup_browser()
            
            if not await self.navigate_to_form():
                print("Failed to navigate to form")
                return False
            
            max_pages = 10
            current_page = 0
            
            while current_page < max_pages:
                current_page += 1
                logger.info(f"Processing page {current_page}")
                
                # Fill current page
                filled = await self.fill_current_page()
                
                # Check if final page
                if await self.check_if_final_page():
                    logger.info("Reached final submission page!")
                    
                    # Take final screenshot
                    await self.page.screenshot(path=f'screenshots/final_form_{int(time.time())}.png')
                    
                    print("\\n" + "="*60)
                    print("FORM FILLING COMPLETE!")
                    print("="*60)
                    print("The EIN application form has been filled out and is ready for review.")
                    print("Please check the browser window to review all filled information.")
                    print("The browser will remain open for your manual review and submission.")
                    print("Screenshots have been saved in the screenshots/ folder.")
                    print("="*60)
                    
                    # Don't close browser - leave it open for user review
                    return True
                
                # Try to go to next page
                if not await self.find_and_click_next():
                    logger.info("No next button found - may have reached end of form")
                    break
                
                await self.human_delay(1000, 2000)
            
            # If we get here, we've processed all pages but may not be at final submission
            print("\\n" + "="*60)
            print("FORM PROCESSING COMPLETE!")
            print("="*60)
            print("All available form pages have been processed.")
            print("Please check the browser window to review and complete submission.")
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            print(f"Error: {e}")
            return False

async def main():
    print("EIN Form Auto-Fill Starting...")
    print("="*40)
    
    automation = AutoFillEIN()
    
    try:
        success = await automation.run_automation()
        if success:
            print("\\nAutomation completed successfully!")
            print("Check the browser window for the filled form.")
        else:
            print("\\nAutomation encountered issues.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())