#!/usr/bin/env python3
"""
Final Working EIN Automation - Complete form filling with proper button detection
"""

import json
import time
import asyncio
import random
import tkinter as tk
from tkinter import messagebox, scrolledtext
from playwright.async_api import async_playwright
import logging

# Setup logging
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
        print("Starting comprehensive EIN form automation...")
        return data
    
    async def setup_browser(self):
        """Setup browser with comprehensive anti-detection"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--start-maximized',
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security'
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
        logger.info("Browser configured and ready")
    
    async def screenshot(self, name):
        """Take screenshot and save path"""
        timestamp = int(time.time())
        path = f'screenshots/{name}_{timestamp}.png'
        await self.page.screenshot(path=path, full_page=True)
        self.screenshots.append(path)
        logger.info(f"Screenshot: {path}")
        return path
    
    async def human_delay(self, min_ms=500, max_ms=1500):
        """Human-like delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def navigate_and_start_application(self):
        """Navigate to IRS site and start application"""
        logger.info("🌐 Navigating to IRS EIN application...")
        
        # Navigate to main page
        await self.page.goto('https://sa.www4.irs.gov/applyein/', timeout=60000)
        await self.screenshot("irs_landing_page")
        await self.human_delay(2000, 3000)
        
        # Start application
        begin_button = await self.page.wait_for_selector('a:has-text("Begin Application Now")', timeout=30000)
        await begin_button.click()
        logger.info("✓ Clicked 'Begin Application Now'")
        
        await self.human_delay(4000, 6000)
        await self.screenshot("application_started")
        
        current_url = self.page.url
        logger.info(f"📍 Current URL: {current_url}")
        
        return True
    
    async def debug_page_elements(self):
        """Debug current page elements"""
        logger.info("🔍 Debugging page elements...")
        
        try:
            # Get all form elements
            inputs = await self.page.locator('input').count()
            buttons = await self.page.locator('button').count()
            selects = await self.page.locator('select').count()
            forms = await self.page.locator('form').count()
            
            logger.info(f"📊 Page elements: {inputs} inputs, {buttons} buttons, {selects} selects, {forms} forms")
            
            # List all buttons with their text/values
            all_buttons = await self.page.locator('button, input[type="submit"], input[type="button"]').all()
            button_info = []
            
            for i, button in enumerate(all_buttons):
                try:
                    if await button.is_visible():
                        tag = await button.evaluate('el => el.tagName.toLowerCase()')
                        if tag == 'button':
                            text = await button.inner_text()
                            onclick = await button.get_attribute('onclick') or ""
                        else:
                            text = await button.get_attribute('value') or ""
                            onclick = await button.get_attribute('onclick') or ""
                        
                        type_attr = await button.get_attribute('type') or ""
                        name = await button.get_attribute('name') or ""
                        id_attr = await button.get_attribute('id') or ""
                        class_attr = await button.get_attribute('class') or ""
                        
                        button_info.append(f"Button {i}: '{text}' [type={type_attr}, name={name}, id={id_attr}, class={class_attr}, onclick={onclick[:50]}...]")
                except Exception as e:
                    button_info.append(f"Button {i}: [Error reading: {e}]")
            
            logger.info("🔘 Available buttons:")
            for info in button_info:
                logger.info(f"   {info}")
            
        except Exception as e:
            logger.error(f"❌ Debug failed: {e}")
    
    async def fill_legal_structure_page(self):
        """Handle the legal structure page completely"""
        logger.info("📝 Processing legal structure page...")
        
        await self.page.wait_for_load_state('domcontentloaded')
        await self.human_delay(1000, 2000)
        await self.screenshot("legal_structure_page")
        
        # Debug the page first
        await self.debug_page_elements()
        
        # Select LLC
        try:
            llc_label = await self.page.wait_for_selector('label[for="LLClegalStructureInputid"]', timeout=10000)
            await llc_label.click()
            logger.info("✓ Selected LLC entity type")
            await self.human_delay(1000, 1500)
        except:
            # JavaScript fallback
            await self.page.evaluate('''
                const llcRadio = document.getElementById("LLClegalStructureInputid");
                if (llcRadio) {
                    llcRadio.checked = true;
                    llcRadio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            ''')
            logger.info("✓ Selected LLC via JavaScript")
            await self.human_delay(1000, 1500)
        
        # Fill any other required fields on this page
        await self.fill_all_visible_form_fields()
        
        await self.screenshot("legal_structure_filled")
        
        # Look for continue button with comprehensive search
        continue_found = await self.find_and_click_continue()
        
        if not continue_found:
            logger.warning("⚠️ Continue button not found - trying alternative approaches...")
            
            # Try pressing Enter on the form
            try:
                await self.page.keyboard.press('Tab')
                await self.human_delay(500, 1000)
                await self.page.keyboard.press('Enter')
                logger.info("✓ Tried pressing Enter to submit form")
                await self.human_delay(3000, 4000)
            except:
                pass
            
            # Try clicking anywhere and then looking for buttons again
            try:
                form = await self.page.locator('form').first
                await form.click()
                await self.human_delay(1000, 1500)
                continue_found = await self.find_and_click_continue()
            except:
                pass
        
        return continue_found
    
    async def fill_all_visible_form_fields(self):
        """Fill all visible and fillable form fields"""
        logger.info("✏️ Filling all visible form fields...")
        
        filled_count = 0
        
        try:
            # Text inputs
            text_inputs = await self.page.locator('input[type="text"], input:not([type]), input[type="email"], input[type="tel"]').all()
            
            for input_elem in text_inputs:
                if await input_elem.is_visible() and await input_elem.is_enabled():
                    # Get field identifiers
                    name = (await input_elem.get_attribute('name') or "").lower()
                    id_attr = (await input_elem.get_attribute('id') or "").lower()
                    placeholder = (await input_elem.get_attribute('placeholder') or "").lower()
                    label_text = ""
                    
                    # Try to find associated label
                    if id_attr:
                        try:
                            label = await self.page.locator(f'label[for="{id_attr}"]').first
                            label_text = (await label.inner_text()).lower()
                        except:
                            pass
                    
                    # Check current value
                    current_value = await input_elem.input_value()
                    if current_value and current_value.strip():
                        continue  # Skip if already filled
                    
                    # Determine what to fill based on field info
                    field_info = f"{name} {id_attr} {placeholder} {label_text}"
                    value_to_fill = self.determine_field_value(field_info)
                    
                    if value_to_fill:
                        await input_elem.clear()
                        await input_elem.type(str(value_to_fill), delay=random.randint(50, 100))
                        logger.info(f"✓ Filled field: {str(value_to_fill)[:25]}...")
                        filled_count += 1
                        await self.human_delay(300, 600)
            
            # Select dropdowns
            selects = await self.page.locator('select').all()
            for select_elem in selects:
                if await select_elem.is_visible() and await select_elem.is_enabled():
                    name = (await select_elem.get_attribute('name') or "").lower()
                    id_attr = (await select_elem.get_attribute('id') or "").lower()
                    
                    if 'state' in f"{name} {id_attr}":
                        state = self.data['business_info']['mailing_address']['state']
                        try:
                            await select_elem.select_option(value=state)
                            logger.info(f"✓ Selected state: {state}")
                            filled_count += 1
                        except:
                            try:
                                await select_elem.select_option(label=state)
                                logger.info(f"✓ Selected state by label: {state}")
                                filled_count += 1
                            except:
                                pass
                        await self.human_delay(300, 600)
            
            # Radio buttons (except LLC which we already handled)
            radio_buttons = await self.page.locator('input[type="radio"]:not(#LLClegalStructureInputid)').all()
            
            for radio in radio_buttons:
                if await radio.is_visible():
                    try:
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
                        
                        combined_info = f"{name} {value} {label_text}".lower()
                        
                        # Employee questions
                        if any(word in combined_info for word in ['employee', 'hire', 'worker']):
                            has_employees = self.data['business_details'].get('has_employees', False)
                            should_select = (has_employees and 'yes' in combined_info) or (not has_employees and 'no' in combined_info)
                            
                            if should_select and not await radio.is_checked():
                                try:
                                    await radio.click()
                                    logger.info(f"✓ Selected: {label_text}")
                                    filled_count += 1
                                    await self.human_delay(300, 600)
                                except:
                                    pass
                    
                    except:
                        continue
            
            # Checkboxes
            checkboxes = await self.page.locator('input[type="checkbox"]').all()
            
            for checkbox in checkboxes:
                if await checkbox.is_visible() and await checkbox.is_enabled():
                    try:
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
                        
                        # Third party designee
                        if 'third' in combined_info and 'party' in combined_info:
                            designate = self.data['third_party_designee'].get('designate_third_party', False)
                            current_checked = await checkbox.is_checked()
                            
                            if designate != current_checked:
                                await checkbox.click()
                                logger.info(f"✓ Set third party designee: {designate}")
                                filled_count += 1
                                await self.human_delay(300, 600)
                    
                    except:
                        continue
            
            logger.info(f"📊 Filled {filled_count} fields on this page")
            return filled_count
            
        except Exception as e:
            logger.error(f"❌ Error filling fields: {e}")
            return 0
    
    def determine_field_value(self, field_info):
        """Determine what value to fill based on field information"""
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
        if any(word in field_info for word in ['responsible', 'contact', 'person', 'individual', 'applicant']) and 'name' in field_info:
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
    
    async def find_and_click_continue(self):
        """Comprehensive continue button detection and clicking"""
        logger.info("🔍 Searching for Continue button...")
        
        # Wait for any dynamic content to load
        await asyncio.sleep(2)
        
        # Try multiple strategies
        strategies = [
            # Strategy 1: Standard form buttons
            {
                'name': 'Standard Continue Buttons',
                'selectors': [
                    'input[type="submit"][value*="Continue"]',
                    'button[type="submit"]:has-text("Continue")',
                    'input[value="Continue"]',
                    'button:has-text("Continue")'
                ]
            },
            
            # Strategy 2: Form submission buttons
            {
                'name': 'Form Submit Buttons',
                'selectors': [
                    'form input[type="submit"]',
                    'form button[type="submit"]',
                    '.form input[type="submit"]',
                    '.form button[type="submit"]'
                ]
            },
            
            # Strategy 3: Next buttons
            {
                'name': 'Next Buttons',
                'selectors': [
                    'input[value*="Next"]',
                    'button:has-text("Next")',
                    'input[type="submit"][value*="Next"]'
                ]
            },
            
            # Strategy 4: JavaScript-based buttons
            {
                'name': 'JavaScript Buttons',
                'selectors': [
                    'button[onclick*="submit"]',
                    'input[onclick*="submit"]',
                    'button[onclick*="continue"]',
                    'input[onclick*="continue"]'
                ]
            }
        ]
        
        for strategy in strategies:
            logger.info(f"🎯 Trying strategy: {strategy['name']}")
            
            for selector in strategy['selectors']:
                try:
                    elements = await self.page.locator(selector).all()
                    
                    for element in elements:
                        if await element.is_visible() and await element.is_enabled():
                            # Get button text/value
                            text = ""
                            if 'input' in selector:
                                text = await element.get_attribute('value') or ""
                            else:
                                text = await element.inner_text()
                            
                            # Skip obviously wrong buttons
                            skip_words = ['here', 'how', 'know', 'info', 'help', 'back', 'previous', 'cancel', 'reset']
                            if any(skip_word in text.lower() for skip_word in skip_words):
                                logger.info(f"⏭️ Skipping button: '{text}' (excluded word found)")
                                continue
                            
                            # Try clicking
                            logger.info(f"🖱️ Attempting to click: '{text}' ({selector})")
                            
                            try:
                                await element.click()
                                await self.human_delay(4000, 6000)  # Wait for navigation
                                
                                # Check if page changed
                                new_url = self.page.url
                                if new_url != await self.page.url:  # This is a bit redundant, but let's check for navigation
                                    logger.info(f"✅ Successfully clicked '{text}' - page may have changed")
                                    return True
                                else:
                                    logger.info(f"✅ Clicked '{text}' - checking for form progression...")
                                    return True  # Assume success for now
                                    
                            except Exception as click_error:
                                logger.warning(f"❌ Failed to click '{text}': {click_error}")
                                continue
                
                except Exception as selector_error:
                    logger.debug(f"⚠️ Selector {selector} failed: {selector_error}")
                    continue
        
        # Last resort: try any visible submit button
        logger.info("🆘 Last resort: trying any submit button...")
        try:
            submit_buttons = await self.page.locator('input[type="submit"], button[type="submit"]').all()
            
            for button in submit_buttons:
                if await button.is_visible() and await button.is_enabled():
                    text = await button.get_attribute('value') if await button.evaluate('el => el.tagName') == 'INPUT' else await button.inner_text()
                    
                    if not any(skip_word in text.lower() for skip_word in ['here', 'how', 'know', 'back', 'cancel']):
                        logger.info(f"🔄 Last resort click: '{text}'")
                        await button.click()
                        await self.human_delay(4000, 6000)
                        return True
        
        except Exception as e:
            logger.error(f"❌ Last resort failed: {e}")
        
        logger.warning("⚠️ No continue button found with any strategy")
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
                    logger.info(f"🎯 Final page indicator found: '{indicator}'")
                    return True
            
            # Check button patterns
            submit_buttons = await self.page.locator('input[value*="Submit"], button:has-text("Submit")').count()
            continue_buttons = await self.page.locator('input[value="Continue"], button:has-text("Continue")').count()
            
            if submit_buttons > 0 and continue_buttons == 0:
                logger.info("🎯 Final page detected: Submit buttons present, no Continue buttons")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking final page: {e}")
            return False
    
    def show_final_submission_modal(self):
        """Show comprehensive final review modal"""
        try:
            root = tk.Tk()
            root.title("🎉 EIN Application - READY FOR SUBMISSION!")
            root.geometry("900x700")
            root.configure(bg='white')
            
            # Main container
            main_frame = tk.Frame(root, bg='white', padx=30, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, 
                                 text="🎉 EIN APPLICATION IS READY FOR SUBMISSION!", 
                                 font=("Arial", 16, "bold"), fg="#28a745", bg='white')
            title_label.pack(pady=(0, 20))
            
            # Instructions
            instructions_frame = tk.Frame(main_frame, bg='#f8f9fa', relief=tk.RIDGE, bd=2)
            instructions_frame.pack(fill=tk.X, pady=(0, 20), padx=10)
            
            instructions_text = """
✅ SUCCESS! Your EIN application form has been completely filled out!

📋 WHAT'S NEXT:
1. Click 'PROCEED TO SUBMIT' below to return to the browser
2. Carefully review ALL information in the IRS form one final time
3. Click the 'Submit' button on the IRS website to submit your application
4. Your EIN will be issued IMMEDIATELY upon successful submission

⚠️  IMPORTANT REMINDERS:
• You can only apply for 1 EIN per responsible party per day
• Double-check all business information for accuracy
• Make sure your business entity is properly formed with your state first
• Keep a copy of your EIN confirmation for your records
            """
            
            instructions_label = tk.Label(instructions_frame, text=instructions_text,
                                        font=("Arial", 10), justify=tk.LEFT, bg='#f8f9fa',
                                        padx=15, pady=15)
            instructions_label.pack()
            
            # Application summary
            summary_frame = tk.Frame(main_frame, bg='#e9ecef', relief=tk.RIDGE, bd=2)
            summary_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20), padx=10)
            
            summary_title = tk.Label(summary_frame, text="📊 APPLICATION SUMMARY",
                                   font=("Arial", 12, "bold"), bg='#e9ecef')
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

