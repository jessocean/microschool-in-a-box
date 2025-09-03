#!/usr/bin/env python3
"""
Final EIN Automation - Targets the actual Continue link button
"""

import json
import time
import asyncio
import random
import tkinter as tk
from tkinter import messagebox, scrolledtext
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('final_ein_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalEINAutomation:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        self.screenshots = []
        
    def load_data(self):
        with open('ein_data.json', 'r') as f:
            data = json.load(f)
        print(f"\\nBusiness: {data['business_info']['legal_name']}")
        print(f"Entity Type: {data['entity_info']['entity_type']}")
        print("Starting final EIN automation...")
        return data
    
    async def setup_browser(self):
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox']
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        
        self.page = await self.context.new_page()
        logger.info("Browser ready")
    
    async def screenshot(self, name):
        timestamp = int(time.time())
        path = f'screenshots/{name}_{timestamp}.png'
        await self.page.screenshot(path=path, full_page=True)
        self.screenshots.append(path)
        logger.info(f"Screenshot: {path}")
        return path
    
    async def human_delay(self, min_ms=500, max_ms=1500):
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def navigate_to_form(self):
        logger.info("Navigating to IRS EIN application...")
        
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.screenshot("01_landing")
        await self.human_delay(2000, 3000)
        
        # Start application
        begin_button = await self.page.wait_for_selector('a:has-text("Begin Application Now")')
        await begin_button.click()
        logger.info("Started application")
        
        await self.human_delay(4000, 6000)
        await self.screenshot("02_started")
        
        return True
    
    async def select_llc_and_fill_page(self):
        """Select LLC and fill the legal structure page"""
        logger.info("Processing legal structure page...")
        
        await self.page.wait_for_load_state('domcontentloaded')
        await self.human_delay(1000, 2000)
        await self.screenshot("03_legal_structure_page")
        
        # Select LLC
        try:
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]')
            await llc_label.click()
            logger.info("Selected LLC")
            await self.human_delay(1000, 1500)
        except:
            await self.page.evaluate('''
                const llc = document.getElementById("LLClegalStructureInputid");
                if (llc) { llc.checked = true; llc.dispatchEvent(new Event('change')); }
            ''')
            logger.info("Selected LLC via JavaScript")
        
        await self.screenshot("04_llc_selected")
        
        # Fill all fields
        await self.fill_all_form_fields()
        await self.screenshot("05_fields_filled")
        
        return True
    
    async def fill_all_form_fields(self):
        """Fill all form fields on current page"""
        logger.info("Filling form fields...")
        
        filled_count = 0
        
        # Text inputs
        text_inputs = await self.page.locator('input[type="text"], input:not([type])').all()
        
        for input_elem in text_inputs:
            try:
                if await input_elem.is_visible() and await input_elem.is_enabled():
                    name = (await input_elem.get_attribute('name') or "").lower()
                    id_attr = (await input_elem.get_attribute('id') or "").lower()
                    placeholder = (await input_elem.get_attribute('placeholder') or "").lower()
                    
                    current_value = await input_elem.input_value()
                    if current_value and current_value.strip():
                        continue
                    
                    field_info = f"{name} {id_attr} {placeholder}"
                    value = self.get_field_value(field_info)
                    
                    if value:
                        await input_elem.clear()
                        await input_elem.type(str(value), delay=50)
                        logger.info(f"Filled: {str(value)[:20]}...")
                        filled_count += 1
                        await self.human_delay(300, 600)
            
            except Exception as e:
                logger.debug(f"Input error: {e}")
                continue
        
        # Select dropdowns
        selects = await self.page.locator('select').all()
        for select_elem in selects:
            try:
                if await select_elem.is_visible():
                    name = (await select_elem.get_attribute('name') or "").lower()
                    id_attr = (await select_elem.get_attribute('id') or "").lower()
                    
                    if 'state' in f"{name} {id_attr}":
                        state = self.data['business_info']['mailing_address']['state']
                        await select_elem.select_option(value=state)
                        logger.info(f"Selected state: {state}")
                        filled_count += 1
                        await self.human_delay(300, 600)
            except Exception as e:
                logger.debug(f"Select error: {e}")
                continue
        
        # Radio buttons (excluding LLC)
        radios = await self.page.locator('input[type="radio"]:not(#LLClegalStructureInputid)').all()
        
        for radio in radios:
            try:
                if await radio.is_visible():
                    name = await radio.get_attribute('name') or ""
                    value = (await radio.get_attribute('value') or "").lower()
                    radio_id = await radio.get_attribute('id') or ""
                    
                    # Find label
                    label_text = ""
                    if radio_id:
                        try:
                            label = await self.page.locator(f'label[for="{radio_id}"]').first
                            label_text = (await label.inner_text()).lower()
                        except:
                            pass
                    
                    combined = f"{name} {value} {label_text}".lower()
                    
                    # Employee questions
                    if any(word in combined for word in ['employee', 'hire']):
                        has_employees = self.data['business_details'].get('has_employees', False)
                        should_select = (has_employees and 'yes' in combined) or (not has_employees and 'no' in combined)
                        
                        if should_select and not await radio.is_checked():
                            await radio.click()
                            logger.info(f"Selected: {label_text}")
                            filled_count += 1
                            await self.human_delay(300, 600)
            
            except Exception as e:
                logger.debug(f"Radio error: {e}")
                continue
        
        logger.info(f"Filled {filled_count} fields")
        return filled_count
    
    def get_field_value(self, field_info):
        """Get value for field based on field info"""
        field_info = field_info.lower()
        
        # Business name
        if any(word in field_info for word in ['business', 'company', 'legal']) and 'name' in field_info:
            return self.data['business_info']['legal_name']
        
        # Trade name
        if any(word in field_info for word in ['trade', 'dba']) and 'name' in field_info:
            return self.data['business_info']['trade_name_dba']
        
        # Address
        if any(word in field_info for word in ['street', 'address']):
            return self.data['business_info']['mailing_address']['street']
        
        if 'city' in field_info:
            return self.data['business_info']['mailing_address']['city']
        
        if any(word in field_info for word in ['zip', 'postal']):
            return self.data['business_info']['mailing_address']['zip_code']
        
        # Responsible party
        if any(word in field_info for word in ['responsible', 'contact']) and 'name' in field_info:
            return self.data['responsible_party']['name']
        
        if any(word in field_info for word in ['ssn', 'tax', 'tin']):
            return self.data['responsible_party']['ssn_itin']
        
        if 'title' in field_info:
            return self.data['responsible_party']['title']
        
        # Business details
        if any(word in field_info for word in ['activity', 'principal']):
            return self.data['business_details'].get('principal_activity', '')
        
        if any(word in field_info for word in ['employee', 'expect']):
            return self.data['business_details'].get('highest_number_employees_expected', '')
        
        if any(word in field_info for word in ['phone', 'telephone']):
            return self.data['applicant_info'].get('phone_number', '')
        
        return None
    
    async def click_continue_link(self):
        """Click the Continue link (not button!) based on debug findings"""
        logger.info("Looking for Continue link...")
        
        try:
            # Target the specific Continue link we found in debug
            continue_selectors = [
                # Primary target: IRS button link with "Continue" text
                'a.irs-button:has-text("Continue")',
                'a[class*="irs-button"]:has-text("Continue")',
                
                # Fallback: any link with Continue text
                'a:has-text("Continue")',
                
                # More specific class-based selectors
                'a.irs-button--active:has-text("Continue")',
                
                # ID-based (we saw id='anchor-ui-0' but it might be dynamic)
                'a[id*="anchor"]:has-text("Continue")'
            ]
            
            for selector in continue_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            # Double check it's actually the Continue link
                            text = await element.inner_text()
                            if 'continue' in text.lower():
                                logger.info(f"Found Continue link: '{text}' ({selector})")
                                
                                # Click the link
                                await element.click()
                                logger.info("Clicked Continue link!")
                                await self.human_delay(4000, 6000)
                                return True
                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("Could not find Continue link")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking Continue: {e}")
            return False
    
    async def is_final_page(self):
        """Check if we're at final submission page"""
        try:
            page_text = await self.page.inner_text('body')
            url = self.page.url
            
            final_keywords = [
                'submit your application',
                'submit application',
                'review and submit', 
                'final step',
                'complete application'
            ]
            
            combined = f"{url} {page_text}".lower()
            
            for keyword in final_keywords:
                if keyword in combined:
                    return True
            
            # Check for Submit buttons without Continue
            submit_count = await self.page.locator('input[value*="Submit"], button:has-text("Submit"), a:has-text("Submit")').count()
            continue_count = await self.page.locator('input[value="Continue"], button:has-text("Continue"), a:has-text("Continue")').count()
            
            return submit_count > 0 and continue_count == 0
            
        except:
            return False
    
    def show_review_modal(self):
        """Show final review modal"""
        try:
            root = tk.Tk()
            root.title("EIN Application - Ready for Submission")
            root.geometry("800x600")
            
            main_frame = tk.Frame(root, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            title_label = tk.Label(main_frame, text="EIN APPLICATION READY FOR SUBMISSION!", 
                                 font=("Arial", 14, "bold"), fg="green")
            title_label.pack(pady=(0, 15))
            
            instructions = tk.Label(main_frame, 
                                  text="The EIN application has been filled out completely.\\n\\n"
                                       "Please review all information in the browser window.\\n\\n"
                                       "When you click PROCEED TO SUBMIT:\\n"
                                       "- You'll return to the browser window\\n"
                                       "- Review all information one final time\\n"
                                       "- Click the Submit button on the IRS website\\n"
                                       "- Your EIN will be issued immediately",
                                  font=("Arial", 10), justify=tk.LEFT)
            instructions.pack(pady=(0, 20))
            
            # Summary
            summary_text = f"""Application Summary:

Business Name: {self.data['business_info']['legal_name']}
Entity Type: {self.data['entity_info']['entity_type']}
Responsible Party: {self.data['responsible_party']['name']}
Address: {self.data['business_info']['mailing_address']['street']}
         {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']} {self.data['business_info']['mailing_address']['zip_code']}
Principal Activity: {self.data['business_details'].get('principal_activity', 'Not specified')}

Screenshots saved: {len(self.screenshots)} images"""
            
            text_area = scrolledtext.ScrolledText(main_frame, height=12, wrap=tk.WORD, 
                                                font=("Courier", 9))
            text_area.insert(tk.END, summary_text)
            text_area.config(state=tk.DISABLED)
            text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            result = {'proceed': False}
            
            def proceed():
                result['proceed'] = True
                root.quit()
                root.destroy()
            
            def cancel():
                result['proceed'] = False
                root.quit()
                root.destroy()
            
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=10)
            
            proceed_btn = tk.Button(button_frame, text="PROCEED TO SUBMIT", 
                                  command=proceed, bg="green", fg="white", 
                                  font=("Arial", 12, "bold"), padx=20, pady=10)
            proceed_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            cancel_btn = tk.Button(button_frame, text="CANCEL", 
                                 command=cancel, bg="red", fg="white", 
                                 font=("Arial", 12), padx=20, pady=10)
            cancel_btn.pack(side=tk.LEFT)
            
            root.mainloop()
            return result['proceed']
            
        except Exception as e:
            logger.error(f"Modal error: {e}")
            response = input("Type 'yes' to proceed with submission: ").lower().strip()
            return response == 'yes'
    
    async def run_automation(self):
        """Run complete automation"""
        try:
            print("\\n" + "="*60)
            print("FINAL EIN FORM AUTOMATION")
            print("="*60)
            
            await self.setup_browser()
            await self.navigate_to_form()
            
            # Handle legal structure page
            if 'legalStructure' in self.page.url:
                await self.select_llc_and_fill_page()
            
            # Process remaining pages
            max_pages = 50
            current_page = 1
            last_url = self.page.url
            
            while current_page <= max_pages:
                logger.info(f"\\n=== Processing page {current_page} ===")
                
                current_url = self.page.url
                logger.info(f"URL: {current_url}")
                
                # Check if final page
                if await self.is_final_page():
                    logger.info("REACHED FINAL SUBMISSION PAGE!")
                    await self.screenshot(f"06_final_submission")
                    
                    if self.show_review_modal():
                        print("\\n" + "="*60)
                        print("READY FOR MANUAL SUBMISSION")
                        print("="*60)
                        print("Please click Submit in the browser.")
                        print("="*60)
                        return "SUCCESS_READY_FOR_SUBMISSION"
                    else:
                        return "CANCELLED_BY_USER"
                
                # Fill fields (skip page 1 since already done)
                if current_page > 1:
                    filled = await self.fill_all_form_fields()
                    if filled > 0:
                        await self.screenshot(f"page_{current_page:02d}_filled")
                
                # Try to continue - this is the key fix!
                if await self.click_continue_link():
                    logger.info("Successfully clicked Continue - advancing")
                    await self.human_delay(2000, 4000)
                    
                    # Check if URL actually changed
                    new_url = self.page.url
                    if new_url != current_url:
                        logger.info(f"URL changed to: {new_url}")
                        last_url = new_url
                    else:
                        logger.info("URL didn't change - may still be processing")
                else:
                    logger.warning("Could not click Continue - checking if at final page")
                    await self.human_delay(2000, 3000)
                    
                    if await self.is_final_page():
                        continue  # Will be caught in next iteration
                    
                    logger.info("No Continue link found - may be at end")
                    break
                
                current_page += 1
            
            await self.screenshot("07_automation_completed")
            print("\\n" + "="*60)
            print("AUTOMATION COMPLETED")
            print("="*60)
            print("Please review and submit the form manually.")
            print("="*60)
            
            return "COMPLETED"
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return f"ERROR: {e}"

async def main():
    print("Final EIN Form Automation")
    print("="*40)
    print("This script will:")
    print("- Fill out the entire EIN form")
    print("- Click Continue LINKS (not buttons)")
    print("- Stop at final submission")
    print("- Show review modal")
    print("="*40)
    
    automation = FinalEINAutomation()
    
    try:
        result = await automation.run_automation()
        print(f"\\nResult: {result}")
        
        if "SUCCESS" in result:
            print("\\nSUCCESS! Ready for submission!")
        elif "ERROR" in result:
            print(f"\\nERROR: {result}")
        else:
            print("\\nCompleted - check browser")
        
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
    except Exception as e:
        print(f"\\nError: {e}")
    
    print("\\nBrowser will remain open.")

if __name__ == "__main__":
    asyncio.run(main())