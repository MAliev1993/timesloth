import logging
import requests
from datetime import datetime, time
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
import pyautogui

# Create loggers
info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')

# Set levels
info_logger.setLevel(logging.INFO)
error_logger.setLevel(logging.ERROR)

# Create handlers
info_handler = logging.FileHandler('logs/info.log')
error_handler = logging.FileHandler('logs/error.log')

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Add handlers to loggers
info_logger.addHandler(info_handler)
error_logger.addHandler(error_handler)

ua = UserAgent()
userAgent = ua.random
info_logger.info(userAgent)

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
options.add_argument(f'user-agent={userAgent}')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Load extension (Optional, mimic human-like behavior)
# options.add_argument('load-extension=/path/to/extension')

url = 'https://stadt.muenchen.de/terminvereinbarung_/terminvereinbarung_abh.html?cts=1000113'
waiting_time = 3
retry_interval = 60


# Function to simulate human-like mouse movements
def human_like_mouse_movements(driver):
    actions = ActionChains(driver)
    actions.move_by_offset(random.randint(0, 100), random.randint(0, 100)).perform()

def solve_friendly_captcha(driver, site_key, endpoint, puzzle_url):
    try:
        info_logger.info("Starting Friendly CAPTCHA solving process")

        # Get the CAPTCHA puzzle using GET method
        puzzle_response = requests.get(puzzle_url, params={"sitekey": site_key})
        puzzle_response.raise_for_status()
        puzzle_data = puzzle_response.json()

        # Normally, you would solve the puzzle here. For this example, we'll assume the puzzle_data contains the solution.
        captcha_solution = puzzle_data.get("solution")

        if captcha_solution:
            info_logger.info("Friendly CAPTCHA solution obtained")
            # Inject the solution into the CAPTCHA field and submit the form
            driver.execute_script(f"document.getElementById('friendly-captcha-solution').value='{captcha_solution}';")
            driver.find_element(By.ID, 'captcha-form-submit-button').click()
            sleep(waiting_time)  # Wait for the page to reload after solving CAPTCHA
            return True
        else:
            error_logger.error("Failed to obtain Friendly CAPTCHA solution")
            return False
    except Exception as e:
        error_logger.error("Error solving Friendly CAPTCHA", exc_info=True)
        return False


def check_availability():
    info_logger.info("Starting check_availability function")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    driver.implicitly_wait(waiting_time)

    try:
        # Simulate human-like mouse movements
        human_like_mouse_movements(driver)

        # Switch to the iframe by ID
        WebDriverWait(driver, waiting_time).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))

        # Select the option in the select field and submit the form
        select = WebDriverWait(driver, waiting_time).until(
            EC.element_to_be_clickable((By.NAME, 'CASETYPES[Notfalltermin UA 35]')))
        select.click()

        option = WebDriverWait(driver, waiting_time).until(
            EC.element_to_be_clickable((By.XPATH, '//option[@value="1"]')))
        option.click()

        submit_button = WebDriverWait(driver, waiting_time).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'WEB_APPOINT_FORWARDBUTTON')))
        submit_button.click()

        info_logger.info("Form submitted successfully")

        # Wait for the next page to load
        sleep(waiting_time)

        # Detect and solve CAPTCHA
        if "captcha" in driver.page_source.lower():
            info_logger.info("CAPTCHA detected, attempting to solve")
            captcha_site_key = driver.execute_script("return captchaSiteKey;")
            captcha_endpoint = driver.execute_script("return captchaEndpoint;")
            captcha_puzzle = driver.execute_script("return captchaPuzzle;")

            if solve_friendly_captcha(driver, captcha_site_key, captcha_endpoint, captcha_puzzle):
                info_logger.info("Friendly CAPTCHA solved and form submitted")
            else:
                error_logger.error("Failed to solve Friendly CAPTCHA")
                return False

        # Check for the availability of appointments
        while True:
            current_time = datetime.now().time()
            if time(6, 0) <= current_time <= time(18, 0):  # Check only between 06:00 and 18:00, Monday to Friday
                driver.switch_to.default_content()
                WebDriverWait(driver, waiting_time).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))

                cells = driver.find_elements(By.CSS_SELECTOR, 'td.nat_calendar')

                for cell in cells:
                    if "Keine freien Termine am" not in cell.text and "5" in cell.text:
                        info_logger.info(f"Available appointment found: {cell.text}")
                        print(f"Available appointment found: {cell.text}")
                        return True
                    else:
                        info_logger.info(f"No available appointment in cell: {cell.text}")

                info_logger.info("No available appointments found, retrying after interval")
                sleep(retry_interval)
            else:
                info_logger.info("Out of checking hours. Waiting until next available check time.")
                sleep(retry_interval)
    except TimeoutException as e:
        error_logger.error("TimeoutException occurred", exc_info=True)
    except NoSuchElementException as e:
        error_logger.error("NoSuchElementException occurred", exc_info=True)
    finally:
        driver.quit()
        info_logger.info("Driver quit")


if __name__ == "__main__":
    available = check_availability()
    if available:
        info_logger.info("Appointment available")
    else:
        info_logger.info("No appointments available")