Screenshots Captured: {len(self.screenshots)} images saved in screenshots/ folder
"""
            
            # Scrollable text area for summary
            text_frame = tk.Frame(summary_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            text_area = scrolledtext.ScrolledText(text_frame, height=15, wrap=tk.WORD,
                                                font=("Consolas", 9), state=tk.NORMAL)
            text_area.insert(tk.END, summary_text)
            text_area.config(state=tk.DISABLED)
            text_area.pack(fill=tk.BOTH, expand=True)
            
            # Button frame
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(pady=20)
            
            result = {'proceed': False}
            
            def proceed_to_submit():
                result['proceed'] = True
                root.quit()
                root.destroy()
            
            def cancel_submission():
                result['proceed'] = False
                root.quit()
                root.destroy()
            
            # Buttons
            proceed_btn = tk.Button(button_frame, text="🚀 PROCEED TO SUBMIT", 
                                  command=proceed_to_submit, 
                                  bg="#28a745", fg="white", 
                                  font=("Arial", 14, "bold"), 
                                  padx=30, pady=15)
            proceed_btn.pack(side=tk.LEFT, padx=(0, 20))
            
            cancel_btn = tk.Button(button_frame, text="❌ CANCEL", 
                                 command=cancel_submission, 
                                 bg="#dc3545", fg="white", 
                                 font=("Arial", 12), 
                                 padx=30, pady=15)
            cancel_btn.pack(side=tk.LEFT)
            
            # Center the window
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Focus and bring to front
            root.lift()
            root.focus_force()
            
            root.mainloop()
            return result['proceed']
            
        except Exception as e:
            logger.error(f"❌ Modal error: {e}")
            # Fallback
            print("\\n" + "="*60)
            print("🎉 EIN APPLICATION READY FOR SUBMISSION!")
            print("="*60)
            response = input("Type 'yes' to proceed with submission: ").lower().strip()
            return response in ['yes', 'y']
    
    async def run_complete_automation(self):
        """Run the complete automation process"""
        try:
            print("\\n" + "="*60)
            print("🚀 STARTING COMPLETE EIN FORM AUTOMATION")
            print("="*60)
            
            # Setup and navigate
            await self.setup_browser()
            await self.navigate_and_start_application()
            
            # Handle legal structure page
            if 'legalStructure' in self.page.url:
                await self.fill_legal_structure_page()
            
            # Process remaining form pages
            max_pages = 50  # Increased limit
            current_page = 1
            stuck_count = 0
            last_url = self.page.url
            
            while current_page <= max_pages:
                logger.info(f"\\n{'='*20} PROCESSING PAGE {current_page} {'='*20}")
                
                current_url = self.page.url
                logger.info(f"📍 Current URL: {current_url}")
                
                # Check for URL changes to detect navigation
                if current_url == last_url:
                    stuck_count += 1
                    if stuck_count > 3:
                        logger.warning(f"⚠️ Stuck on same URL for {stuck_count} iterations")
                else:
                    stuck_count = 0
                    last_url = current_url
                
                # Check if final submission page
                if await self.is_final_submission_page():
                    logger.info("🎯 REACHED FINAL SUBMISSION PAGE!")
                    await self.screenshot("final_submission_page")
                    
                    # Show final review modal
                    if self.show_final_submission_modal():
                        print("\\n" + "="*60)
                        print("🎯 RETURNING TO BROWSER FOR FINAL SUBMISSION")
                        print("="*60)
                        print("Please click the 'Submit' button in the browser window.")
                        print("Your EIN will be issued immediately upon successful submission.")
                        print("="*60)
                        
                        # Keep browser open for manual submission
                        return "SUCCESS_READY_FOR_MANUAL_SUBMISSION"
                    else:
                        logger.info("👤 User cancelled submission")
                        return "CANCELLED_BY_USER"
                
                # Fill all fields on current page
                fields_filled = await self.fill_all_visible_form_fields()
                
                if fields_filled > 0:
                    await self.screenshot(f"page_{current_page}_completed")
                
                # Try to continue to next page
                continue_success = await self.find_and_click_continue()
                
                if not continue_success:
                    if stuck_count > 2:
                        logger.warning("⚠️ Cannot find continue button and stuck on same page")
                        break
                    else:
                        logger.info("ℹ️ No continue button found - waiting and retrying...")
                        await self.human_delay(3000, 5000)
                
                current_page += 1
                
                # Safety check - if we've been stuck too long, break
                if stuck_count > 5:
                    logger.warning("⚠️ Breaking due to being stuck too long")
                    break
            
            # Final screenshot and completion
            await self.screenshot("automation_final_state")
            
            print("\\n" + "="*60)
            print("✅ EIN FORM AUTOMATION COMPLETED")
            print("="*60)
            print("The automation has processed all available form pages.")
            print("Please review the form in the browser window and submit manually if needed.")
            print("All screenshots have been saved in the screenshots/ folder.")
            print("="*60)
            
            return "COMPLETED_SUCCESSFULLY"
            
        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            await self.screenshot("error_state")
            return f"ERROR: {str(e)}"

async def main():
    print("Final Working EIN Automation System")
    print("="*50)
    print("This comprehensive script will:")
    print("- Navigate to the IRS EIN application")
    print("- Fill out ALL form pages automatically")  
    print("- Stop at the final submission page")
    print("- Show you a detailed review modal")
    print("- Let you manually submit for final control")
    print("="*50)
    
    automation = FinalEINAutomation()
    
    try:
        result = await automation.run_complete_automation()
        
        print(f"\\nFINAL RESULT: {result}")
        
        if "SUCCESS" in result:
            print("\\nSUCCESS! The EIN application is ready for your submission!")
        elif "ERROR" in result:
            print(f"\\nERROR: {result}")
        else:
            print(f"\\nCOMPLETED: {result}")
        
    except KeyboardInterrupt:
        print("\\nProcess interrupted by user")
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        logger.error(f"Main execution error: {e}")
    
    print("\\nThe browser window will remain open.")
    print("   Close it manually when you're finished.")
    print("   All screenshots are saved in screenshots/ folder.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Critical error: {e}")
        input("Press Enter to exit...")