#!/usr/bin/env python3
"""
Complete EIN Form Automation - Fills entire form and shows review modal before final submission
"""

import json
import time
import asyncio
import random
import tkinter as tk
from tkinter import messagebox
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ein_automation_complete.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteEINAutomation:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        self.page_count = 0
        self.screenshots = []
        
    def load_data(self):
        """Load data from ein_data.json"""
        try:
            with open('ein_data.json', 'r') as f:
                data = json.load(f)
            logger.info("Data loaded successfully")
            print(f"Business: {data['business_info']['legal_name']}")
            print(f"Entity Type: {data['entity_info']['entity_type']}")
            print("Starting complete form automation...")
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
                '--start-maximized',
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser setup complete")
    
    async def take_screenshot(self, name="page"):
        """Take screenshot and track it"""
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
        except:
            await asyncio.sleep(2)
        
        self.page_count += 1
        screenshot_path = f'screenshots/{name}_{self.page_count}_{int(time.time())}.png'
        await self.page.screenshot(path=screenshot_path, full_page=True)
        self.screenshots.append(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    
    async def human_delay(self, min_ms=300, max_ms=800):
        """Human-like delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def navigate_to_form(self):
        """Navigate to the EIN application form"""
        logger.info("Navigating to EIN application...")
        
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.take_screenshot("landing")
        await self.human_delay(2000, 3000)
        
        # Click "Begin Application Now"
        begin_link = await self.page.wait_for_selector('a:has-text("Begin Application Now")', timeout=30000)
        await begin_link.click()
        logger.info("Clicked 'Begin Application Now'")
        
        await self.human_delay(3000, 5000)
        await self.take_screenshot("after_begin")
        
        return True
    
    async def handle_legal_structure_page(self):
        """Handle legal structure selection"""
        logger.info("Processing legal structure page...")
        
        await self.take_screenshot("legal_structure_page")
        
        # Select LLC by clicking its label
        try:
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]', timeout=15000)
            await llc_label.click()
            logger.info("Selected LLC entity type")
            await self.human_delay()
        except:
            # Fallback: use JavaScript
            await self.page.evaluate('''
                const llcRadio = document.getElementById("LLClegalStructureInputid");
                if (llcRadio) {
                    llcRadio.checked = true;
                    llcRadio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            ''')
            logger.info("Selected LLC using JavaScript fallback")
        
        await self.take_screenshot("llc_selected")
        
        # Find and click continue button with multiple selectors
        continue_clicked = await self.click_continue_button()
        if not continue_clicked:
            raise Exception("Could not find continue button on legal structure page")
        
        return True
    
    async def click_continue_button(self):
        """Comprehensive continue button clicking"""
        continue_selectors = [
            'button:has-text("Continue")',
            'input[value="Continue"]',
            'button:has-text("Next")',
            'input[value="Next"]',
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'input[value="Submit"]',
            # More specific selectors
            'button.usa-button',
            'input.usa-button',
            'button[class*="button"]',
            'input[class*="button"]'
        ]
        
        for selector in continue_selectors:
            try:
                elements = await self.page.locator(selector).all()
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        text = ""
                        try:
                            text = await element.inner_text() if 'button' in selector else await element.get_attribute('value')
                        except:
                            text = "button"
                        
                        await element.click()
                        logger.info(f"Clicked continue button: '{text}' ({selector})")
                        await self.human_delay(3000, 5000)
                        return True
            except Exception as e:
                logger.debug(f"Continue selector {selector} failed: {e}")
                continue
        
        # Last resort: look for any clickable button
        try:
            all_buttons = await self.page.locator('button, input[type="submit"], input[type="button"]').all()
            for button in all_buttons:
                if await button.is_visible() and await button.is_enabled():
                    text = await button.inner_text() if await button.evaluate('el => el.tagName') == 'BUTTON' else await button.get_attribute('value')
                    if text and any(word in text.lower() for word in ['continue', 'next', 'submit', 'proceed']):
                        await button.click()
                        logger.info(f"Clicked button via text match: '{text}'")
                        await self.human_delay(3000, 5000)
                        return True
        except Exception as e:
            logger.debug(f"Last resort button clicking failed: {e}")
        
        logger.warning("No continue button found with any method")
        return False
    
    async def fill_form_fields_comprehensive(self):
        """Comprehensive form field filling"""
        logger.info("Filling form fields on current page...")
        
        filled_count = 0
        current_url = self.page.url
        
        try:
            await self.page.wait_for_load_state('networkidle', timeout=15000)
        except:
            await asyncio.sleep(2)
        
        # Text inputs - more comprehensive mapping
        text_inputs = await self.page.locator('input[type="text"], input:not([type]), input[type="email"], input[type="tel"]').all()
        
        for input_elem in text_inputs:
            try:
                if await input_elem.is_visible() and await input_elem.is_enabled():
                    # Get all identifying information
                    name = (await input_elem.get_attribute('name') or "").lower()
                    id_attr = (await input_elem.get_attribute('id') or "").lower()
                    placeholder = (await input_elem.get_attribute('placeholder') or "").lower()
                    aria_label = (await input_elem.get_attribute('aria-label') or "").lower()
                    
                    # Check if already filled
                    current_value = await input_elem.input_value()
                    if current_value and current_value.strip():
                        continue
                    
                    field_info = f"{name} {id_attr} {placeholder} {aria_label}"
                    value_to_fill = None
                    field_description = ""
                    
                    # Business name fields
                    if any(word in field_info for word in ['legalname', 'businessname', 'companyname', 'entityname', 'name']):
                        value_to_fill = self.data['business_info']['legal_name']
                        field_description = "business name"
                    
                    # Trade name / DBA
                    elif any(word in field_info for word in ['tradename', 'dba', 'doing', 'business', 'trade']):
                        value_to_fill = self.data['business_info']['trade_name_dba']
                        field_description = "trade name"
                    
                    # Address fields
                    elif any(word in field_info for word in ['street', 'address', 'addr', 'line1']):
                        value_to_fill = self.data['business_info']['mailing_address']['street']
                        field_description = "street address"
                    
                    elif 'city' in field_info:
                        value_to_fill = self.data['business_info']['mailing_address']['city']
                        field_description = "city"
                    
                    elif any(word in field_info for word in ['zip', 'postal', 'zipcode']):
                        value_to_fill = self.data['business_info']['mailing_address']['zip_code']
                        field_description = "zip code"
                    
                    # Responsible party
                    elif any(word in field_info for word in ['responsible', 'contact', 'person', 'individual']):
                        value_to_fill = self.data['responsible_party']['name']
                        field_description = "responsible party name"
                    
                    elif any(word in field_info for word in ['ssn', 'socialsecurity', 'taxid', 'tin', 'itin']):
                        value_to_fill = self.data['responsible_party']['ssn_itin']
                        field_description = "SSN/TIN"
                    
                    elif any(word in field_info for word in ['title', 'position', 'role']):
                        value_to_fill = self.data['responsible_party']['title']
                        field_description = "title"
                    
                    # Business details
                    elif any(word in field_info for word in ['activity', 'business', 'principal', 'primary']):
                        value_to_fill = self.data['business_details'].get('principal_activity', '')
                        field_description = "business activity"
                    
                    elif any(word in field_info for word in ['product', 'service', 'goods']):
                        value_to_fill = self.data['business_details'].get('principal_product_or_service', '')
                        field_description = "products/services"
                    
                    elif any(word in field_info for word in ['employee', 'workers', 'staff', 'expect']):
                        value_to_fill = self.data['business_details'].get('highest_number_employees_expected', '')
                        field_description = "expected employees"
                    
                    elif any(word in field_info for word in ['startdate', 'began', 'commenced', 'start']):
                        value_to_fill = self.data['business_details'].get('date_business_started', '')
                        field_description = "start date"
                    
                    elif any(word in field_info for word in ['phone', 'telephone', 'contact']):
                        value_to_fill = self.data['applicant_info'].get('phone_number', '')
                        field_description = "phone number"
                    
                    # Fill the field if we found a value
                    if value_to_fill:
                        await input_elem.clear()
                        await input_elem.type(str(value_to_fill), delay=random.randint(50, 150))
                        logger.info(f"Filled {field_description}: {str(value_to_fill)[:30]}...")
                        filled_count += 1
                        await self.human_delay(300, 600)
                
            except Exception as e:
                logger.warning(f"Failed to fill text input: {e}")
                continue
        
        # Select dropdowns
        select_elements = await self.page.locator('select').all()
        
        for select_elem in select_elements:
            try:
                if await select_elem.is_visible() and await select_elem.is_enabled():
                    name = (await select_elem.get_attribute('name') or "").lower()
                    id_attr = (await select_elem.get_attribute('id') or "").lower()
                    
                    field_info = f"{name} {id_attr}"
                    
                    # State selection
                    if 'state' in field_info:
                        state = self.data['business_info']['mailing_address']['state']
                        try:
                            await select_elem.select_option(value=state)
                            logger.info(f"Selected state: {state}")
                            filled_count += 1
                            await self.human_delay()
                        except:
                            # Try by label
                            try:
                                await select_elem.select_option(label=state)
                                logger.info(f"Selected state by label: {state}")
                                filled_count += 1
                                await self.human_delay()
                            except:
                                pass
                    
                    # Month selection (accounting year)
                    elif any(word in field_info for word in ['month', 'accounting', 'year']):
                        month = self.data['business_details'].get('closing_month_of_accounting_year', 'December')
                        try:
                            await select_elem.select_option(label=month)
                            logger.info(f"Selected accounting month: {month}")
                            filled_count += 1
                            await self.human_delay()
                        except:
                            pass
            
            except Exception as e:
                logger.warning(f"Failed to fill select: {e}")
                continue
        
        # Radio buttons - comprehensive handling
        radio_groups = {}
        radios = await self.page.locator('input[type="radio"]').all()
        
        # Group radios by name
        for radio in radios:
            try:
                if await radio.is_visible():
                    name = await radio.get_attribute('name')
                    if name:
                        if name not in radio_groups:
                            radio_groups[name] = []
                        radio_groups[name].append(radio)
            except:
                continue
        
        # Handle each radio group
        for group_name, radio_list in radio_groups.items():
            try:
                group_name_lower = group_name.lower()
                
                for radio in radio_list:
                    try:
                        value = (await radio.get_attribute('value') or "").lower()
                        radio_id = await radio.get_attribute('id') or ""
                        
                        # Find associated label
                        label_text = ""
                        if radio_id:
                            try:
                                label = await self.page.locator(f'label[for="{radio_id}"]').first
                                label_text = (await label.inner_text()).lower()
                            except:
                                pass
                        
                        combined_info = f"{value} {label_text}".lower()
                        
                        # Entity type selection (LLC)
                        if any(word in group_name_lower for word in ['legal', 'structure', 'entity', 'organization']):
                            if 'llc' in combined_info or 'limited liability' in combined_info:
                                try:
                                    if radio_id:
                                        label_elem = await self.page.locator(f'label[for="{radio_id}"]')
                                        await label_elem.click()
                                    else:
                                        await radio.click()
                                    logger.info(f"Selected entity type: {label_text}")
                                    filled_count += 1
                                    await self.human_delay()
                                    break
                                except:
                                    pass
                        
                        # Employee questions
                        elif any(word in group_name_lower for word in ['employee', 'hire', 'worker']):
                            has_employees = self.data['business_details'].get('has_employees', False)
                            if (has_employees and 'yes' in combined_info) or (not has_employees and 'no' in combined_info):
                                try:
                                    await radio.click()
                                    logger.info(f"Selected employee option: {label_text}")
                                    filled_count += 1
                                    await self.human_delay()
                                    break
                                except:
                                    pass
                        
                        # Reason for applying
                        elif any(word in group_name_lower for word in ['reason', 'purpose', 'applying']):
                            reason = self.data['business_details'].get('reason_for_applying', '').lower()
                            if reason and reason in combined_info:
                                try:
                                    await radio.click()
                                    logger.info(f"Selected reason: {label_text}")
                                    filled_count += 1
                                    await self.human_delay()
                                    break
                                except:
                                    pass
                    
                    except Exception as e:
                        logger.debug(f"Radio button handling error: {e}")
                        continue
            
            except Exception as e:
                logger.warning(f"Radio group {group_name} handling failed: {e}")
                continue
        
        # Checkboxes
        checkboxes = await self.page.locator('input[type="checkbox"]').all()
        
        for checkbox in checkboxes:
            try:
                if await checkbox.is_visible() and await checkbox.is_enabled():
                    checkbox_id = await checkbox.get_attribute('id') or ""
                    name = (await checkbox.get_attribute('name') or "").lower()
                    
                    # Find label
                    label_text = ""
                    if checkbox_id:
                        try:
                            label = await self.page.locator(f'label[for="{checkbox_id}"]').first
                            label_text = (await label.inner_text()).lower()
                        except:
                            pass
                    
                    combined_info = f"{name} {label_text}".lower()
                    
                    # Third party designee
                    if any(word in combined_info for word in ['third', 'party', 'designee']):
                        designate = self.data['third_party_designee'].get('designate_third_party', False)
                        current_checked = await checkbox.is_checked()
                        
                        if designate != current_checked:
                            await checkbox.click()
                            logger.info(f"Set third party designee: {designate}")
                            filled_count += 1
                            await self.human_delay()
            
            except Exception as e:
                logger.warning(f"Checkbox handling failed: {e}")
                continue
        
        logger.info(f"Filled {filled_count} fields on this page")
        return filled_count
    
    async def is_final_submission_page(self):
        """Check if we're at the final submission page"""
        try:
            page_text = await self.page.inner_text('body')
            url = self.page.url.lower()
            title = await self.page.title()
            
            # Check for submission indicators
            submission_indicators = [
                'submit your application',
                'submit application',
                'review and submit',
                'final step',
                'complete your application',
                'submit for processing'
            ]
            
            page_text_lower = page_text.lower()
            title_lower = title.lower()
            
            # Check text content
            for indicator in submission_indicators:
                if indicator in page_text_lower or indicator in title_lower:
                    return True
            
            # Check URL patterns
            if any(word in url for word in ['submit', 'final', 'complete', 'review']):
                return True
            
            # Check for submit buttons (but not continue buttons)
            submit_buttons = await self.page.locator('button:has-text("Submit"), input[value*="Submit"]').all()
            continue_buttons = await self.page.locator('button:has-text("Continue"), input[value="Continue"]').all()
            
            # If we have submit buttons but no continue buttons, likely final page
            if len(submit_buttons) > 0 and len(continue_buttons) == 0:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking submission page: {e}")
            return False
    
    def show_final_review_modal(self):
        """Show final review modal before submission"""
        try:
            root = tk.Tk()
            root.title("EIN Application - Final Review")
            root.geometry("900x700")
            root.configure(bg='white')
            
            # Main frame
            main_frame = tk.Frame(root, bg='white', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, text="EIN APPLICATION READY FOR SUBMISSION!", 
                                 font=("Arial", 16, "bold"), fg="green", bg='white')
            title_label.pack(pady=(0, 20))
            
            # Instructions
            instructions = tk.Label(main_frame, 
                                  text="The EIN application form has been completely filled out.\n"
                                       "Please review all information in the browser window before proceeding.\n\n"
                                       "What happens next:\n"
                                       "• Click 'PROCEED TO SUBMIT' to go back to the browser\n"
                                       "• Review all filled information one final time\n"
                                       "• Click the final 'Submit' button on the IRS website\n"
                                       "• Your EIN will be issued immediately if approved",
                                  font=("Arial", 11), justify=tk.LEFT, bg='white')
            instructions.pack(pady=(0, 20))
            
            # Data summary
            summary_frame = tk.Frame(main_frame, bg='#f0f0f0', relief=tk.RIDGE, bd=2)
            summary_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            summary_label = tk.Label(summary_frame, text="Application Summary:", 
                                   font=("Arial", 12, "bold"), bg='#f0f0f0')
            summary_label.pack(pady=(10, 5))
            
            # Create summary text
            summary_text = f"""Business Name: {self.data['business_info']['legal_name']}
Entity Type: {self.data['entity_info']['entity_type']}
Responsible Party: {self.data['responsible_party']['name']}
Business Address: {self.data['business_info']['mailing_address']['street']}
                 {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']} {self.data['business_info']['mailing_address']['zip_code']}
Principal Activity: {self.data['business_details'].get('principal_activity', 'N/A')}

Screenshots saved: {len(self.screenshots)} images in screenshots/ folder
"""
            
            text_widget = tk.Text(summary_frame, height=12, width=70, wrap=tk.WORD, 
                                font=("Courier", 9), bg='white', state=tk.NORMAL)
            text_widget.insert(tk.END, summary_text)
            text_widget.config(state=tk.DISABLED)
            text_widget.pack(padx=10, pady=(0, 10))
            
            # Buttons
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(pady=10)
            
            result = {'proceed': False}
            
            def proceed():
                result['proceed'] = True
                root.quit()
                root.destroy()
            
            def cancel():
                result['proceed'] = False
                root.quit()
                root.destroy()
            
            proceed_btn = tk.Button(button_frame, text="PROCEED TO SUBMIT", 
                                  command=proceed, bg="#28a745", fg="white", 
                                  font=("Arial", 12, "bold"), padx=20, pady=10)
            proceed_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            cancel_btn = tk.Button(button_frame, text="CANCEL", 
                                 command=cancel, bg="#dc3545", fg="white", 
                                 font=("Arial", 12), padx=20, pady=10)
            cancel_btn.pack(side=tk.LEFT)
            
            # Center window
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
            y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
            root.geometry(f"+{x}+{y}")
            
            root.mainloop()
            return result['proceed']
            
        except Exception as e:
            logger.error(f"Modal error: {e}")
            # Fallback to console
            print("\\n" + "="*60)
            print("EIN APPLICATION READY FOR SUBMISSION!")
            print("="*60)
            print("Please review the form in the browser window.")
            response = input("Type 'yes' to proceed with submission: ").lower().strip()
            return response == 'yes'
    
    async def run_complete_automation(self):
        """Run the complete EIN form automation"""
        try:
            print("Starting complete EIN form automation...")
            
            await self.setup_browser()
            await self.navigate_to_form()
            
            # Handle first page (legal structure)
            if 'legalStructure' in self.page.url:
                await self.handle_legal_structure_page()
            
            # Process all remaining form pages
            max_pages = 25
            current_page = 1
            
            while current_page <= max_pages:
                logger.info(f"\\n=== Processing Form Page {current_page} ===")
                
                current_url = self.page.url
                logger.info(f"Current URL: {current_url}")
                
                # Check if final submission page
                if await self.is_final_submission_page():
                    logger.info("REACHED FINAL SUBMISSION PAGE!")
                    await self.take_screenshot("final_submission_page")
                    
                    # Show review modal
                    proceed = self.show_final_review_modal()
                    
                    if proceed:
                        print("\\n" + "="*60)
                        print("RETURNING TO BROWSER FOR FINAL SUBMISSION")
                        print("="*60)
                        print("Please click the final 'Submit' button in the browser.")
                        print("Your EIN will be issued immediately upon successful submission.")
                        print("The browser will remain open for you to complete the submission.")
                        print("="*60)
                        
                        # Don't close browser - let user submit manually
                        return "SUCCESS_READY_FOR_MANUAL_SUBMISSION"
                    else:
                        print("User cancelled submission.")
                        return "CANCELLED_BY_USER"
                
                # Fill form fields on current page
                fields_filled = await self.fill_form_fields_comprehensive()
                
                if fields_filled > 0:
                    await self.take_screenshot(f"page_{current_page}_filled")
                    logger.info(f"Filled {fields_filled} fields on page {current_page}")
                else:
                    logger.info(f"No fields filled on page {current_page}")
                
                # Try to continue to next page
                if not await self.click_continue_button():
                    logger.warning("Could not find continue button - checking if at final page...")
                    
                    # Wait and check again for final page
                    await asyncio.sleep(2)
                    if await self.is_final_submission_page():
                        continue  # This will trigger the final page handling above
                    
                    logger.info("No continue button found and not final page - automation complete")
                    break
                
                current_page += 1
                await asyncio.sleep(1)  # Brief pause between pages
            
            # If we exit without finding final submission page
            await self.take_screenshot("automation_completed")
            print("\\n" + "="*60)
            print("FORM AUTOMATION COMPLETED")
            print("="*60)
            print("All form pages have been processed.")
            print("Please review the form in the browser window and submit manually.")
            print("="*60)
            
            return "COMPLETED_CHECK_BROWSER"
            
        except Exception as e:
            logger.error(f"Complete automation failed: {e}")
            await self.take_screenshot("error_state")
            return f"ERROR: {e}"

async def main():
    print("Complete EIN Form Automation")
    print("="*50)
    print("This script will:")
    print("- Fill out the entire EIN application form")
    print("- Stop at the final submission page")
    print("- Show you a review modal before submission")
    print("- Let you manually click the final submit button")
    print("="*50)
    
    automation = CompleteEINAutomation()
    
    try:
        result = await automation.run_complete_automation()
        
        print(f"\\nAutomation Result: {result}")
        
        if "SUCCESS" in result:
            print("\\nAutomation completed successfully!")
            print("The EIN application is ready for your final submission.")
        elif "ERROR" in result:
            print(f"\\nAutomation encountered an error: {result}")
        else:
            print(f"\\nAutomation completed: {result}")
        
    except KeyboardInterrupt:
        print("\\nAutomation interrupted by user")
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
    
    print("\\nBrowser window will remain open for your review.")
    print("Close it manually when you're finished.")

if __name__ == "__main__":
    asyncio.run(main())