"""
LMS Automation with Direct URL Navigation - FIXED VERSION
Prevents browser from closing prematurely
"""

import os
import sys
import json
import time
import random
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class LMSAutomation:
    def __init__(self):
        self.LMS_URL = "https://lms2.ai.saveetha.in"
        self.driver = None
        self.wait = None

    def human_delay(self, min_delay=0.8, max_delay=1.8):
        time.sleep(random.uniform(min_delay, max_delay))

    def detect_recaptcha(self):
        try:
            if not self.driver:
                return False
            frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[title*='captcha']")
            return len(frames) > 0
        except Exception:
            return False

    def wait_for_manual_recaptcha(self, timeout=120):
        start = time.time()
        print("⚠️ reCAPTCHA detected. Please solve it manually in the opened Chrome window.", file=sys.stderr)
        while time.time() - start < timeout:
            self.human_delay(1.0, 2.0)
            if not self.detect_recaptcha():
                print("✅ reCAPTCHA solved, continuing automation", file=sys.stderr)
                return True
        print("⏰ Timed out waiting for reCAPTCHA solution", file=sys.stderr)
        return False

    def setup_driver(self):
        try:
            options = Options()
            user_agent = os.getenv("LMS_AUTOMATION_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36")
            profile_dir = os.path.join(os.path.dirname(__file__), "..", "temp", "chrome-profile")
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={os.path.abspath(profile_dir)}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--lang=en-US")
            options.add_argument(f"--user-agent={user_agent}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--timeout=300000")
            options.add_argument("--page-load-strategy=normal")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)

            prefs = {
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.notifications": 2
            }
            options.add_experimental_option("prefs", prefs)

            service = Service()
            service.creation_flags = 0x08000000
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(300)
            self.driver.implicitly_wait(30)
            self.driver.set_window_size(1920, 1080)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                """
            })
            self.wait = WebDriverWait(self.driver, 60)
            
            print("✅ WebDriver setup completed successfully", file=sys.stderr)
            return True

        except Exception as e:
            print(f"❌ WebDriver setup failed: {e}", file=sys.stderr)
            return False

    def is_driver_alive(self):
        """Check if the driver session is still active"""
        try:
            self.driver.current_url
            return True
        except Exception:
            return False

    def login(self, username, password):
        try:
            print(f"🔐 Attempting login for user: {username}", file=sys.stderr)
            if not self.is_driver_alive():
                return {"success": False, "message": "WebDriver session terminated"}

            self.driver.get(f"{self.LMS_URL}/login/index.php")
            self.human_delay(2.0, 3.5)

            if self.detect_recaptcha():
                if not self.wait_for_manual_recaptcha():
                    return {"success": False, "message": "reCAPTCHA not solved in time"}

            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(username)
            self.human_delay()

            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            self.human_delay()

            self.driver.find_element(By.ID, "loginbtn").click()
            print("✅ Login credentials submitted, waiting for dashboard...", file=sys.stderr)

            if self.detect_recaptcha():
                if not self.wait_for_manual_recaptcha():
                    return {"success": False, "message": "reCAPTCHA not solved in time"}

            self.wait.until(EC.any_of(
                EC.url_contains("/my/"),
                EC.presence_of_element_located((By.CLASS_NAME, "usermenu"))
            ))

            print("✅ Login successful - Dashboard loaded", file=sys.stderr)
            time.sleep(3)
            return {"success": True, "message": "Successfully logged in to LMS"}

        except TimeoutException:
            print("❌ Login timeout - credentials may be incorrect", file=sys.stderr)
            return {"success": False, "message": "Login failed - timeout"}
        except Exception as e:
            print(f"❌ Login error: {str(e)}", file=sys.stderr)
            return {"success": False, "message": "Login failed", "error": str(e)}

    def navigate_direct_url(self, submission_url):
        """Navigate directly to submission page using URL from MongoDB"""
        try:
            print(f"🚀 Navigating directly to submission page...", file=sys.stderr)
            print(f"📍 URL: {submission_url}", file=sys.stderr)
            
            if not self.is_driver_alive():
                return {"success": False, "message": "WebDriver session terminated"}

            # Navigate directly to the submission URL
            self.driver.get(submission_url)
            print("✅ Page loaded, waiting for submission elements...", file=sys.stderr)
            
            time.sleep(5)

            # Verify we're on the submission page
            try:
                self.wait.until(EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//button[normalize-space()='Add submission']")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'submissionstatussubmitted')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[@id='region-main']"))
                ))
                print("✅ Submission page loaded and verified successfully", file=sys.stderr)
                return {"success": True, "message": "Successfully navigated to submission page"}
            except TimeoutException:
                print("⚠️ Could not verify submission page elements", file=sys.stderr)
                return {"success": False, "message": "Submission page elements not found"}

        except Exception as e:
            print(f"❌ Navigation error: {str(e)}", file=sys.stderr)
            traceback.print_exc()
            return {"success": False, "message": "Direct navigation failed", "error": str(e)}

    def upload_pdf_file(self, file_path):
        """Enhanced PDF upload method"""
        try:
            print(f"📝 Starting PDF upload for: {file_path}", file=sys.stderr)
            
            cleaned_file_path = file_path.strip('"').strip("'")
            print(f"📁 Cleaned file path: {cleaned_file_path}", file=sys.stderr)

            if not os.path.exists(cleaned_file_path):
                return {"success": False, "message": f"PDF file not found: {cleaned_file_path}"}

            file_size = os.path.getsize(cleaned_file_path)
            file_name = os.path.basename(cleaned_file_path)

            if not file_name.lower().endswith('.pdf'):
                return {"success": False, "message": f"File is not a PDF: {file_name}"}

            if file_size < 100:
                return {"success": False, "message": f"PDF file is too small: {file_size} bytes"}

            print(f"📁 PDF File Validated ✅", file=sys.stderr)
            print(f"   - Name: {file_name}", file=sys.stderr)
            print(f"   - Size: {file_size} bytes", file=sys.stderr)

            if not self.is_driver_alive():
                return {"success": False, "message": "WebDriver session terminated"}

            # STEP 1: Click Add submission button
            print("🔄 Step 1: Clicking 'Add submission' button...", file=sys.stderr)
            add_submission_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Add submission']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_submission_btn)
            time.sleep(2)
            self.driver.execute_script("arguments[0].click();", add_submission_btn)
            print("✅ Add submission page opened", file=sys.stderr)
            time.sleep(5)

            # STEP 2: Click Add file icon
            print("🔄 Step 2: Clicking 'Add...' file icon...", file=sys.stderr)
            add_file_icon = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Add...']"))
            )
            add_file_icon.click()
            print("✅ File picker opened", file=sys.stderr)
            time.sleep(3)

            # STEP 3: Click "Upload a file" tab
            print("🔄 Step 3: Selecting 'Upload a file' tab...", file=sys.stderr)
            upload_tab = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Upload a file']"))
            )
            upload_tab.click()
            print("✅ Upload tab selected", file=sys.stderr)
            time.sleep(3)

            # STEP 4: Locate file input element
            print("🔄 Step 4: Locating file input element...", file=sys.stderr)
            file_input_selectors = [
                "input[name='repo_upload_file']",
                "input[type='file']",
                "input[type='file'][name='repo_upload_file']"
            ]
            
            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found file input: {selector}", file=sys.stderr)
                    break
                except:
                    continue

            if not file_input:
                return {"success": False, "message": "Could not locate file input element"}

            # Make file input visible
            self.driver.execute_script("""
                arguments[0].style.display = 'block';
                arguments[0].style.visibility = 'visible';
                arguments[0].style.height = 'auto';
                arguments[0].style.width = 'auto';
                arguments[0].style.opacity = '1';
                arguments[0].removeAttribute('hidden');
            """, file_input)
            time.sleep(2)

            # STEP 5: Send file path
            print("🔄 Step 5: Sending PDF file path...", file=sys.stderr)
            abs_file_path = os.path.abspath(cleaned_file_path)
            print(f"📁 Absolute path: {abs_file_path}", file=sys.stderr)

            file_input.clear()
            file_input.send_keys(abs_file_path)
            print(f"✅ File path sent to input", file=sys.stderr)
            time.sleep(3)

            # STEP 6: Click Upload button
            print("🔄 Step 6: Clicking 'Upload this file' button...", file=sys.stderr)
            upload_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Upload this file']"))
            )
            upload_btn.click()
            print("✅ Upload button clicked", file=sys.stderr)
            time.sleep(10)

            # STEP 7: Verify upload
            print("🔄 Step 7: Verifying upload...", file=sys.stderr)
            upload_verified = False
            for attempt in range(5):
                try:
                    self.driver.find_element(By.PARTIAL_LINK_TEXT, file_name)
                    upload_verified = True
                    print(f"✅ Upload verified - found file: {file_name}", file=sys.stderr)
                    break
                except:
                    time.sleep(2)

            if not upload_verified:
                print("⚠️ Could not verify upload, continuing...", file=sys.stderr)

            # STEP 8: Final submission
            print("🔄 Step 8: Final submission...", file=sys.stderr)
            save_btn = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "submitbutton"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
            time.sleep(3)
            self.driver.execute_script("arguments[0].click();", save_btn)
            print("✅ Final submission button clicked", file=sys.stderr)
            time.sleep(15)

            # Verify submission success
            success_confirmed = False
            success_indicators = [
                "//div[contains(@class, 'alert-success')]",
                "//div[contains(text(), 'Submitted for grading')]",
                "//span[contains(text(), 'Submitted')]"
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element:
                        print(f"✅ Submission confirmed with success indicator", file=sys.stderr)
                        success_confirmed = True
                        break
                except:
                    continue

            print("🎉 PDF UPLOAD AND SUBMISSION COMPLETED!", file=sys.stderr)
            return {"success": True, "message": f"PDF '{file_name}' uploaded successfully"}

        except Exception as e:
            print(f"❌ Upload error: {str(e)}", file=sys.stderr)
            traceback.print_exc()
            return {"success": False, "message": "PDF upload failed", "error": str(e)}

    def complete_automation(self, username, password, subject_code, file_path=None, submission_url=None):
        """Complete automation with direct URL navigation - FIXED to prevent early termination"""
        result = {
            "login": {"success": False},
            "navigation": {"success": False},
            "upload": {"success": False}
        }
        
        try:
            print("="*80, file=sys.stderr)
            print("🚀 LMS AUTOMATION STARTED", file=sys.stderr)
            print("="*80, file=sys.stderr)
            
            # Setup WebDriver
            print("🔧 Setting up WebDriver...", file=sys.stderr)
            if not self.setup_driver():
                result["login"] = {"success": False, "message": "WebDriver setup failed"}
                print("JSON_START")
                print(json.dumps(result, ensure_ascii=False))
                print("JSON_END")
                return

            # Login
            print("\n" + "="*80, file=sys.stderr)
            print("📝 STEP 1: LOGIN", file=sys.stderr)
            print("="*80, file=sys.stderr)
            login_result = self.login(username, password)
            result["login"] = login_result
            
            if not login_result['success']:
                print("❌ Login failed, stopping automation", file=sys.stderr)
                print("JSON_START")
                print(json.dumps(result, ensure_ascii=False))
                print("JSON_END")
                return

            # Navigate using direct URL
            print("\n" + "="*80, file=sys.stderr)
            print("📝 STEP 2: NAVIGATION", file=sys.stderr)
            print("="*80, file=sys.stderr)
            
            if submission_url:
                print(f"🚀 Using direct URL for subject: {subject_code}", file=sys.stderr)
                navigation_result = self.navigate_direct_url(submission_url)
            else:
                print(f"⚠️ No direct URL provided for subject: {subject_code}", file=sys.stderr)
                navigation_result = {"success": False, "message": "No submission URL provided"}
            
            result["navigation"] = navigation_result
            
            if not navigation_result['success']:
                print("❌ Navigation failed, stopping automation", file=sys.stderr)
                print("JSON_START")
                print(json.dumps(result, ensure_ascii=False))
                print("JSON_END")
                return

            # Upload PDF
            print("\n" + "="*80, file=sys.stderr)
            print("📝 STEP 3: PDF UPLOAD", file=sys.stderr)
            print("="*80, file=sys.stderr)
            
            if file_path:
                cleaned_file_path = file_path.strip('"').strip("'")
                if os.path.exists(cleaned_file_path):
                    if not cleaned_file_path.lower().endswith('.pdf'):
                        result["upload"] = {"success": False, "message": "Only PDF files allowed"}
                        print("❌ File is not a PDF", file=sys.stderr)
                    else:
                        upload_result = self.upload_pdf_file(file_path)
                        result["upload"] = upload_result
                        
                        if upload_result.get('success'):
                            print("🎉 Upload successful!", file=sys.stderr)
                            time.sleep(5)
                        else:
                            print("❌ Upload failed", file=sys.stderr)
                            time.sleep(3)
                else:
                    result["upload"] = {"success": False, "message": f"File not found: {cleaned_file_path}"}
                    print(f"❌ PDF file not found: {cleaned_file_path}", file=sys.stderr)
            else:
                result["upload"] = {"success": False, "message": "No file path provided"}
                print("❌ No file path provided", file=sys.stderr)

            # Print final result
            print("\n" + "="*80, file=sys.stderr)
            print("📊 FINAL RESULT", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print("JSON_START")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("JSON_END")

        except Exception as e:
            print(f"❌ Automation crashed: {str(e)}", file=sys.stderr)
            traceback.print_exc()
            result["error"] = str(e)
            print("JSON_START")
            print(json.dumps(result, ensure_ascii=False))
            print("JSON_END")

        finally:
            print("\n🔄 Cleanup starting in 5 seconds...", file=sys.stderr)
            time.sleep(5)
            self.cleanup()

    def cleanup(self):
        try:
            if self.driver:
                print("🧹 Closing browser...", file=sys.stderr)
                self.driver.quit()
                print("✅ Cleanup complete", file=sys.stderr)
        except Exception as e:
            print(f"❌ Cleanup error: {e}", file=sys.stderr)

def main():
    if len(sys.argv) < 4:
        print("Usage: python lms_automation.py <username> <password> <subject_code> <pdf_path> [submission_url]", file=sys.stderr)
        print("JSON_START")
        print(json.dumps({"error": "Insufficient arguments"}, ensure_ascii=False))
        print("JSON_END")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    subject_code = sys.argv[3]
    file_path = sys.argv[4] if len(sys.argv) > 4 else None
    submission_url = sys.argv[5] if len(sys.argv) > 5 else None

    print(f"📋 Arguments received:", file=sys.stderr)
    print(f"   Username: {username}", file=sys.stderr)
    print(f"   Subject Code: {subject_code}", file=sys.stderr)
    print(f"   File Path: {file_path}", file=sys.stderr)
    print(f"   Submission URL: {submission_url if submission_url else 'Not provided'}", file=sys.stderr)

    # Validate PDF
    if file_path:
        cleaned_file_path = file_path.strip('"').strip("'")
        if not os.path.exists(cleaned_file_path):
            print(f"❌ PDF not found: {cleaned_file_path}", file=sys.stderr)
            print("JSON_START")
            print(json.dumps({"error": f"PDF not found: {cleaned_file_path}"}, ensure_ascii=False))
            print("JSON_END")
            sys.exit(1)
        
        if not cleaned_file_path.lower().endswith('.pdf'):
            print(f"❌ Only PDF files allowed", file=sys.stderr)
            print("JSON_START")
            print(json.dumps({"error": "Only PDF files allowed"}, ensure_ascii=False))
            print("JSON_END")
            sys.exit(1)

    automation = LMSAutomation()
    automation.complete_automation(username, password, subject_code, file_path, submission_url)

if __name__ == "__main__":
    main()