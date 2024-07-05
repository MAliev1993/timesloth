from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import datetime
import logging
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
userAgent = ua.random
info_logger.info(userAgent)

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
options.add_argument(f'user-agent={userAgent}')

url = 'https://stadt.muenchen.de/terminvereinbarung_/terminvereinbarung_abh.html?cts=1000113'
wait_interval = 3
retry_interval = 60

driver = webdriver.Chrome(options=options)
driver.get(url)

driver.implicitly_wait(wait_interval)

def check_availability():
    # Switch to the iframe
    try:
        WebDriverWait(driver, wait_interval).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))
    except Exception as e:
        error_logger.error("Error switching to iframe:", e)
        error_logger.error(driver.page_source)  # Print the page source for debugging
        return False

    # Locate the select field and change its value
    try:
        select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'CASETYPES[Notfalltermin UA 35]')))
        select = Select(select_element)
        select.select_by_value('1')
    except Exception as e:
        error_logger.error("Error selecting value in the select field:", e)
        return False

    # Locate and click the submit button
    try:
        submit_button = driver.find_element(By.CLASS_NAME, 'WEB_APPOINT_FORWARDBUTTON')
        submit_button.click()
    except Exception as e:
        error_logger.error("Error clicking the submit button:", e)
        return False

    info_logger.info("Form submitted successfully")

    # Wait for the new page to load
    time.sleep(retry_interval)

    # Switch to the iframe again on the new page
    try:
        WebDriverWait(driver, wait_interval).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))
    except Exception as e:
        error_logger.error("Error switching to iframe on the new page:", e)
        error_logger.error(driver.page_source)  # Print the page source for debugging
        return False

    # Check for available appointment slots
    try:
        calendar_cells = driver.find_elements(By.CSS_SELECTOR, 'td.nat_calendar')
        today_day = datetime.datetime.now().day

        for cell in calendar_cells:
            span_text = cell.find_element(By.TAG_NAME, 'span').text
            if 'Keine freien Termine am' not in span_text and str(today_day) in span_text:
                print(f"Available slot found: {cell.text}")
                return True
        return False
    except Exception as e:
        error_logger.error(f"Error while checking availability: {e}")
        return False

def is_within_operating_hours():
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # Saturday and Sunday are 5 and 6
        return False
    if now.hour < 6 or now.hour >= 18:
        return False
    return True

try:
    while True:
        if is_within_operating_hours():
            available = check_availability()
            if available:
                info_logger.info("Appointment available. Exiting...")
                break
            else:
                info_logger.info("No available appointments. Checking again in 60 seconds...")
        else:
            info_logger.info("Outside operating hours. Waiting...")

        time.sleep(retry_interval)
finally:
    driver.quit()
