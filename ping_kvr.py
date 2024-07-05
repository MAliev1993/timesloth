import os
import logging
import json
from datetime import datetime, time
from time import sleep
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent

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
userAgent = ua.chrome  # Use a common browser user-agent
info_logger.info(userAgent)

chrome_profile_path = './chrome_profile'
user_agent_data = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
options.add_argument(f'user-agent={userAgent}')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(f"user-data-dir={os.path.abspath(chrome_profile_path)}")
options.add_argument(f"user-agent={user_agent_data}")

url = 'https://stadt.muenchen.de/terminvereinbarung_/terminvereinbarung_abh.html?cts=1000113'
waiting_time = 3
retry_interval = 15


# Function to randomize sleep
def random_sleep(min_time, max_time):
    sleep(random.uniform(min_time, max_time))


def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)


def load_cookies(driver, path):
    with open(path, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)


def check_availability(driver):
    info_logger.info("Starting check_availability function")
    driver.get(url)

    driver.implicitly_wait(waiting_time)

    # Load cookies if available
    try:
        load_cookies(driver, 'cookies.json')
        driver.refresh()
    except FileNotFoundError:
        info_logger.info("No cookies file found, starting fresh")

    try:
        random_sleep(2, 5)

        # Switch to the iframe by ID
        WebDriverWait(driver, waiting_time).until(
            ec.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))

        # Select the option in the select field and submit the form
        select = WebDriverWait(driver, waiting_time).until(
            ec.element_to_be_clickable((By.NAME, 'CASETYPES[Notfalltermin UA 35]')))
        select.click()

        option = WebDriverWait(driver, waiting_time).until(
            ec.element_to_be_clickable((By.XPATH, '//option[@value="1"]')))
        option.click()

        submit_button = WebDriverWait(driver, waiting_time).until(
            ec.element_to_be_clickable((By.CLASS_NAME, 'WEB_APPOINT_FORWARDBUTTON')))
        submit_button.click()

        info_logger.info("Form submitted successfully")

        # Wait for the next page to load
        sleep(waiting_time)

        # Detect and solve CAPTCHA
        if "captcha" in driver.page_source.lower():
            info_logger.info("CAPTCHA detected, attempting to solve")
            return False

        # Save cookies
        save_cookies(driver, 'cookies.json')

        # Check for the availability of appointments
        while True:
            current_time = datetime.now().time()
            if time(6, 0) <= current_time <= time(18, 0):  # Check only between 06:00 and 18:00, Monday to Friday
                driver.switch_to.default_content()
                WebDriverWait(driver, waiting_time).until(
                    ec.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))

                cells = driver.find_elements(By.CSS_SELECTOR, 'td.nat_calendar')

                for cell in cells:
                    if "Keine freien Termine am" not in cell.text and "5" in cell.text:
                        info_logger.info(f"Available appointment found: {cell.text}")
                        print(f"Available appointment found: {cell.text}")
                        return True
                    else:
                        info_logger.info(f"No available appointment in cell: {cell.text}")

                info_logger.info("No available appointments found, retrying after interval")
                random_sleep(retry_interval - 10, retry_interval + 10)
            else:
                info_logger.info("Out of checking hours. Waiting until next available check time.")
                random_sleep(retry_interval - 10, retry_interval + 10)
    except TimeoutException as e:
        error_logger.error("TimeoutException occurred", exc_info=True)
    except NoSuchElementException as e:
        error_logger.error("NoSuchElementException occurred", exc_info=True)
    finally:
        driver.quit()
        info_logger.info("Driver quit")


if __name__ == "__main__":
    d = webdriver.Chrome(options=options)
    available = check_availability(d)
    if available:
        info_logger.info("Appointment available")
    else:
        info_logger.info("No appointments available")
