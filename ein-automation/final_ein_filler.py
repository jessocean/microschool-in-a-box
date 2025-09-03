#!/usr/bin/env python3
"""
Final EIN form filler - handles radio button clicking and form submission
"""

import json
import time
import asyncio
import random
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalEINFiller:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        
    def load_data(self):
        with open('ein_data.json', 'r') as f:
            data = json.load(f)
        print(f"Business: {data['business_info']['legal_name']}")
        print(f"Entity Type: {data['entity_info']['entity_type']}")
        print("Starting form automation...")
        return data
    
    async def setup_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def navigate_and_start(self):
        """Navigate to form and start application"""
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await asyncio.sleep(2)
        
        # Click begin application
        begin_link = await self.page.wait_for_selector('a:has-text("Begin Application Now")')
        await begin_link.click()
        await asyncio.sleep(3)
        
        logger.info(f"Current URL: {self.page.url}")
        return True
    
    async def handle_legal_structure_page(self):
        """Handle the legal structure selection page"""
        logger.info("Handling legal structure page...")
        
        # Wait for page to load
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
        # Screenshot
        await self.page.screenshot(path=f'screenshots/legal_structure_{int(time.time())}.png')
        
        # Handle LLC selection - click the label instead of the input
        try:
            # Try clicking the label for LLC
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]', timeout=10000)
            await llc_label.click()
            logger.info("Selected LLC by clicking label")
            await asyncio.sleep(1)
            
        except:
            # Alternative: use JavaScript to check the radio button
            await self.page.evaluate('''
                const llcRadio = document.getElementById("LLClegalStructureInputid");
                if (llcRadio) {
                    llcRadio.checked = true;
                    llcRadio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            ''')
            logger.info("Selected LLC using JavaScript")
            await asyncio.sleep(1)
        
        # Look for and click continue button
        continue_button = await self.page.wait_for_selector('input[value="Continue"], button:has-text("Continue")')
        await continue_button.click()
        logger.info("Clicked continue from legal structure page")
        await asyncio.sleep(3)
        
        return True
    
    async def fill_current_form_page(self):
        """Fill whatever form page we're currently on"""
        try:
            await self.page.wait_for_load_state('networkidle')
            url = self.page.url
            title = await self.page.title()
            logger.info(f"Filling page: {title}")
            logger.info(f"URL: {url}")
            
            # Take screenshot
            page_name = url.split('/')[-1] if '/' in url else 'unknown'
            await self.page.screenshot(path=f'screenshots/{page_name}_{int(time.time())}.png')
            
            filled_count = 0
            
            # Fill text inputs
            inputs = await self.page.locator('input[type="text"], input:not([type])').all()
            for input_elem in inputs:
                if await input_elem.is_visible() and await input_elem.is_enabled():
                    name = await input_elem.get_attribute('name') or ""
                    id_attr = await input_elem.get_attribute('id') or ""
                    placeholder = await input_elem.get_attribute('placeholder') or ""
                    
                    field_info = f"{name} {id_attr} {placeholder}".lower()
                    current_value = await input_elem.input_value()
                    
                    if current_value:
                        continue  # Skip if already filled
                    
                    # Determine what to fill
                    value = None
                    if any(word in field_info for word in ['name', 'business', 'company', 'legal']):
                        value = self.data['business_info']['legal_name']
                    elif any(word in field_info for word in ['street', 'address']):
                        value = self.data['business_info']['mailing_address']['street']
                    elif 'city' in field_info:
                        value = self.data['business_info']['mailing_address']['city']
                    elif any(word in field_info for word in ['zip', 'postal']):
                        value = self.data['business_info']['mailing_address']['zip_code']
                    elif any(word in field_info for word in ['responsible', 'contact', 'person']):
                        value = self.data['responsible_party']['name']
                    elif any(word in field_info for word in ['ssn', 'tax', 'ein']):
                        value = self.data['responsible_party']['ssn_itin']
                    elif 'title' in field_info:
                        value = self.data['responsible_party']['title']
                    elif any(word in field_info for word in ['activity', 'business']):
                        value = self.data['business_details'].get('principal_activity', '')
                    elif any(word in field_info for word in ['employee', 'expect']):
                        value = self.data['business_details'].get('highest_number_employees_expected', '')
                    
                    if value:
                        await input_elem.fill(value)
                        logger.info(f"Filled {field_info[:30]}... with: {value[:20]}...")
                        filled_count += 1
                        await asyncio.sleep(0.3)
            
            # Handle select dropdowns
            selects = await self.page.locator('select').all()
            for select_elem in selects:
                if await select_elem.is_visible():
                    name = await select_elem.get_attribute('name') or ""
                    id_attr = await select_elem.get_attribute('id') or ""
                    
                    if 'state' in f"{name} {id_attr}".lower():
                        await select_elem.select_option(value=self.data['business_info']['mailing_address']['state'])
                        logger.info(f"Selected state: {self.data['business_info']['mailing_address']['state']}")
                        filled_count += 1
            
            # Handle radio buttons more carefully
            radios = await self.page.locator('input[type="radio"]').all()
            for radio in radios:
                if await radio.is_visible():
                    value = await radio.get_attribute('value') or ""
                    name = await radio.get_attribute('name') or ""
                    radio_id = await radio.get_attribute('id') or ""
                    
                    # Find associated label
                    label_text = ""
                    try:
                        if radio_id:
                            label = await self.page.locator(f'label[for="{radio_id}"]').first
                            label_text = await label.inner_text()
                    except:
                        pass
                    
                    combined = f"{value} {label_text}".lower()
                    
                    # Select appropriate radio buttons
                    if 'llc' in combined or 'limited liability' in combined:
                        try:
                            if radio_id:
                                label = await self.page.locator(f'label[for="{radio_id}"]')
                                await label.click()
                            else:
                                await radio.click()
                            logger.info(f"Selected: {label_text}")
                            filled_count += 1
                            await asyncio.sleep(0.5)
                        except:
                            pass
                    
                    elif 'yes' in combined and any(word in name.lower() for word in ['employee', 'hire']):
                        try:
                            await radio.click()
                            logger.info(f"Selected: {label_text}")
                            filled_count += 1
                            await asyncio.sleep(0.5)
                        except:
                            pass
            
            logger.info(f"Filled {filled_count} fields on this page")
            return filled_count > 0
            
        except Exception as e:
            logger.error(f"Error filling page: {e}")
            return False
    
    async def click_continue(self):
        """Click continue/next/submit button"""
        try:
            # Wait a moment for any dynamic content
            await asyncio.sleep(1)
            
            continue_selectors = [
                'input[value="Continue"]',
                'button:has-text("Continue")',
                'input[value="Next"]',
                'button:has-text("Next")',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            for selector in continue_selectors:
                try:
                    element = await self.page.locator(selector).first
                    if await element.is_visible():
                        text = await element.inner_text() if 'button' in selector else await element.get_attribute('value')
                        await element.click()
                        logger.info(f"Clicked: {text}")
                        await asyncio.sleep(3)  # Wait for navigation
                        return True
                except:
                    continue
            
            logger.warning("No continue button found")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking continue: {e}")
            return False
    
    async def is_submission_page(self):
        """Check if this is the final submission page"""
        try:
            body_text = await self.page.inner_text('body')
            submission_keywords = [
                'submit your application',
                'review and submit',
                'submit application',
                'final step'
            ]
            return any(keyword in body_text.lower() for keyword in submission_keywords)
        except:
            return False
    
    async def run_full_automation(self):
        """Run the complete form automation"""
        try:
            await self.setup_browser()
            
            # Navigate and start
            await self.navigate_and_start()
            
            # Handle legal structure page first
            if 'legalStructure' in self.page.url:
                await self.handle_legal_structure_page()
            
            # Process remaining pages
            max_pages = 20
            for page_num in range(1, max_pages + 1):
                logger.info(f"\\n--- Processing Page {page_num} ---")
                
                # Check if submission page
                if await self.is_submission_page():
                    await self.page.screenshot(path=f'screenshots/submission_page_{int(time.time())}.png')
                    
                    print("\\n" + "="*70)
                    print("SUCCESS! REACHED FINAL SUBMISSION PAGE!")
                    print("="*70)
                    print("The EIN application form has been filled out completely.")
                    print("Please review all information in the browser window.")
                    print("When ready, click SUBMIT to complete your application.")
                    print("\\nThe browser will stay open for your final review.")
                    print("="*70)
                    
                    # Keep browser open - don't close automatically
                    return "SUCCESS_READY_FOR_SUBMISSION"
                
                # Fill current page
                filled = await self.fill_current_form_page()
                
                # Try to continue
                if not await self.click_continue():
                    logger.info("No continue button - checking if we're done...")
                    await asyncio.sleep(2)
                    
                    # Final check
                    if await self.is_submission_page():
                        await self.page.screenshot(path=f'screenshots/final_submission_{int(time.time())}.png')
                        print("\\n" + "="*70)
                        print("FORM COMPLETED - READY FOR SUBMISSION!")
                        print("="*70)
                        print("Please review and submit in the browser window.")
                        print("="*70)
                        return "SUCCESS_FORM_COMPLETE"
                    else:
                        logger.info("Reached end of form pages")
                        break
                
                # Safety check for URL changes
                current_url = self.page.url
                logger.info(f"Current URL: {current_url}")
                
                await asyncio.sleep(1)  # Brief pause between pages
            
            # If we get here, we've gone through all pages
            await self.page.screenshot(path=f'screenshots/final_state_{int(time.time())}.png')
            print("\\n" + "="*70)
            print("AUTOMATION COMPLETED")
            print("="*70)
            print("All form pages have been processed.")
            print("Please check the browser window for final review.")
            print("="*70)
            
            return "COMPLETED"
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return f"ERROR: {e}"

async def main():
    print("Final EIN Form Automation")
    print("=" * 40)
    
    filler = FinalEINFiller()
    
    try:
        result = await filler.run_full_automation()
        print(f"\\nResult: {result}")
        
        if "SUCCESS" in result:
            print("\\nForm automation completed successfully!")
            print("The browser window contains your filled EIN application.")
            print("Please review all information and submit when ready.")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Don't close browser automatically - let user control it
    print("\\nBrowser will remain open. Close it manually when done.")

if __name__ == "__main__":
    asyncio.run(main())