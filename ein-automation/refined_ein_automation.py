#!/usr/bin/env python3
"""
Refined EIN Form Automation - Better button detection and form navigation
"""

import json
import time
import asyncio
import random
import tkinter as tk
from tkinter import messagebox
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class RefinedEINAutomation:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        self.page_count = 0
        self.last_url = ""
        
    def load_data(self):
        with open('ein_data.json', 'r') as f:
            data = json.load(f)
        print(f"Business: {data['business_info']['legal_name']}")
        print("Starting refined EIN automation...")
        return data
    
    async def setup_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--disable-web-security']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        logger.info("Browser ready")
    
    async def screenshot(self, name):
        self.page_count += 1
        path = f'screenshots/{name}_{self.page_count}_{int(time.time())}.png'
        await self.page.screenshot(path=path, full_page=True)
        logger.info(f"Screenshot: {path}")
        return path
    
    async def navigate_to_form(self):
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.screenshot("landing")
        await asyncio.sleep(2)
        
        # Click Begin Application
        begin_link = await self.page.wait_for_selector('a:has-text("Begin Application Now")')
        await begin_link.click()
        logger.info("Started application")
        await asyncio.sleep(3)
        await self.screenshot("application_started")
        
        return True
    
    async def select_llc_entity_type(self):
        """Select LLC on the legal structure page"""
        logger.info("Selecting LLC entity type...")
        
        try:
            # Wait for the LLC label and click it
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]', timeout=15000)
            await llc_label.click()
            logger.info("Selected LLC")
            await asyncio.sleep(1)
            await self.screenshot("llc_selected")
            return True
        except:
            # Fallback method
            await self.page.evaluate('''
                const llcRadio = document.getElementById("LLClegalStructureInputid");
                if (llcRadio) {
                    llcRadio.checked = true;
                    llcRadio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            ''')
            logger.info("Selected LLC via JavaScript")
            await self.screenshot("llc_selected_js")
            return True
    
    async def find_and_click_real_continue_button(self):
        """Find and click the actual Continue button (not other buttons)"""
        logger.info("Looking for Continue button...")
        
        # First, let's see what buttons are available
        try:
            all_buttons = await self.page.locator('button, input[type="submit"], input[type="button"]').all()
            button_texts = []
            
            for i, button in enumerate(all_buttons):
                try:
                    if await button.is_visible():
                        text = ""
                        if await button.evaluate('el => el.tagName') == 'BUTTON':
                            text = await button.inner_text()
                        else:
                            text = await button.get_attribute('value') or ""
                        
                        if text:
                            button_texts.append(f"Button {i}: '{text.strip()}'")
                except:
                    continue
            
            logger.info(f"Available buttons: {', '.join(button_texts)}")
            
            # Now try to find the right continue button with very specific selectors
            continue_selectors = [
                # Try form-specific continue buttons first
                'form input[type="submit"][value="Continue"]',
                'form button[type="submit"]:has-text("Continue")',
                'div.form-group input[value="Continue"]',
                'div.form-section input[value="Continue"]',
                
                # General continue buttons
                'input[type="submit"][value="Continue"]',
                'button[type="submit"]:has-text("Continue")',
                'input[value="Continue"]',
                'button:has-text("Continue")',
                
                # Fallback to any submit button
                'form input[type="submit"]',
                'form button[type="submit"]'
            ]
            
            for selector in continue_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            # Get the button text/value
                            if 'input' in selector:
                                text = await element.get_attribute('value') or ""
                            else:
                                text = await element.inner_text()
                            
                            # Skip buttons that are clearly not continue buttons
                            if text and any(skip_word in text.lower() for skip_word in [
                                "here's how", "know", "info", "help", "back", "previous", "cancel"
                            ]):
                                logger.info(f"Skipping button: '{text}' (not a continue button)")
                                continue
                            
                            # Click the button
                            logger.info(f"Clicking continue button: '{text}' ({selector})")
                            await element.click()
                            await asyncio.sleep(4)  # Wait for navigation
                            
                            # Check if URL changed
                            new_url = self.page.url
                            if new_url != self.last_url:
                                logger.info(f"URL changed from {self.last_url} to {new_url}")
                                self.last_url = new_url
                                return True
                            else:
                                logger.warning(f"URL didn't change after clicking '{text}'")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            logger.warning("Could not find a working continue button")
            return False
            
        except Exception as e:
            logger.error(f"Error finding continue button: {e}")
            return False
    
    async def fill_comprehensive_form_fields(self):
        """Fill all form fields on the current page"""
        logger.info("Filling form fields...")
        
        await self.page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(1)
        
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
                    value = None
                    
                    # Business name
                    if any(word in field_info for word in ['name', 'business', 'legal', 'company']):
                        value = self.data['business_info']['legal_name']
                    # Address
                    elif any(word in field_info for word in ['street', 'address']):
                        value = self.data['business_info']['mailing_address']['street']
                    elif 'city' in field_info:
                        value = self.data['business_info']['mailing_address']['city']
                    elif any(word in field_info for word in ['zip', 'postal']):
                        value = self.data['business_info']['mailing_address']['zip_code']
                    # Responsible party
                    elif any(word in field_info for word in ['responsible', 'contact']):
                        value = self.data['responsible_party']['name']
                    elif any(word in field_info for word in ['ssn', 'tax', 'tin']):
                        value = self.data['responsible_party']['ssn_itin']
                    elif 'title' in field_info:
                        value = self.data['responsible_party']['title']
                    # Business details
                    elif any(word in field_info for word in ['activity', 'principal']):
                        value = self.data['business_details'].get('principal_activity', '')
                    elif any(word in field_info for word in ['employee', 'expect']):
                        value = self.data['business_details'].get('highest_number_employees_expected', '')
                    elif any(word in field_info for word in ['phone', 'telephone']):
                        value = self.data['applicant_info'].get('phone_number', '')
                    
                    if value:
                        await input_elem.clear()
                        await input_elem.type(str(value), delay=50)
                        logger.info(f"Filled field with {str(value)[:20]}...")
                        filled_count += 1
                        await asyncio.sleep(0.3)
            
            except Exception as e:
                logger.debug(f"Text input error: {e}")
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
                        await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Select error: {e}")
                continue
        
        # Radio buttons - be more selective
        radios = await self.page.locator('input[type="radio"]').all()
        radio_groups = {}
        
        # Group by name
        for radio in radios:
            try:
                if await radio.is_visible():
                    name = await radio.get_attribute('name')
                    if name and name not in radio_groups:
                        radio_groups[name] = []
                    if name:
                        radio_groups[name].append(radio)
            except:
                continue
        
        # Handle radio groups
        for group_name, radios_in_group in radio_groups.items():
            try:
                group_name_lower = group_name.lower()
                
                # Skip legal structure since we already handled it
                if 'legalstructure' in group_name_lower:
                    continue
                
                for radio in radios_in_group:
                    try:
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
                        
                        combined = f"{value} {label_text}"
                        
                        # Employee questions
                        if any(word in group_name_lower for word in ['employee', 'hire']):
                            has_employees = self.data['business_details'].get('has_employees', False)
                            if (has_employees and 'yes' in combined) or (not has_employees and 'no' in combined):
                                await radio.click()
                                logger.info(f"Selected employee option: {label_text}")
                                filled_count += 1
                                await asyncio.sleep(0.5)
                                break
                    
                    except Exception as e:
                        logger.debug(f"Radio error: {e}")
                        continue
            
            except Exception as e:
                logger.debug(f"Radio group error: {e}")
                continue
        
        logger.info(f"Filled {filled_count} fields")
        return filled_count
    
    async def is_final_submission_page(self):
        """Enhanced detection of final submission page"""
        try:
            url = self.page.url
            page_text = await self.page.inner_text('body')
            title = await self.page.title()
            
            # Check for final submission indicators
            final_indicators = [
                'submit your application',
                'submit application',
                'review and submit',
                'final step',
                'complete application',
                'submit for processing',
                'confirm submission'
            ]
            
            text_lower = page_text.lower()
            title_lower = title.lower()
            url_lower = url.lower()
            
            for indicator in final_indicators:
                if indicator in text_lower or indicator in title_lower or indicator in url_lower:
                    return True
            
            # Check for submit buttons without continue buttons
            submit_buttons = await self.page.locator('input[value*="Submit"], button:has-text("Submit")').count()
            continue_buttons = await self.page.locator('input[value="Continue"], button:has-text("Continue")').count()
            
            if submit_buttons > 0 and continue_buttons == 0:
                return True
            
            return False
            
        except:
            return False
    
    def show_final_review_modal(self):
        """Show final review modal"""
        try:
            root = tk.Tk()
            root.title("EIN Application - Ready for Submission")
            root.geometry("700x500")
            
            # Main content
            main_frame = tk.Frame(root, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            title_label = tk.Label(main_frame, text="EIN APPLICATION READY FOR SUBMISSION!", 
                                 font=("Arial", 14, "bold"), fg="green")
            title_label.pack(pady=(0, 15))
            
            message = tk.Label(main_frame, 
                              text="The EIN application form has been filled out completely.\\n\\n"
                                   "Please review all information in the browser window.\\n\\n"
                                   "When you click 'PROCEED TO SUBMIT' below:\\n"
                                   "• You'll return to the browser\\n"
                                   "• Review all filled information one final time\\n"
                                   "• Click the 'Submit' button on the IRS website\\n"
                                   "• Your EIN will be issued immediately upon approval",
                              font=("Arial", 10), justify=tk.LEFT, wraplength=600)
            message.pack(pady=(0, 20))
            
            # Summary
            summary_text = f"""Application Summary:
Business: {self.data['business_info']['legal_name']}
Entity Type: {self.data['entity_info']['entity_type']}
Responsible Party: {self.data['responsible_party']['name']}
Address: {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']}"""
            
            summary_label = tk.Label(main_frame, text=summary_text, 
                                   font=("Courier", 9), justify=tk.LEFT, 
                                   relief=tk.SUNKEN, padx=10, pady=10)
            summary_label.pack(pady=(0, 20), fill=tk.X)
            
            result = {'proceed': False}
            
            def proceed():
                result['proceed'] = True
                root.quit()
                root.destroy()
            
            def cancel():
                result['proceed'] = False
                root.quit()
                root.destroy()
            
            # Buttons
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=10)
            
            proceed_btn = tk.Button(button_frame, text="PROCEED TO SUBMIT", 
                                  command=proceed, bg="green", fg="white", 
                                  font=("Arial", 12, "bold"), padx=30, pady=10)
            proceed_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            cancel_btn = tk.Button(button_frame, text="CANCEL", 
                                 command=cancel, bg="red", fg="white", 
                                 font=("Arial", 12), padx=30, pady=10)
            cancel_btn.pack(side=tk.LEFT)
            
            root.mainloop()
            return result['proceed']
            
        except Exception as e:
            logger.error(f"Modal error: {e}")
            return True  # Fallback to proceeding
    
    async def run_automation(self):
        """Run complete automation"""
        try:
            await self.setup_browser()
            await self.navigate_to_form()
            
            # Initialize URL tracking
            self.last_url = self.page.url
            
            # Handle legal structure page
            if 'legalStructure' in self.page.url:
                await self.select_llc_entity_type()
            
            # Process form pages
            max_pages = 30
            for page_num in range(1, max_pages + 1):
                logger.info(f"\\n=== Processing Page {page_num} ===")
                
                current_url = self.page.url
                logger.info(f"Current URL: {current_url}")
                
                # Check if final page
                if await self.is_final_submission_page():
                    logger.info("REACHED FINAL SUBMISSION PAGE!")
                    await self.screenshot("final_submission_page")
                    
                    # Show modal
                    if self.show_final_review_modal():
                        print("\\n" + "="*60)
                        print("READY FOR MANUAL SUBMISSION")
                        print("="*60)
                        print("Please click 'Submit' in the browser window.")
                        print("Your EIN will be issued immediately.")
                        print("="*60)
                        return "SUCCESS_READY_FOR_SUBMISSION"
                    else:
                        return "CANCELLED_BY_USER"
                
                # Fill fields
                fields_filled = await self.fill_comprehensive_form_fields()
                
                if fields_filled > 0:
                    await self.screenshot(f"page_{page_num}_filled")
                
                # Continue to next page
                if not await self.find_and_click_real_continue_button():
                    logger.warning("No continue button found - checking for final page...")
                    await asyncio.sleep(2)
                    
                    if await self.is_final_submission_page():
                        continue  # Will be caught in next iteration
                    
                    logger.info("Reached end of form")
                    break
                
                await asyncio.sleep(1)
            
            await self.screenshot("automation_completed")
            print("\\n" + "="*60)
            print("AUTOMATION COMPLETED")
            print("="*60)
            print("Please review and submit the form in the browser.")
            print("="*60)
            
            return "COMPLETED"
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return f"ERROR: {e}"

async def main():
    print("Refined EIN Form Automation")
    print("="*40)
    
    automation = RefinedEINAutomation()
    
    try:
        result = await automation.run_automation()
        print(f"\\nResult: {result}")
        
        if "SUCCESS" in result:
            print("\\nForm is ready for submission!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\\nBrowser will remain open for final review.")

if __name__ == "__main__":
    asyncio.run(main())