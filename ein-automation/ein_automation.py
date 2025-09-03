#!/usr/bin/env python3
"""
IRS EIN Application Automation Script
Fills out the EIN application form using data from ein_data.json
"""

import json
import time
import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import tkinter as tk
from tkinter import messagebox, scrolledtext
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

class EINAutomation:
    def __init__(self):
        self.data = self.load_data()
        self.page = None
        self.browser = None
        self.context = None
        self.max_retries = 3
        
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
    
    def show_review_modal(self):
        """Show review modal with all data before proceeding"""
        root = tk.Tk()
        root.title("EIN Application Data Review")
        root.geometry("800x600")
        
        # Create scrollable text area
        text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=30)
        text_area.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Format and display data
        formatted_data = self.format_data_for_review()
        text_area.insert(tk.END, formatted_data)
        text_area.config(state=tk.DISABLED)
        
        result = {'proceed': False}
        
        def on_proceed():
            result['proceed'] = True
            root.quit()
            root.destroy()
        
        def on_cancel():
            result['proceed'] = False
            root.quit()
            root.destroy()
        
        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        proceed_btn = tk.Button(button_frame, text="Proceed with Application", 
                              command=on_proceed, bg="green", fg="white", font=("Arial", 12))
        proceed_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                             command=on_cancel, bg="red", fg="white", font=("Arial", 12))
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Center the window
        root.mainloop()
        
        return result['proceed']
    
    def format_data_for_review(self):
        """Format data for human review"""
        lines = ["EIN APPLICATION DATA REVIEW", "=" * 40, ""]
        
        # Business Information
        lines.extend([
            "BUSINESS INFORMATION:",
            f"Legal Name: {self.data['business_info']['legal_name']}",
            f"Trade Name/DBA: {self.data['business_info']['trade_name_dba']}",
            f"Mailing Address: {self.data['business_info']['mailing_address']['street']}",
            f"City, State ZIP: {self.data['business_info']['mailing_address']['city']}, {self.data['business_info']['mailing_address']['state']} {self.data['business_info']['mailing_address']['zip_code']}",
            ""
        ])
        
        # Entity Information
        lines.extend([
            "ENTITY INFORMATION:",
            f"Entity Type: {self.data['entity_info']['entity_type']}",
            f"LLC Classification: {self.data['entity_info']['llc_classification']}",
            f"Number of LLC Members: {self.data['entity_info']['number_of_llc_members']}",
            ""
        ])
        
        # Responsible Party
        lines.extend([
            "RESPONSIBLE PARTY:",
            f"Name: {self.data['responsible_party']['name']}",
            f"SSN/ITIN: {self.data['responsible_party']['ssn_itin']}",
            f"Title: {self.data['responsible_party']['title']}",
            ""
        ])
        
        # Business Details
        lines.extend([
            "BUSINESS DETAILS:",
            f"Reason for Applying: {self.data['business_details']['reason_for_applying']}",
            f"Business Start Date: {self.data['business_details']['date_business_started']}",
            f"Principal Activity: {self.data['business_details']['principal_activity']}",
            f"Has Employees: {self.data['business_details']['has_employees']}",
            f"Expected Number of Employees: {self.data['business_details']['highest_number_employees_expected']}",
            ""
        ])
        
        lines.extend([
            "IMPORTANT REMINDERS:",
            "• You can only apply for 1 EIN per day",
            "• Application expires after 15 minutes of inactivity",
            "• Review all information carefully before submission",
            "• This script will STOP before final submission for your review",
            ""
        ])
        
        return "\\n".join(lines)
    
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
                    logger.info(f"Site accessible at {url}")
                    return True
                elif response.status == 503:
                    logger.warning(f"Site maintenance (503) at {url}")
                    continue
                elif response.status == 403:
                    logger.warning(f"Access forbidden (403) at {url} - trying next URL")
                    continue
                else:
                    logger.warning(f"Unexpected status {response.status} at {url}")
                    continue
                    
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout accessing {url}")
                continue
            except Exception as e:
                logger.warning(f"Error accessing {url}: {e}")
                continue
        
        logger.error("All URLs failed - site appears to be down")
        return False
    
    async def human_like_delay(self, min_ms=100, max_ms=300):
        """Add random delay to simulate human behavior"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def type_like_human(self, selector, text):
        """Type text with human-like delays"""
        element = await self.page.wait_for_selector(selector, timeout=10000)
        await element.clear()
        
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.randint(50, 150) / 1000)
    
    async def setup_browser(self):
        """Setup browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        # Launch browser with realistic settings
        self.browser = await playwright.chromium.launch(
            headless=False,  # Always visible for manual review
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
        
        logger.info("Browser setup complete")
    
    async def navigate_to_application(self):
        """Navigate to the EIN application"""
        logger.info("Navigating to EIN application")
        
        try:
            # Try main application URL first
            await self.page.goto('https://sa.www4.irs.gov/applyein/', 
                                timeout=60000, wait_until='domcontentloaded')
            await self.human_like_delay(2000, 4000)
            
            # Look for "Begin Application" or similar button
            begin_selectors = [
                'input[value*="Begin"]',
                'button:has-text("Begin")',
                'a:has-text("Begin")',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            for selector in begin_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found begin button with selector: {selector}")
                        await element.click()
                        await self.human_like_delay(3000, 5000)
                        return True
                except:
                    continue
            
            logger.warning("Could not find begin button, trying direct individual application URL")
            
            # Try direct individual application URL
            await self.page.goto('https://sa.www4.irs.gov/modiein/individual/index.jsp', 
                                timeout=60000, wait_until='domcontentloaded')
            await self.human_like_delay(2000, 4000)
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to application: {e}")
            return False
    
    async def fill_form_page(self):
        """Fill out form fields based on current page"""
        try:
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            await self.human_like_delay(1000, 2000)
            
            # Get page title or URL to determine which page we're on
            title = await self.page.title()
            url = self.page.url
            logger.info(f"Current page: {title} - {url}")
            
            # Take screenshot for debugging
            await self.page.screenshot(path=f'screenshots/page_{int(time.time())}.png')
            
            # Look for common form fields and fill them
            await self.fill_business_name_fields()
            await self.fill_address_fields()
            await self.fill_entity_type_fields()
            await self.fill_responsible_party_fields()
            await self.fill_business_details_fields()
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling form page: {e}")
            return False
    
    async def fill_business_name_fields(self):
        """Fill business name related fields"""
        name_selectors = [
            'input[name*="name"]',
            'input[id*="name"]',
            'input[name*="legal"]',
            'input[id*="legal"]'
        ]
        
        for selector in name_selectors:
            try:
                if await self.page.locator(selector).is_visible():
                    await self.type_like_human(selector, self.data['business_info']['legal_name'])
                    logger.info(f"Filled business name field: {selector}")
                    break
            except:
                continue
    
    async def fill_address_fields(self):
        """Fill address related fields"""
        address_mappings = [
            ('street', self.data['business_info']['mailing_address']['street']),
            ('city', self.data['business_info']['mailing_address']['city']),
            ('state', self.data['business_info']['mailing_address']['state']),
            ('zip', self.data['business_info']['mailing_address']['zip_code'])
        ]
        
        for field_type, value in address_mappings:
            if not value:
                continue
                
            selectors = [
                f'input[name*="{field_type}"]',
                f'input[id*="{field_type}"]',
                f'select[name*="{field_type}"]',
                f'select[id*="{field_type}"]'
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.locator(selector).first
                    if await element.is_visible():
                        if 'select' in selector:
                            await element.select_option(value)
                        else:
                            await self.type_like_human(selector, value)
                        logger.info(f"Filled {field_type} field")
                        break
                except:
                    continue
    
    async def fill_entity_type_fields(self):
        """Fill entity type related fields"""
        entity_type = self.data['entity_info']['entity_type']
        if not entity_type:
            return
        
        # Look for radio buttons or dropdowns for entity type
        entity_selectors = [
            'select[name*="entity"]',
            'select[id*="entity"]',
            'input[type="radio"]',
            'select[name*="organization"]'
        ]
        
        for selector in entity_selectors:
            try:
                if 'select' in selector:
                    await self.page.select_option(selector, entity_type)
                    logger.info(f"Selected entity type: {entity_type}")
                    break
            except:
                continue
    
    async def fill_responsible_party_fields(self):
        """Fill responsible party information"""
        rp_data = self.data['responsible_party']
        
        mappings = [
            ('name', rp_data['name']),
            ('ssn', rp_data['ssn_itin']),
            ('title', rp_data['title'])
        ]
        
        for field_type, value in mappings:
            if not value:
                continue
            
            selectors = [
                f'input[name*="responsible"][name*="{field_type}"]',
                f'input[id*="responsible"][id*="{field_type}"]',
                f'input[name*="{field_type}"]',
                f'input[id*="{field_type}"]'
            ]
            
            for selector in selectors:
                try:
                    if await self.page.locator(selector).is_visible():
                        await self.type_like_human(selector, value)
                        logger.info(f"Filled responsible party {field_type}")
                        break
                except:
                    continue
    
    async def fill_business_details_fields(self):
        """Fill business details"""
        # This would be expanded based on specific form fields found
        pass
    
    async def find_and_click_next(self):
        """Find and click the next/continue button"""
        next_selectors = [
            'input[value*="Next"]',
            'input[value*="Continue"]',
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'input[type="submit"]'
        ]
        
        for selector in next_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=5000)
                if element and await element.is_visible():
                    await element.click()
                    logger.info(f"Clicked next button: {selector}")
                    await self.human_like_delay(2000, 4000)
                    return True
            except:
                continue
        
        logger.warning("Could not find next button")
        return False
    
    async def run_automation(self):
        """Main automation workflow"""
        try:
            # Show review modal first
            if not self.show_review_modal():
                logger.info("User cancelled the application")
                return False
            
            await self.setup_browser()
            
            # Check site availability
            if not await self.check_site_availability():
                messagebox.showerror("Site Unavailable", 
                                   "The IRS EIN application site appears to be down. Please try again later.")
                return False
            
            # Navigate to application
            if not await self.navigate_to_application():
                logger.error("Failed to navigate to application")
                return False
            
            # Process form pages
            max_pages = 10  # Safety limit
            current_page = 0
            
            while current_page < max_pages:
                logger.info(f"Processing page {current_page + 1}")
                
                # Fill current page
                if not await self.fill_form_page():
                    logger.error(f"Failed to fill page {current_page + 1}")
                    break
                
                await self.human_like_delay(1000, 2000)
                
                # Check if we're at the final submission page
                page_text = await self.page.inner_text('body')
                if any(keyword in page_text.lower() for keyword in ['submit', 'final', 'review', 'confirm']):
                    logger.info("Reached final submission page")
                    
                    # Final review modal
                    root = tk.Tk()
                    root.withdraw()  # Hide main window
                    result = messagebox.askyesno(
                        "Final Confirmation",
                        "You are about to submit the EIN application. \\n\\n"
                        "Please review the form manually in the browser window.\\n\\n"
                        "Click 'Yes' if you want to proceed with submission,\\n"
                        "or 'No' to stop here and submit manually."
                    )
                    root.destroy()
                    
                    if not result:
                        logger.info("User chose to submit manually")
                        messagebox.showinfo("Manual Submission", 
                                          "The form has been filled out. Please review and submit manually.")
                        return True
                    
                    # If user wants to proceed, submit
                    submit_selectors = [
                        'input[value*="Submit"]',
                        'button:has-text("Submit")',
                        'input[type="submit"]'
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            element = await self.page.wait_for_selector(selector, timeout=5000)
                            if element:
                                await element.click()
                                logger.info("Form submitted!")
                                return True
                        except:
                            continue
                    
                    logger.warning("Could not find submit button")
                    break
                
                # Try to go to next page
                if not await self.find_and_click_next():
                    logger.info("No next button found - may be at final page")
                    break
                
                current_page += 1
            
            logger.info("Form processing completed")
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return False
        finally:
            if self.browser:
                # Don't close browser so user can review/submit manually
                logger.info("Browser left open for manual review")
                pass
    
    async def cleanup(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()

def main():
    """Main entry point"""
    automation = EINAutomation()
    
    try:
        asyncio.run(automation.run_automation())
    except KeyboardInterrupt:
        logger.info("Automation interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    
    print("\\nAutomation completed. Check the browser window and logs for details.")

if __name__ == "__main__":
    # Create screenshots directory
    Path("screenshots").mkdir(exist_ok=True)
    main()