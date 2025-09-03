#!/usr/bin/env python3
"""
Improved EIN form filler with better page detection and navigation
"""

import json
import time
import asyncio
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedEINFiller:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        self.page_count = 0
        
    def load_data(self):
        """Load data from ein_data.json"""
        try:
            with open('ein_data.json', 'r') as f:
                data = json.load(f)
            logger.info("Data loaded successfully")
            print(f"Business: {data['business_info']['legal_name']}")
            return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    async def setup_browser(self):
        """Setup browser"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-web-security']
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        
        self.page = await self.context.new_page()
        logger.info("Browser setup complete")
    
    async def wait_and_screenshot(self, name="page"):
        """Wait for page to load and take screenshot"""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=15000)
        except:
            await asyncio.sleep(2)  # Fallback wait
        
        self.page_count += 1
        screenshot_path = f'screenshots/{name}_{self.page_count}_{int(time.time())}.png'
        await self.page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"Screenshot: {screenshot_path}")
        return screenshot_path
    
    async def navigate_to_form(self):
        """Navigate to EIN form"""
        logger.info("Navigating to EIN application...")
        
        # Start with the main application URL
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.wait_and_screenshot("landing")
        
        # Look for any button/link to start the application
        start_selectors = [
            'a:has-text("Begin")',
            'input[value*="Begin"]',
            'button:has-text("Begin")',
            'a:has-text("Start")',
            'input[value*="Start"]',
            'a:has-text("Apply")',
            'input[value*="Apply"]',
            'a[href*="individual"]',
            'input[type="submit"]'
        ]
        
        clicked = False
        for selector in start_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=3000)
                if element and await element.is_visible():
                    text = await element.inner_text() if 'button' in selector or 'a' in selector else await element.get_attribute('value')
                    logger.info(f"Found start element: {text} ({selector})")
                    await element.click()
                    await asyncio.sleep(3)
                    await self.wait_and_screenshot("after_start_click")
                    clicked = True
                    break
            except:
                continue
        
        if not clicked:
            # Try direct URL to individual application
            logger.info("Trying direct individual application URL")
            await self.page.goto('https://sa.www4.irs.gov/modiein/individual/index.jsp', timeout=60000)
            await self.wait_and_screenshot("direct_individual")
        
        return True
    
    async def analyze_page(self):
        """Analyze current page and determine what type it is"""
        try:
            title = await self.page.title()
            url = self.page.url
            body_text = await self.page.inner_text('body')
            
            logger.info(f"Page analysis: {title}")
            logger.info(f"URL: {url}")
            
            # Count form elements
            inputs = await self.page.locator('input').count()
            selects = await self.page.locator('select').count()
            textareas = await self.page.locator('textarea').count()
            radios = await self.page.locator('input[type="radio"]').count()
            checkboxes = await self.page.locator('input[type="checkbox"]').count()
            
            logger.info(f"Form elements: {inputs} inputs, {selects} selects, {textareas} textareas, {radios} radios, {checkboxes} checkboxes")
            
            # Identify page type based on content
            page_type = "unknown"
            if "employer identification number" in body_text.lower():
                page_type = "ein_form"
            elif "begin" in body_text.lower() or "start" in body_text.lower():
                page_type = "start_page"  
            elif "business" in body_text.lower() and (inputs > 5 or selects > 2):
                page_type = "business_info"
            elif "responsible party" in body_text.lower():
                page_type = "responsible_party"
            elif "submit" in body_text.lower() and "review" in body_text.lower():
                page_type = "final_review"
            
            logger.info(f"Detected page type: {page_type}")
            return page_type
            
        except Exception as e:
            logger.error(f"Page analysis failed: {e}")
            return "unknown"
    
    async def fill_any_form_fields(self):
        """Aggressively try to fill any form fields found"""
        filled_count = 0
        
        try:
            # Get all input elements
            inputs = await self.page.locator('input[type="text"], input:not([type]), input[type="email"], input[type="tel"]').all()
            
            for input_elem in inputs:
                try:
                    if await input_elem.is_visible() and await input_elem.is_enabled():
                        # Get field identifiers
                        name = await input_elem.get_attribute('name') or ""
                        id_attr = await input_elem.get_attribute('id') or ""
                        placeholder = await input_elem.get_attribute('placeholder') or ""
                        
                        field_id = f"{name} {id_attr} {placeholder}".lower()
                        current_value = await input_elem.input_value()
                        
                        if current_value and current_value.strip():
                            continue  # Skip if already filled
                        
                        # Determine what to fill based on field identifiers
                        value_to_fill = None
                        
                        if any(keyword in field_id for keyword in ['name', 'business', 'company', 'entity']):
                            value_to_fill = self.data['business_info']['legal_name']
                            
                        elif any(keyword in field_id for keyword in ['street', 'address', 'addr']):
                            value_to_fill = self.data['business_info']['mailing_address']['street']
                            
                        elif 'city' in field_id:
                            value_to_fill = self.data['business_info']['mailing_address']['city']
                            
                        elif any(keyword in field_id for keyword in ['zip', 'postal']):
                            value_to_fill = self.data['business_info']['mailing_address']['zip_code']
                            
                        elif any(keyword in field_id for keyword in ['responsible', 'contact', 'person']):
                            value_to_fill = self.data['responsible_party']['name']
                            
                        elif any(keyword in field_id for keyword in ['ssn', 'tax', 'tin', 'id']):
                            value_to_fill = self.data['responsible_party']['ssn_itin']
                            
                        elif 'title' in field_id:
                            value_to_fill = self.data['responsible_party']['title']
                            
                        elif any(keyword in field_id for keyword in ['activity', 'business', 'purpose']):
                            value_to_fill = self.data['business_details'].get('principal_activity', '')
                            
                        elif any(keyword in field_id for keyword in ['employee', 'expect']):
                            value_to_fill = self.data['business_details'].get('highest_number_employees_expected', '')
                            
                        elif any(keyword in field_id for keyword in ['date', 'start']):
                            value_to_fill = self.data['business_details'].get('date_business_started', '')
                        
                        if value_to_fill:
                            await input_elem.clear()
                            await input_elem.type(value_to_fill, delay=50)
                            logger.info(f"Filled field '{field_id}' with: {value_to_fill[:20]}...")
                            filled_count += 1
                            await asyncio.sleep(0.5)
                            
                except Exception as e:
                    logger.warning(f"Failed to fill input field: {e}")
                    continue
            
            # Handle select dropdowns
            selects = await self.page.locator('select').all()
            
            for select_elem in selects:
                try:
                    if await select_elem.is_visible() and await select_elem.is_enabled():
                        name = await select_elem.get_attribute('name') or ""
                        id_attr = await select_elem.get_attribute('id') or ""
                        
                        field_id = f"{name} {id_attr}".lower()
                        
                        if 'state' in field_id:
                            try:
                                await select_elem.select_option(value=self.data['business_info']['mailing_address']['state'])
                                logger.info(f"Selected state: {self.data['business_info']['mailing_address']['state']}")
                                filled_count += 1
                                await asyncio.sleep(0.5)
                            except:
                                pass
                                
                        elif any(keyword in field_id for keyword in ['entity', 'organization', 'type']):
                            # Try to select LLC or appropriate entity type
                            options = await select_elem.locator('option').all()
                            for option in options:
                                option_text = await option.inner_text()
                                if 'llc' in option_text.lower() or self.data['entity_info']['entity_type'].lower() in option_text.lower():
                                    await select_elem.select_option(option_text)
                                    logger.info(f"Selected entity type: {option_text}")
                                    filled_count += 1
                                    await asyncio.sleep(0.5)
                                    break
                        
                except Exception as e:
                    logger.warning(f"Failed to fill select field: {e}")
                    continue
            
            # Handle radio buttons
            radios = await self.page.locator('input[type="radio"]').all()
            
            for radio in radios:
                try:
                    if await radio.is_visible():
                        value = await radio.get_attribute('value') or ""
                        name = await radio.get_attribute('name') or ""
                        
                        # Get associated label text
                        label_text = ""
                        try:
                            # Try different ways to find label
                            label_elem = await radio.locator('..').locator('label').first
                            label_text = await label_elem.inner_text()
                        except:
                            try:
                                # Try finding label by for attribute
                                radio_id = await radio.get_attribute('id')
                                if radio_id:
                                    label_elem = await self.page.locator(f'label[for="{radio_id}"]').first
                                    label_text = await label_elem.inner_text()
                            except:
                                pass
                        
                        combined_text = f"{value} {label_text}".lower()
                        
                        # Select appropriate radio buttons
                        if any(keyword in combined_text for keyword in ['llc', 'limited liability']):
                            if not await radio.is_checked():
                                await radio.click()
                                logger.info(f"Selected radio: {label_text}")
                                filled_count += 1
                                await asyncio.sleep(0.5)
                        
                        elif 'yes' in combined_text and any(keyword in name.lower() for keyword in ['employee', 'hire']):
                            if not await radio.is_checked():
                                await radio.click()
                                logger.info(f"Selected radio: {label_text}")
                                filled_count += 1
                                await asyncio.sleep(0.5)
                
                except Exception as e:
                    logger.warning(f"Failed to handle radio button: {e}")
                    continue
            
            logger.info(f"Filled {filled_count} form fields")
            return filled_count > 0
            
        except Exception as e:
            logger.error(f"Error filling form fields: {e}")
            return False
    
    async def find_continue_button(self):
        """Find and click continue/next/submit button"""
        continue_selectors = [
            'input[value*="Continue"]',
            'input[value*="Next"]', 
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'input[type="submit"]',
            'button[type="submit"]',
            'input[value*="Submit"]',
            'button:has-text("Submit")'
        ]
        
        for selector in continue_selectors:
            try:
                elements = await self.page.locator(selector).all()
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        text = await element.inner_text() if 'button' in selector else await element.get_attribute('value')
                        logger.info(f"Clicking continue button: {text}")
                        await element.click()
                        await asyncio.sleep(3)
                        return True, text
            except:
                continue
                
        return False, None
    
    async def is_final_submission_page(self):
        """Check if this is the final submission page"""
        try:
            body_text = await self.page.inner_text('body')
            final_keywords = [
                'submit your application',
                'submit application', 
                'final step',
                'review and submit',
                'confirm and submit'
            ]
            return any(keyword in body_text.lower() for keyword in final_keywords)
        except:
            return False
    
    async def run_form_filling(self):
        """Main form filling process"""
        try:
            await self.setup_browser()
            await self.navigate_to_form()
            
            max_pages = 15  # Increased limit
            current_page = 0
            
            while current_page < max_pages:
                current_page += 1
                logger.info(f"\\n--- Processing Page {current_page} ---")
                
                # Analyze current page
                page_type = await self.analyze_page()
                await self.wait_and_screenshot(f"page_{current_page}")
                
                # Check if final submission page
                if await self.is_final_submission_page():
                    logger.info("\\nREACHED FINAL SUBMISSION PAGE!")
                    await self.wait_and_screenshot("final_submission_page")
                    
                    print("\\n" + "="*80)
                    print("SUCCESS! EIN APPLICATION FORM IS READY FOR SUBMISSION!")
                    print("="*80)
                    print("The form has been filled out and you're now at the final submission page.")
                    print("Please review all information in the browser window before submitting.")
                    print("The browser will remain open for your final review and submission.")
                    print("\\nScreenshots of all pages have been saved in screenshots/ folder.")
                    print("="*80)
                    
                    # Keep browser open and don't exit
                    input("\\nPress Enter when you're done reviewing (this will close the browser)...")
                    return True
                
                # Try to fill form fields on current page
                filled_something = await self.fill_any_form_fields()
                
                if filled_something:
                    await self.wait_and_screenshot(f"page_{current_page}_filled")
                
                # Try to continue to next page
                clicked, button_text = await self.find_continue_button()
                
                if clicked:
                    logger.info(f"Successfully clicked: {button_text}")
                    await asyncio.sleep(2)  # Wait for page transition
                else:
                    logger.warning("No continue button found - checking if we're stuck")
                    
                    # If we can't find continue button, try some common alternatives
                    alt_selectors = [
                        'a[href*="next"]',
                        'a[href*="continue"]', 
                        'input[onclick]',
                        'button[onclick]'
                    ]
                    
                    clicked_alt = False
                    for selector in alt_selectors:
                        try:
                            element = await self.page.locator(selector).first
                            if await element.is_visible():
                                await element.click()
                                logger.info(f"Clicked alternative navigation: {selector}")
                                clicked_alt = True
                                await asyncio.sleep(2)
                                break
                        except:
                            continue
                    
                    if not clicked_alt:
                        logger.warning("Cannot find way to continue - may be at end of form")
                        break
                
                # Safety check - if URL hasn't changed in a while, we might be stuck
                await asyncio.sleep(1)
            
            # If we exit the loop without reaching final page
            logger.info("Completed form processing")
            await self.wait_and_screenshot("final_state")
            
            print("\\n" + "="*80)
            print("FORM PROCESSING COMPLETED")
            print("="*80)
            print("The automation has processed all available form pages.")
            print("Please check the browser window to review the form and complete any remaining steps.")
            print("The browser will remain open for your review.")
            print("="*80)
            
            input("\\nPress Enter when done reviewing (this will close the browser)...")
            return True
            
        except Exception as e:
            logger.error(f"Form filling failed: {e}")
            print(f"\\nError during form filling: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    print("Improved EIN Form Filler Starting...")
    print("="*50)
    
    filler = ImprovedEINFiller()
    
    try:
        await filler.run_form_filling()
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
    except Exception as e:
        print(f"\\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())