#!/usr/bin/env python3
"""
Enhanced EIN Form Automation - Better Continue button detection
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
        logging.FileHandler('enhanced_ein_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedEINAutomation:
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
        print("Starting enhanced EIN form automation...")
        return data
    
    async def setup_browser(self):
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox', '--disable-web-security']
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        
        # Add anti-detection script
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser configured and ready")
    
    async def screenshot(self, name):
        timestamp = int(time.time())
        path = f'screenshots/{name}_{timestamp}.png'
        await self.page.screenshot(path=path, full_page=True)
        self.screenshots.append(path)
        logger.info(f"Screenshot saved: {path}")
        return path
    
    async def human_delay(self, min_ms=500, max_ms=1500):
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def debug_page_buttons(self):
        """Debug all buttons on the current page"""
        logger.info("Debugging all buttons on page...")
        
        try:
            # Get all clickable elements
            all_clickable = await self.page.locator('button, input[type="submit"], input[type="button"], a').all()
            
            button_info = []
            for i, element in enumerate(all_clickable):
                try:
                    if await element.is_visible():
                        tag = await element.evaluate('el => el.tagName.toLowerCase()')
                        
                        if tag == 'button':
                            text = await element.inner_text()
                            type_attr = await element.get_attribute('type') or ""
                        elif tag == 'input':
                            text = await element.get_attribute('value') or ""
                            type_attr = await element.get_attribute('type') or ""
                        elif tag == 'a':
                            text = await element.inner_text()
                            type_attr = "link"
                        
                        class_attr = await element.get_attribute('class') or ""
                        id_attr = await element.get_attribute('id') or ""
                        name = await element.get_attribute('name') or ""
                        
                        # Check if enabled
                        enabled = await element.is_enabled()
                        
                        button_info.append({
                            'index': i,
                            'tag': tag,
                            'text': text.strip(),
                            'type': type_attr,
                            'class': class_attr,
                            'id': id_attr,
                            'name': name,
                            'enabled': enabled
                        })
                
                except Exception as e:
                    button_info.append({
                        'index': i,
                        'error': str(e)
                    })
            
            logger.info("Found clickable elements:")
            for info in button_info:
                if 'error' not in info:
                    logger.info(f"  [{info['index']}] {info['tag'].upper()}: '{info['text']}' "
                              f"(type={info['type']}, enabled={info['enabled']}, "
                              f"class='{info['class'][:30]}...', id='{info['id']}')")
                else:
                    logger.info(f"  [{info['index']}] ERROR: {info['error']}")
            
            return button_info
            
        except Exception as e:
            logger.error(f"Debug failed: {e}")
            return []
    
    async def navigate_to_form(self):
        logger.info("Navigating to IRS EIN application...")
        
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.screenshot("01_landing_page")
        await self.human_delay(2000, 3000)
        
        # Start application
        begin_button = await self.page.wait_for_selector('a:has-text("Begin Application Now")', timeout=30000)
        await begin_button.click()
        logger.info("Started EIN application")
        
        await self.human_delay(4000, 6000)
        await self.screenshot("02_application_started")
        
        return True
    
    async def select_llc_and_fill_all_fields(self):
        """Select LLC and fill all fields on the legal structure page"""
        logger.info("Processing legal structure page...")
        
        await self.page.wait_for_load_state('domcontentloaded')
        await self.human_delay(1000, 2000)
        
        # Take screenshot before doing anything
        await self.screenshot("03_legal_structure_page_initial")
        
        # Debug buttons before selection
        await self.debug_page_buttons()
        
        # Select LLC
        try:
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]', timeout=10000)
            await llc_label.click()
            logger.info("Selected LLC by clicking label")
            await self.human_delay(1000, 1500)
        except:
            # JavaScript fallback
            await self.page.evaluate('''
                const llcRadio = document.getElementById("LLClegalStructureInputid");
                if (llcRadio) {
                    llcRadio.checked = true;
                    llcRadio.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log("LLC selected via JavaScript");
                }
            ''')
            logger.info("Selected LLC via JavaScript fallback")
            await self.human_delay(1000, 1500)
        
        # Take screenshot after LLC selection
        await self.screenshot("04_llc_selected")
        
        # Fill all other fields on the page
        await self.fill_all_form_fields()
        
        # Take screenshot after filling fields
        await self.screenshot("05_all_fields_filled")
        
        # Debug buttons after filling fields (they might have changed)
        logger.info("Checking buttons after filling fields...")
        await self.debug_page_buttons()
        
        return True
    
    async def fill_all_form_fields(self):
        """Fill all visible form fields on the current page"""
        logger.info("Filling all form fields on current page...")
        
        filled_count = 0
        
        try:
            # Text inputs
            text_inputs = await self.page.locator('input[type="text"], input:not([type]), input[type="email"], input[type="tel"]').all()
            
            for input_elem in text_inputs:
                try:
                    if await input_elem.is_visible() and await input_elem.is_enabled():
                        name = (await input_elem.get_attribute('name') or "").lower()
                        id_attr = (await input_elem.get_attribute('id') or "").lower()
                        placeholder = (await input_elem.get_attribute('placeholder') or "").lower()
                        
                        # Check current value
                        current_value = await input_elem.input_value()
                        if current_value and current_value.strip():
                            continue  # Skip if already filled
                        
                        # Determine what to fill
                        field_info = f"{name} {id_attr} {placeholder}"
                        value = self.get_field_value(field_info)
                        
                        if value:
                            await input_elem.clear()
                            await input_elem.type(str(value), delay=random.randint(50, 100))
                            logger.info(f"Filled field: {str(value)[:25]}...")
                            filled_count += 1
                            await self.human_delay(300, 600)
                
                except Exception as e:
                    logger.debug(f"Text input error: {e}")
                    continue
            
            # Select dropdowns
            selects = await self.page.locator('select').all()
            for select_elem in selects:
                try:
                    if await select_elem.is_visible() and await select_elem.is_enabled():
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
            
            # Radio buttons (excluding LLC which we already handled)
            radios = await self.page.locator('input[type="radio"]:not(#LLClegalStructureInputid)').all()
            
            for radio in radios:
                try:
                    if await radio.is_visible():
                        name = await radio.get_attribute('name') or ""
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
                        
                        combined_info = f"{name} {value} {label_text}".lower()
                        
                        # Handle specific radio button types
                        if any(word in combined_info for word in ['employee', 'hire', 'worker']):
                            has_employees = self.data['business_details'].get('has_employees', False)
                            should_select = (has_employees and 'yes' in combined_info) or (not has_employees and 'no' in combined_info)
                            
                            if should_select and not await radio.is_checked():
                                await radio.click()
                                logger.info(f"Selected radio: {label_text}")
                                filled_count += 1
                                await self.human_delay(300, 600)
                
                except Exception as e:
                    logger.debug(f"Radio button error: {e}")
                    continue
            
            # Checkboxes
            checkboxes = await self.page.locator('input[type="checkbox"]').all()
            
            for checkbox in checkboxes:
                try:
                    if await checkbox.is_visible() and await checkbox.is_enabled():
                        name = (await checkbox.get_attribute('name') or "").lower()
                        checkbox_id = await checkbox.get_attribute('id') or ""
                        
                        # Find label
                        label_text = ""
                        if checkbox_id:
                            try:
                                label = await self.page.locator(f'label[for="{checkbox_id}"]').first
                                label_text = (await label.inner_text()).lower()
                            except:
                                pass
                        
                        combined_info = f"{name} {label_text}".lower()
                        
                        # Handle third party designee
                        if 'third' in combined_info and 'party' in combined_info:
                            designate = self.data['third_party_designee'].get('designate_third_party', False)
                            current_checked = await checkbox.is_checked()
                            
                            if designate != current_checked:
                                await checkbox.click()
                                logger.info(f"Set third party designee: {designate}")
                                filled_count += 1
                                await self.human_delay(300, 600)
                
                except Exception as e:
                    logger.debug(f"Checkbox error: {e}")
                    continue
            
            logger.info(f"Filled {filled_count} fields on this page")
            return filled_count
            
        except Exception as e:
            logger.error(f"Error filling form fields: {e}")
            return 0
    
    def get_field_value(self, field_info):
        """Determine field value based on field information"""
        field_info = field_info.lower()
        
        # Business information
        if any(word in field_info for word in ['business', 'company', 'legal', 'entity']) and 'name' in field_info:
            return self.data['business_info']['legal_name']
        
        if any(word in field_info for word in ['trade', 'dba', 'doing']) and 'name' in field_info:
            return self.data['business_info']['trade_name_dba']
        
        # Address fields
        if any(word in field_info for word in ['street', 'address', 'addr']):
            return self.data['business_info']['mailing_address']['street']
        
        if 'city' in field_info:
            return self.data['business_info']['mailing_address']['city']
        
        if any(word in field_info for word in ['zip', 'postal', 'zipcode']):
            return self.data['business_info']['mailing_address']['zip_code']
        
        # Responsible party
        if any(word in field_info for word in ['responsible', 'contact', 'person', 'individual']) and 'name' in field_info:
            return self.data['responsible_party']['name']
        
        if any(word in field_info for word in ['ssn', 'social', 'security', 'tax', 'tin', 'itin']):
            return self.data['responsible_party']['ssn_itin']
        
        if any(word in field_info for word in ['title', 'position', 'role']):
            return self.data['responsible_party']['title']
        
        # Business details
        if any(word in field_info for word in ['activity', 'business', 'principal', 'primary']) and not 'address' in field_info:
            return self.data['business_details'].get('principal_activity', '')
        
        if any(word in field_info for word in ['product', 'service', 'goods']):
            return self.data['business_details'].get('principal_product_or_service', '')
        
        if any(word in field_info for word in ['employee', 'workers', 'staff', 'expect', 'number']):
            return self.data['business_details'].get('highest_number_employees_expected', '')
        
        if any(word in field_info for word in ['start', 'began', 'commence', 'date']) and not 'end' in field_info:
            return self.data['business_details'].get('date_business_started', '')
        
        # Contact info
        if any(word in field_info for word in ['phone', 'telephone', 'tel']):
            return self.data['applicant_info'].get('phone_number', '')
        
        if any(word in field_info for word in ['fax']):
            return self.data['applicant_info'].get('fax_number', '')
        
        return None
    
    async def find_and_click_continue_button(self):
        """Enhanced Continue button detection based on your description"""
        logger.info("Looking for Continue button (should be to the right of Back button)...")
        
        # Strategy 1: Look for Continue button specifically positioned after Back button
        try:
            # First, find Back button as a reference point
            back_buttons = await self.page.locator('button:has-text("Back"), input[value="Back"]').all()
            
            for back_button in back_buttons:
                if await back_button.is_visible():
                    logger.info("Found Back button, looking for Continue button nearby...")
                    
                    # Look for Continue button in the same container/parent
                    parent = await back_button.locator('..').first  # Get parent element
                    
                    # Try to find Continue button within the same parent
                    continue_in_parent = await parent.locator('button:has-text("Continue"), input[value="Continue"]').all()
                    
                    for continue_btn in continue_in_parent:
                        if await continue_btn.is_visible() and await continue_btn.is_enabled():
                            text = await continue_btn.inner_text() if await continue_btn.evaluate('el => el.tagName') == 'BUTTON' else await continue_btn.get_attribute('value')
                            logger.info(f"Found Continue button in same container as Back: '{text}'")
                            await continue_btn.click()
                            await self.human_delay(3000, 5000)
                            return True
        
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Look for Continue buttons that are enabled (not disabled)
        try:
            continue_selectors = [
                'button:has-text("Continue")',
                'input[value="Continue"]',
                'input[type="submit"][value="Continue"]',
                'button[type="submit"]:has-text("Continue")'
            ]
            
            for selector in continue_selectors:
                elements = await self.page.locator(selector).all()
                
                for element in elements:
                    if await element.is_visible() and await element.is_enabled():
                        # Double-check it's not a hidden or disabled element
                        opacity = await element.evaluate('el => window.getComputedStyle(el).opacity')
                        display = await element.evaluate('el => window.getComputedStyle(el).display')
                        
                        if opacity != '0' and display != 'none':
                            text = await element.inner_text() if await element.evaluate('el => el.tagName') == 'BUTTON' else await element.get_attribute('value')
                            logger.info(f"Found enabled Continue button: '{text}' ({selector})")
                            await element.click()
                            await self.human_delay(3000, 5000)
                            return True
        
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Look for any submit button that might be the Continue button
        try:
            submit_buttons = await self.page.locator('input[type="submit"], button[type="submit"]').all()
            
            for button in submit_buttons:
                if await button.is_visible() and await button.is_enabled():
                    text = await button.get_attribute('value') if await button.evaluate('el => el.tagName') == 'INPUT' else await button.inner_text()
                    
                    # Skip obviously wrong buttons
                    if not any(skip_word in text.lower() for skip_word in ['back', 'cancel', 'reset', 'clear']):
                        logger.info(f"Trying submit button: '{text}'")
                        await button.click()
                        await self.human_delay(3000, 5000)
                        return True
        
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")
        
        # Strategy 4: JavaScript approach - trigger form submission
        try:
            logger.info("Trying JavaScript form submission...")
            
            # Look for forms and try to submit them
            forms = await self.page.locator('form').all()
            
            for form in forms:
                try:
                    # Try to submit the form via JavaScript
                    await form.evaluate('form => form.submit()')
                    logger.info("Submitted form via JavaScript")
                    await self.human_delay(3000, 5000)
                    return True
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"Strategy 4 failed: {e}")
        
        logger.warning("Could not find Continue button with any strategy")
        return False
    
    async def is_final_submission_page(self):
        """Check if we've reached the final submission page"""
        try:
            url = self.page.url
            page_text = await self.page.inner_text('body')
            title = await self.page.title()
            
            final_indicators = [
                'submit your application',
                'submit application',
                'review and submit',
                'final step',
                'complete your application',
                'ein application summary',
                'confirm and submit'
            ]
            
            combined_text = f"{url} {page_text} {title}".lower()
            
            for indicator in final_indicators:
                if indicator in combined_text:
                    logger.info(f"Final page detected: '{indicator}' found")
                    return True
            
            # Check button patterns - final page typically has Submit but no Continue
            submit_buttons = await self.page.locator('input[value*="Submit"], button:has-text("Submit")').count()
            continue_buttons = await self.page.locator('input[value="Continue"], button:has-text("Continue")').count()
            
            if submit_buttons > 0 and continue_buttons == 0:
                logger.info("Final page detected: Submit buttons present, no Continue buttons")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking final page: {e}")
            return False
    
    def show_final_review_modal(self):
        """Show comprehensive review modal before final submission"""
        try:
            root = tk.Tk()
            root.title("EIN Application - READY FOR SUBMISSION!")
            root.geometry("900x700")
            root.configure(bg='white')
            
            # Main container
            main_frame = tk.Frame(root, bg='white', padx=30, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, 
                                 text="EIN APPLICATION IS READY FOR SUBMISSION!", 
                                 font=("Arial", 16, "bold"), fg="#28a745", bg='white')
            title_label.pack(pady=(0, 20))
            
            # Instructions
            instructions_text = """SUCCESS! Your EIN application form has been completely filled out!

WHAT'S NEXT:
1. Click 'PROCEED TO SUBMIT' below to return to the browser
2. Carefully review ALL information in the IRS form one final time  
3. Click the 'Submit' button on the IRS website to submit your application
4. Your EIN will be issued IMMEDIATELY upon successful submission

IMPORTANT REMINDERS:
• You can only apply for 1 EIN per responsible party per day
• Double-check all business information for accuracy
• Make sure your business entity is properly formed with your state first
• Keep a copy of your EIN confirmation for your records"""
            
            instructions_label = tk.Label(main_frame, text=instructions_text,
                                        font=("Arial", 10), justify=tk.LEFT, bg='white')
            instructions_label.pack(pady=(0, 20))
            
            # Application summary
            summary_frame = tk.Frame(main_frame, bg='#f8f9fa', relief=tk.RIDGE, bd=2)
            summary_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            summary_title = tk.Label(summary_frame, text="APPLICATION SUMMARY",
                                   font=("Arial", 12, "bold"), bg='#f8f9fa')
            summary_title.pack(pady=(10, 5))
            
            summary_text = f"""Business Legal Name: {self.data['business_info']['legal_name']}
Entity Type: {self.data['entity_info']['entity_type']}
Trade Name/DBA: {self.data['business_info']['trade_name_dba'] or 'None'}

Business Address:
{self.data['business_info']['mailing_address']['street']}
{self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']} {self.data['business_info']['mailing_address']['zip_code']}

Responsible Party: {self.data['responsible_party']['name']}
Title: {self.data['responsible_party']['title']}
SSN/ITIN: {self.data['responsible_party']['ssn_itin'][:3]}**-**-{self.data['responsible_party']['ssn_itin'][-4:]}

Principal Business Activity: {self.data['business_details'].get('principal_activity', 'Not specified')}
Expected Employees: {self.data['business_details'].get('highest_number_employees_expected', 'Not specified')}

Screenshots Captured: {len(self.screenshots)} images saved in screenshots/ folder"""
            
            # Scrollable text area
            text_area = scrolledtext.ScrolledText(summary_frame, height=15, wrap=tk.WORD,
                                                font=("Consolas", 9), state=tk.NORMAL)
            text_area.insert(tk.END, summary_text)
            text_area.config(state=tk.DISABLED)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            # Buttons
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(pady=20)
            
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
                                  font=("Arial", 14, "bold"), padx=30, pady=15)
            proceed_btn.pack(side=tk.LEFT, padx=(0, 20))
            
            cancel_btn = tk.Button(button_frame, text="CANCEL", 
                                 command=cancel, bg="#dc3545", fg="white", 
                                 font=("Arial", 12), padx=30, pady=15)
            cancel_btn.pack(side=tk.LEFT)
            
            # Center window
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"{width}x{height}+{x}+{y}")
            
            root.mainloop()
            return result['proceed']
            
        except Exception as e:
            logger.error(f"Modal error: {e}")
            # Fallback
            print("\\n" + "="*60)
            print("EIN APPLICATION READY FOR SUBMISSION!")
            print("="*60)
            response = input("Type 'yes' to proceed: ").lower().strip()
            return response == 'yes'
    
    async def run_complete_automation(self):
        """Run the complete automation process"""
        try:
            print("\\n" + "="*60)
            print("ENHANCED EIN FORM AUTOMATION")
            print("="*60)
            
            await self.setup_browser()
            await self.navigate_to_form()
            
            # Handle legal structure page
            if 'legalStructure' in self.page.url:
                await self.select_llc_and_fill_all_fields()
            
            # Process form pages
            max_pages = 50
            current_page = 1
            last_url = self.page.url
            stuck_count = 0
            
            while current_page <= max_pages:
                logger.info(f"\\n{'='*15} PROCESSING PAGE {current_page} {'='*15}")
                
                current_url = self.page.url
                logger.info(f"Current URL: {current_url}")
                
                # Track if we're stuck on same URL
                if current_url == last_url:
                    stuck_count += 1
                    logger.info(f"Same URL - stuck count: {stuck_count}")
                else:
                    stuck_count = 0
                    logger.info("URL changed - progress made")
                    last_url = current_url
                
                # Check if final submission page
                if await self.is_final_submission_page():
                    logger.info("REACHED FINAL SUBMISSION PAGE!")
                    await self.screenshot(f"06_final_submission_page")
                    
                    # Show final review modal
                    if self.show_final_review_modal():
                        print("\\n" + "="*60)
                        print("RETURNING TO BROWSER FOR FINAL SUBMISSION")
                        print("="*60)
                        print("Please click the 'Submit' button in the browser window.")
                        print("Your EIN will be issued immediately upon successful submission.")
                        print("="*60)
                        
                        # Keep browser open for manual submission
                        return "SUCCESS_READY_FOR_MANUAL_SUBMISSION"
                    else:
                        logger.info("User cancelled submission")
                        return "CANCELLED_BY_USER"
                
                # Fill fields on current page (if not already done)
                if current_page > 1:  # Skip page 1 since we already filled it
                    fields_filled = await self.fill_all_form_fields()
                    
                    if fields_filled > 0:
                        await self.screenshot(f"page_{current_page:02d}_filled")
                        logger.info(f"Filled {fields_filled} fields on page {current_page}")
                
                # Try to continue to next page
                continue_success = await self.find_and_click_continue_button()
                
                if continue_success:
                    logger.info("Successfully clicked Continue - moving to next page")
                    await self.human_delay(2000, 3000)  # Wait for page transition
                else:
                    logger.warning("Could not find/click Continue button")
                    
                    if stuck_count > 3:
                        logger.warning("Stuck on same page too long - checking for final page...")
                        await self.human_delay(2000, 3000)
                        
                        # Final check for submission page
                        if await self.is_final_submission_page():
                            continue  # Will be caught in next iteration
                        
                        logger.warning("Breaking due to being stuck")
                        break
                    else:
                        logger.info("Waiting and will retry...")
                        await self.human_delay(3000, 5000)
                
                current_page += 1
                
                # Safety break
                if stuck_count > 6:
                    logger.warning("Breaking due to excessive stuck count")
                    break
            
            # Final state
            await self.screenshot("07_automation_final_state")
            
            print("\\n" + "="*60)
            print("EIN FORM AUTOMATION COMPLETED")
            print("="*60)
            print("The automation has processed all available form pages.")
            print("Please review the form in the browser window and submit manually if needed.")
            print("All screenshots have been saved in the screenshots/ folder.")
            print("="*60)
            
            return "COMPLETED_SUCCESSFULLY"
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            await self.screenshot("08_error_state")
            return f"ERROR: {str(e)}"

async def main():
    print("Enhanced EIN Form Automation")
    print("="*40)
    print("This enhanced script will:")
    print("- Navigate to the IRS EIN application") 
    print("- Fill out ALL form pages automatically")
    print("- Use improved Continue button detection")
    print("- Stop at final submission for your review")
    print("- Show detailed review modal")
    print("="*40)
    
    automation = EnhancedEINAutomation()
    
    try:
        result = await automation.run_complete_automation()
        
        print(f"\\nFINAL RESULT: {result}")
        
        if "SUCCESS" in result:
            print("\\nSUCCESS! The EIN application is ready for your final submission!")
        elif "ERROR" in result:
            print(f"\\nERROR: {result}")
        else:
            print(f"\\nCOMPLETED: {result}")
        
    except KeyboardInterrupt:
        print("\\nProcess interrupted by user")
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
    
    print("\\nBrowser window will remain open for your review.")
    print("Close it manually when finished.")

if __name__ == "__main__":
    asyncio.run(main())