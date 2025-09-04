"""
Automation Service for TeBSTrack
Handles automated VPN account creation and other template automations
"""

import time
import secrets
import string
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess
import os
from typing import Dict, Tuple, Optional

# Import pywin32 at module level to check availability
try:
    import win32com.client
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False

class VPNAutomationService:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def generate_vpn_password(self, length: int = 12) -> str:
        """Generate a secure random password for VPN account"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    def extract_username_from_email(self, email_string: str) -> str:
        """Extract username from email address, handling formats like 'Name <email@domain.com>' or 'email@domain.com'"""
        import re
        
        # Clean the input
        email_string = email_string.strip()
        
        # Check if it's in format "Name <email@domain.com>"
        email_match = re.search(r'<([^>]+)>', email_string)
        if email_match:
            email = email_match.group(1)
        else:
            # Check if it looks like an email directly
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email_string)
            if email_match:
                email = email_match.group(1)
            else:
                # If no email pattern found, assume the whole string is the email
                email = email_string
        
        # Extract username part (before @)
        if '@' in email:
            return email.split('@')[0]
        return email
    
    def safe_click_element(self, element, element_description="element"):
        """Safely click an element with multiple fallback methods for headless mode"""
        try:
            # Method 1: Scroll element into view and try regular click
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(0.5)  # Wait for scroll to complete
            
            try:
                element.click()
                logging.info(f"Successfully clicked {element_description} with regular click")
                return True
            except Exception as click_error:
                logging.warning(f"Regular click failed for {element_description}: {click_error}")
                
                # Method 2: Try JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    logging.info(f"Successfully clicked {element_description} with JavaScript click")
                    return True
                except Exception as js_error:
                    logging.warning(f"JavaScript click failed for {element_description}: {js_error}")
                    
                    # Method 3: Try to remove any overlapping elements and click
                    try:
                        # Remove any potentially overlapping footers or modals
                        self.driver.execute_script("""
                            var overlays = document.querySelectorAll('.footer, .modal, .overlay');
                            overlays.forEach(function(overlay) {
                                if (overlay.style) overlay.style.display = 'none';
                            });
                        """)
                        time.sleep(0.2)
                        element.click()
                        logging.info(f"Successfully clicked {element_description} after removing overlays")
                        return True
                    except Exception as final_error:
                        logging.error(f"All click methods failed for {element_description}: {final_error}")
                        return False
                        
        except Exception as e:
            logging.error(f"Failed to handle clicking {element_description}: {e}")
            return False
    
    def setup_browser(self) -> bool:
        """Setup Chrome browser with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            # Set a specific window size for headless mode to ensure consistent layout
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add SSL certificate ignore options for the VPN system
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-certificate-errors-spki-list")
            chrome_options.add_argument("--ignore-certificate-authority-invalid")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-insecure-localhost")
            chrome_options.add_argument("--disable-extensions")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            
            logging.info("Browser setup completed successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to setup browser: {e}")
            return False
    
    def handle_ssl_warning(self) -> bool:
        """Handle SSL certificate warning if it appears"""
        try:
            # Wait a moment for page to fully load
            time.sleep(2)
            
            # Check if we're on the SSL warning page
            if "Your connection is not private" in self.driver.page_source or "NET::ERR_CERT_AUTHORITY_INVALID" in self.driver.page_source:
                logging.info("SSL warning detected, attempting to proceed")
                
                # Method 1: Try standard Chrome SSL bypass
                try:
                    # Click Advanced button
                    advanced_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "details-button"))
                    )
                    advanced_button.click()
                    logging.info("Clicked Advanced button")
                    time.sleep(1)
                    
                    # Click Proceed link
                    proceed_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "proceed-link"))
                    )
                    proceed_link.click()
                    logging.info("Clicked Proceed link")
                    time.sleep(3)  # Wait for page to load
                    return True
                    
                except Exception as e1:
                    logging.warning(f"Standard SSL bypass failed: {e1}")
                    
                    # Method 2: Try alternative selectors
                    try:
                        # Try clicking Advanced with different approaches
                        advanced_button = self.driver.find_element(By.XPATH, "//button[contains(@id, 'details')]")
                        self.driver.execute_script("arguments[0].click();", advanced_button)
                        time.sleep(1)
                        
                        # Try proceed link with different approaches
                        proceed_link = self.driver.find_element(By.XPATH, "//a[contains(@id, 'proceed')]")
                        self.driver.execute_script("arguments[0].click();", proceed_link)
                        time.sleep(3)
                        logging.info("SSL warning bypassed with alternative method")
                        return True
                        
                    except Exception as e2:
                        logging.warning(f"Alternative SSL bypass failed: {e2}")
                        
                        # Method 3: Try typing "thisisunsafe" (Chrome secret)
                        try:
                            self.driver.find_element(By.TAG_NAME, "body").send_keys("thisisunsafe")
                            time.sleep(2)
                            logging.info("Used Chrome secret bypass")
                            return True
                        except Exception as e3:
                            logging.error(f"All SSL bypass methods failed: {e3}")
                            return False
            
            logging.info("No SSL warning detected or already bypassed")
            return True  # No SSL warning detected
            
        except Exception as e:
            logging.error(f"Error handling SSL warning: {e}")
            return False
    
    def login_to_vpn_system(self) -> bool:
        """Step 1-2: Navigate to VPN system and login"""
        try:
            # Step 1: Navigate to login page
            self.driver.get("http://203.125.240.114/login")
            logging.info("Navigated to VPN login page")
            
            # Handle SSL warning if it appears
            if not self.handle_ssl_warning():
                logging.error("Failed to handle SSL warning")
                return False
            
            # Wait for the actual login page to load and ensure we're not on SSL warning
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Check if we're still on SSL warning page
                    if "Your connection is not private" in self.driver.page_source:
                        logging.info(f"Still on SSL warning page, attempt {attempt + 1}")
                        self.handle_ssl_warning()
                        time.sleep(2)
                        continue
                    
                    # Try to find the username field to confirm we're on login page
                    username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                    logging.info("Successfully reached login page")
                    break
                except:
                    if attempt < max_retries - 1:
                        logging.info(f"Login page not ready, retrying... (attempt {attempt + 1})")
                        time.sleep(2)
                        continue
                    else:
                        logging.error("Could not reach login page after multiple attempts")
                        return False
            
            # Step 2: Login with credentials
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "#username")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "#secretkey")
                login_button = self.driver.find_element(By.CSS_SELECTOR, "#login_button")
                
                username_field.clear()
                username_field.send_keys("muhd.farhan")
                
                password_field.clear()
                password_field.send_keys("W@#v1560$$cDM")
                
                login_button.click()
                logging.info("Login credentials submitted")
                
                # Wait a moment for login to process
                time.sleep(3)
                return True
                
            except Exception as e:
                logging.error(f"Failed to fill login form: {e}")
                return False
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return False
    
    def navigate_to_user_wizard(self) -> bool:
        """Step 3-4: Navigate to user wizard and start process"""
        try:
            # Step 3: Wait 1s then navigate to wizard
            time.sleep(1)
            self.driver.get("https://203.125.240.114/ng/user/wizard")
            logging.info("Navigated to user wizard")
            
            # Step 4: Wait 3s then click primary button
            time.sleep(2)
            primary_button = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, 
                "#ng-base > form > div.footer.ng-scope > dialog-footer > button.primary"
            )))
            
            # Use safe click method for headless mode compatibility
            if self.safe_click_element(primary_button, "wizard start button"):
                logging.info("Started user creation wizard")
                return True
            else:
                logging.error("Failed to click wizard start button")
                return False
        except Exception as e:
            logging.error(f"Failed to start wizard: {e}")
            return False
    
    def fill_user_credentials(self, vpn_username: str, vpn_password: str) -> bool:
        """Step 5: Fill in VPN username and password"""
        try:
            # Wait 0.5s
            time.sleep(0.5)
            
            # Fill username field
            username_field = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > section > div:nth-child(1) > div > input"
            )))
            username_field.clear()
            username_field.send_keys(vpn_username)
            
            # Wait 0.5s then fill password field
            time.sleep(0.5)
            password_field = self.driver.find_element(By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > section > div.field.ng-scope > div > input"
            )
            password_field.clear()
            password_field.send_keys(vpn_password)
            
            logging.info(f"Filled credentials - Username: {vpn_username}")
            return True
        except Exception as e:
            logging.error(f"Failed to fill credentials: {e}")
            return False
    
    def continue_wizard_step6(self) -> bool:
        """Step 6: Click primary button to continue"""
        try:
            time.sleep(0.5)
            primary_button = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.footer.ng-scope > dialog-footer > button.primary"
            )))
            
            # Use safe click method for headless mode compatibility
            if self.safe_click_element(primary_button, "wizard continue button"):
                logging.info("Continued to next wizard step")
                return True
            else:
                logging.error("Failed to click wizard continue button")
                return False
        except Exception as e:
            logging.error(f"Failed to continue wizard: {e}")
            return False
    
    def configure_two_factor_auth(self, vpn_username: str) -> bool:
        """Steps 7-12: Configure two-factor authentication"""
        try:
            # Step 7: Toggle 2FA
            time.sleep(0.5)
            tfa_toggle = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > f-two-factor-auth > label > label"
            )))
            tfa_toggle.click()
            logging.info("Enabled two-factor authentication")
            
            # Step 8: Select radio option
            time.sleep(0.5)
            radio_option = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > f-two-factor-auth > section > f-field:nth-child(1) > div > field-value > f-radio-group > label:nth-child(4)"
            )))
            radio_option.click()
            
            # Step 9: Click dropdown
            time.sleep(0.5)
            dropdown = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > f-two-factor-auth > section > f-field:nth-child(2) > div > field-value > f-ng2-fortitoken-tfa-omniselect-component > div > nu-omni-select > div"
            )))
            dropdown.click()
            
            # Step 10: Select dropdown option by text content
            time.sleep(0.5)
            dropdown_option = self.wait.until(EC.element_to_be_clickable((
                By.XPATH,
                "//*[contains(text(), 'FTKMOB3BE69D7457')]"
            )))
            dropdown_option.click()
            
            # Step 11: Fill email field
            time.sleep(2)
            try:
                # Try multiple approaches to find the email input field
                email_field = None
                
                # Method 1: Try by ng-model attribute
                try:
                    email_field = self.wait.until(EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "input[ng-model=\"$ctrl.entry['email-to']\"]"
                    )))
                except:
                    # Method 2: Try by type and class
                    try:
                        email_field = self.driver.find_element(By.CSS_SELECTOR,
                            "input[type='email'][ng-model*='email-to']"
                        )
                    except:
                        # Method 3: Try XPath for email input
                        email_field = self.driver.find_element(By.XPATH,
                            "//input[@type='email' and contains(@ng-model, 'email-to')]"
                        )
                
                if email_field:
                    email_field.clear()
                    email_field.send_keys(f"{vpn_username}@totalebizsolutions.com")
                    logging.info(f"Successfully filled email field with {vpn_username}@totalebizsolutions.com")
                else:
                    raise Exception("Could not find email input field")
                    
            except Exception as e:
                logging.error(f"Failed to fill email field: {e}")
                # Fallback: try to find any email input on the page
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                    email_field.clear()
                    email_field.send_keys(f"{vpn_username}@totalebizsolutions.com")
                    logging.info("Used fallback method to fill email field")
                except Exception as fallback_error:
                    logging.error(f"Fallback email field method also failed: {fallback_error}")
                    return False
            
            # Step 12: Continue
            time.sleep(0.5)
            primary_button = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.footer.ng-scope > dialog-footer > button.primary"
            )))
            
            # Use safe click method for headless mode compatibility
            if self.safe_click_element(primary_button, "2FA continue button"):
                logging.info("Configured two-factor authentication")
                return True
            else:
                logging.error("Failed to click 2FA continue button")
                return False
        except Exception as e:
            logging.error(f"Failed to configure 2FA: {e}")
            return False
    
    def configure_user_groups(self) -> bool:
        """Steps 13-16: Configure user groups"""
        try:
            # Step 13: Toggle user groups
            time.sleep(0.5)
            groups_toggle = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > section > div:nth-child(2) > label > span > label"
            )))
            groups_toggle.click()
            
            # Step 14: Click add placeholder
            time.sleep(0.5)
            add_placeholder = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "#ng-base > form > div.content.full-height > div.content-container.slot-filled > div.slot-filled > dialog-content > f-local-user-wizard > section > div:nth-child(2) > div > div > div.add-placeholder"
            )))
            add_placeholder.click()
            
            # Step 15: Select group entry by text content
            time.sleep(1.5)
            try:
                # Try to find the SSL_VPN_USERS div element
                group_entry = self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class, 'entry') and .//span[text()='SSL_VPN_USERS']]"
                )))
                
                # Try regular click first
                try:
                    group_entry.click()
                    logging.info("Successfully clicked SSL_VPN_USERS group")
                except Exception as click_error:
                    logging.warning(f"Regular click failed, trying JavaScript click: {click_error}")
                    # If regular click fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", group_entry)
                    logging.info("Successfully clicked SSL_VPN_USERS group with JavaScript")
                    
            except Exception as e:
                logging.error(f"Could not find SSL_VPN_USERS group: {e}")
                # Fallback: try to click any entry with SSL_VPN_USERS text
                try:
                    fallback_entry = self.driver.find_element(By.XPATH, "//*[contains(text(), 'SSL_VPN_USERS')]")
                    self.driver.execute_script("arguments[0].click();", fallback_entry)
                    logging.info("Used fallback method to click SSL_VPN_USERS")
                except Exception as fallback_error:
                    logging.error(f"Fallback click also failed: {fallback_error}")
                    return False
            
            # Step 16: Final continue
            time.sleep(0.5)
            try:
                primary_button = self.wait.until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "#ng-base > form > div.footer.ng-scope > dialog-footer > button.primary"
                )))
                
                # Use safe click method for headless mode compatibility
                if self.safe_click_element(primary_button, "final continue button"):
                    logging.info("Successfully clicked final continue button")
                else:
                    logging.error("Failed to click final continue button with all methods")
                    return False
                
                # Wait a moment for the action to complete
                time.sleep(2)
                logging.info("User groups configuration completed")
                
            except Exception as button_error:
                logging.error(f"Failed to click final continue button: {button_error}")
                return False
            
            logging.info("Configured user groups - returning True to proceed to next step")
            print("DEBUG: configure_user_groups returning True", flush=True)
            return True
        except Exception as e:
            logging.error(f"Failed to configure user groups: {e}")
            print(f"DEBUG: configure_user_groups failed with error: {e}", flush=True)
            return False
    
    def start_outlook_explicitly(self) -> bool:
        """Explicitly start Outlook and wait for it to be ready"""
        try:
            logging.info("Explicitly starting Outlook application...")
            print("DEBUG: Explicitly starting Outlook application...", flush=True)
            
            # First, try to start Outlook via subprocess
            try:
                subprocess.run(['start', 'outlook'], shell=True, check=True)
                logging.info("Started Outlook via subprocess")
                print("DEBUG: Started Outlook via subprocess", flush=True)
            except subprocess.CalledProcessError as e:
                logging.warning(f"Failed to start Outlook via subprocess: {e}")
                print(f"DEBUG: Failed to start Outlook via subprocess: {e}", flush=True)
            
            # Wait for Outlook to start and become available
            max_attempts = 15  # 15 seconds max wait
            for attempt in range(max_attempts):
                try:
                    if PYWIN32_AVAILABLE:
                        import pythoncom
                        pythoncom.CoInitialize()
                        try:
                            # Try to connect to Outlook
                            outlook = win32com.client.Dispatch("Outlook.Application")
                            # Test if we can access Outlook's namespace (this confirms it's ready)
                            namespace = outlook.GetNamespace("MAPI")
                            logging.info(f"Outlook is ready after {attempt + 1} seconds")
                            print(f"DEBUG: Outlook is ready after {attempt + 1} seconds", flush=True)
                            return True
                        finally:
                            pythoncom.CoUninitialize()
                    else:
                        # If pywin32 not available, just wait a bit
                        time.sleep(5)
                        return True
                        
                except Exception as e:
                    if attempt < max_attempts - 1:
                        logging.info(f"Outlook not ready yet, waiting... (attempt {attempt + 1})")
                        print(f"DEBUG: Outlook not ready yet, waiting... (attempt {attempt + 1})", flush=True)
                        time.sleep(1)
                    else:
                        logging.error(f"Outlook failed to become ready after {max_attempts} seconds: {e}")
                        print(f"DEBUG: Outlook failed to become ready after {max_attempts} seconds: {e}", flush=True)
                        return False
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to start Outlook explicitly: {e}")
            print(f"DEBUG: Failed to start Outlook explicitly: {e}", flush=True)
            return False

    def open_outlook_and_draft_email(self, vpn_username: str, vpn_password: str) -> bool:
        """Step 17: Open Outlook and draft email automatically"""
        try:
            logging.info("Starting Outlook email creation process...")
            print("DEBUG: Starting Outlook email creation process...", flush=True)
            
            # Step 1: Explicitly start Outlook first
            if not self.start_outlook_explicitly():
                logging.warning("Failed to start Outlook explicitly, trying COM automation anyway...")
                print("DEBUG: Failed to start Outlook explicitly, trying COM automation anyway...", flush=True)
            
            time.sleep(2)  # Additional wait after explicit startup
            
            # Extract actual name from username for personalization
            username_parts = vpn_username.split('.')
            display_name = ' '.join(word.capitalize() for word in username_parts)
            
            # Create email body with attachment references
            email_body = f"""Hi {display_name},

We have created a VPN account for you and attached the setup guides in this email.

Below are your credentials:

Username: {vpn_username}
Password: {vpn_password}

Please refer to the attached documents:
1. TeBS-FortiToken 2FA Guide - For setting up two-factor authentication
2. TeBS-VPN Client Setup Guide - For configuring your VPN client

Thanks & Regards,
Farhan
Infra Intern"""
            
            try:
                # Use COM automation to create email in Outlook
                if not PYWIN32_AVAILABLE:
                    raise ImportError("pywin32 not available")
                
                # Initialize COM properly
                import pythoncom
                pythoncom.CoInitialize()
                
                try:
                    # Connect to the already-started Outlook application
                    logging.info("Connecting to Outlook via COM...")
                    print("DEBUG: Connecting to Outlook via COM...", flush=True)
                    
                    # Try to get existing Outlook instance first
                    try:
                        outlook = win32com.client.GetActiveObject("Outlook.Application")
                        logging.info("Connected to existing Outlook instance")
                        print("DEBUG: Connected to existing Outlook instance", flush=True)
                    except:
                        # If no existing instance, create new one
                        outlook = win32com.client.Dispatch("Outlook.Application")
                        logging.info("Created new Outlook instance")
                        print("DEBUG: Created new Outlook instance", flush=True)
                        time.sleep(3)  # Wait for new instance to initialize
                    
                    # Create a new mail item
                    logging.info("Creating new email message...")
                    print("DEBUG: Creating new email message...", flush=True)
                    mail = outlook.CreateItem(0)  # 0 = olMailItem
                    
                    # Set email properties
                    mail.To = f"{vpn_username}@totalebizsolutions.com"
                    mail.Subject = "VPN Account Credentials"
                    mail.Body = email_body
                    logging.info("Set email basic properties")
                    print("DEBUG: Set email basic properties", flush=True)
                    
                    # Add PDF attachments
                    try:
                        logging.info("Adding PDF attachments...")
                        print("DEBUG: Adding PDF attachments...", flush=True)
                        # Get the absolute path to the documents folder
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        documents_path = os.path.join(script_dir, 'static', 'documents')
                        
                        # Attach FortiToken 2FA Guide
                        fortitoken_guide = os.path.join(documents_path, "TeBS-FortiToken 2FA Guide.V1.0.pdf")
                        if os.path.exists(fortitoken_guide):
                            mail.Attachments.Add(fortitoken_guide)
                            logging.info("Added FortiToken 2FA Guide attachment")
                            print("DEBUG: Added FortiToken 2FA Guide attachment", flush=True)
                        else:
                            logging.warning(f"FortiToken guide not found at: {fortitoken_guide}")
                            print(f"DEBUG: FortiToken guide not found at: {fortitoken_guide}", flush=True)
                        
                        # Attach VPN Client Setup Guide
                        vpn_guide = os.path.join(documents_path, "TeBS-VPN Client Setup Guide.V4.0.pdf")
                        if os.path.exists(vpn_guide):
                            mail.Attachments.Add(vpn_guide)
                            logging.info("Added VPN Client Setup Guide attachment")
                            print("DEBUG: Added VPN Client Setup Guide attachment", flush=True)
                        else:
                            logging.warning(f"VPN guide not found at: {vpn_guide}")
                            print(f"DEBUG: VPN guide not found at: {vpn_guide}", flush=True)
                            
                    except Exception as attachment_error:
                        logging.warning(f"Failed to add attachments: {attachment_error}")
                        print(f"DEBUG: Failed to add attachments: {attachment_error}", flush=True)
                    
                    # Display the email (this opens it in a window ready to send)
                    logging.info("Displaying email draft...")
                    print("DEBUG: Displaying email draft...", flush=True)
                    
                    # Try to bring Outlook to foreground
                    try:
                        # Get Outlook window and bring it to front
                        import win32gui
                        import win32con
                        
                        def enum_windows_callback(hwnd, windows):
                            if win32gui.IsWindowVisible(hwnd):
                                window_text = win32gui.GetWindowText(hwnd)
                                if "outlook" in window_text.lower():
                                    windows.append(hwnd)
                        
                        windows = []
                        win32gui.EnumWindows(enum_windows_callback, windows)
                        
                        if windows:
                            # Bring Outlook window to foreground
                            win32gui.SetForegroundWindow(windows[0])
                            win32gui.ShowWindow(windows[0], win32con.SW_RESTORE)
                            logging.info("Brought Outlook window to foreground")
                            print("DEBUG: Brought Outlook window to foreground", flush=True)
                    except Exception as window_error:
                        logging.warning(f"Could not bring Outlook to foreground: {window_error}")
                        print(f"DEBUG: Could not bring Outlook to foreground: {window_error}", flush=True)
                    
                    mail.Display(True)  # True = modal dialog
                    
                    logging.info(f"Created draft email in Outlook for {vpn_username}")
                    logging.info("Email is ready - user just needs to click Send")
                    print("DEBUG: Email draft created successfully!", flush=True)
                    return True
                    
                finally:
                    # Clean up COM
                    pythoncom.CoUninitialize()
                    
            except ImportError:
                logging.warning("pywin32 not available, falling back to manual Outlook opening")
                # Fallback: Open Outlook manually and provide instructions
                try:
                    subprocess.run(['start', 'outlook'], shell=True, check=True)
                    logging.info(f"Opened Outlook Classic for {vpn_username}")
                    
                    # Get attachment paths for manual reference
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    documents_path = os.path.join(script_dir, 'static', 'documents')
                    fortitoken_guide = os.path.join(documents_path, "TeBS-FortiToken 2FA Guide.V1.0.pdf")
                    vpn_guide = os.path.join(documents_path, "TeBS-VPN Client Setup Guide.V4.0.pdf")
                    
                    # Provide email details for manual creation
                    logging.info(f"Please create email manually with these details:")
                    logging.info(f"To: {vpn_username}@totalebizsolutions.com")
                    logging.info(f"Subject: VPN Account Credentials")
                    logging.info(f"Body: {email_body}")
                    logging.info(f"Attachments to add:")
                    logging.info(f"1. {fortitoken_guide}")
                    logging.info(f"2. {vpn_guide}")
                    
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Could not open Outlook: {e}")
                    return False
                
            except Exception as com_error:
                logging.error(f"Failed to create email via COM: {com_error}")
                print(f"DEBUG: Failed to create email via COM: {com_error}", flush=True)
                # Fallback to manual method
                try:
                    subprocess.run(['start', 'outlook'], shell=True, check=True)
                    logging.info("Opened Outlook manually due to COM error")
                    
                    # Get attachment paths for manual reference
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    documents_path = os.path.join(script_dir, 'static', 'documents')
                    fortitoken_guide = os.path.join(documents_path, "TeBS-FortiToken 2FA Guide.V1.0.pdf")
                    vpn_guide = os.path.join(documents_path, "TeBS-VPN Client Setup Guide.V4.0.pdf")
                    
                    logging.info(f"Please create email manually:")
                    logging.info(f"To: {vpn_username}@totalebizsolutions.com")
                    logging.info(f"Subject: VPN Account Credentials") 
                    logging.info(f"Body: {email_body}")
                    logging.info(f"Attachments to add:")
                    logging.info(f"1. {fortitoken_guide}")
                    logging.info(f"2. {vpn_guide}")
                except subprocess.CalledProcessError:
                    logging.error("Could not open Outlook at all")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to handle Outlook email: {e}")
            return False
    
    def cleanup(self):
        """Close browser and cleanup resources"""
        if self.driver:
            self.driver.quit()
            logging.info("Browser session closed")
    
    def execute_vpn_creation_automation(self, sender_email: str, vpn_username: str, vpn_password: str) -> Dict:
        """Execute the complete VPN creation automation"""
        results = {
            'success': False,
            'steps_completed': 0,
            'total_steps': 18,
            'error_message': None,
            'vpn_credentials': {
                'username': vpn_username,
                'password': vpn_password
            }
        }
        
        try:
            # Setup browser
            if not self.setup_browser():
                results['error_message'] = "Failed to setup browser"
                return results
            results['steps_completed'] = 1
            
            # Login to VPN system
            if not self.login_to_vpn_system():
                results['error_message'] = "Failed to login to VPN system"
                return results
            results['steps_completed'] = 2
            
            # Navigate to wizard
            if not self.navigate_to_user_wizard():
                results['error_message'] = "Failed to navigate to user wizard"
                return results
            results['steps_completed'] = 4
            
            # Fill credentials
            if not self.fill_user_credentials(vpn_username, vpn_password):
                results['error_message'] = "Failed to fill user credentials"
                return results
            results['steps_completed'] = 5
            
            # Continue wizard
            if not self.continue_wizard_step6():
                results['error_message'] = "Failed to continue wizard"
                return results
            results['steps_completed'] = 6
            
            # Configure 2FA
            if not self.configure_two_factor_auth(vpn_username):
                results['error_message'] = "Failed to configure two-factor authentication"
                return results
            results['steps_completed'] = 12
            
            # Configure groups
            print("DEBUG: Starting user groups configuration (step 16)...", flush=True)
            logging.info("Starting user groups configuration (step 16)...")
            if not self.configure_user_groups():
                results['error_message'] = "Failed to configure user groups"
                return results
            results['steps_completed'] = 16
            print("DEBUG: User groups configuration completed successfully, proceeding to Outlook...", flush=True)
            logging.info("User groups configuration completed successfully, proceeding to Outlook...")
            
            # Open Outlook
            print("DEBUG: Starting Outlook email creation (step 17)...", flush=True)
            logging.info("Starting Outlook email creation (step 17)...")
            if not self.open_outlook_and_draft_email(vpn_username, vpn_password):
                results['error_message'] = "Failed to open Outlook"
                return results
            results['steps_completed'] = 17
            print("DEBUG: Outlook email creation completed successfully!", flush=True)
            logging.info("Outlook email creation completed successfully!")
            
            results['success'] = True
            results['steps_completed'] = 18
            
        except Exception as e:
            results['error_message'] = f"Automation failed: {str(e)}"
            logging.error(f"VPN automation error: {e}")
        finally:
            self.cleanup()
        
        return results

# Global automation service instance
_automation_service = None

def get_automation_service():
    """Get the global automation service instance"""
    global _automation_service
    if _automation_service is None:
        _automation_service = VPNAutomationService()
    return _automation_service
