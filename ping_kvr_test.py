from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import datetime
import logging
from fake_useragent import UserAgent

logger = logging.getLogger('CopasiTools')
logger.setLevel(logging.INFO)
log_filename = 'timesloth.log'
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler = logging.FileHandler(log_filename, 'a')
handler.setFormatter(formatter)
logger.addHandler(handler)
# logging.basicConfig(filename=log_filename, format='%(asctime)s - %(message)s', level=logging.INFO)

ua = UserAgent()
userAgent = ua.random
logger.info(userAgent)

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')
options.add_argument(f'user-agent={userAgent}')

url = 'https://stadt.muenchen.de/terminvereinbarung_/terminvereinbarung_abh.html?cts=1000113'
waiting_time = 3

driver = webdriver.Chrome(options=options)
driver.get(url)

driver.implicitly_wait(waiting_time)

def check_availability():
    # Switch to the iframe
    try:
        WebDriverWait(driver, waiting_time).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))
    except Exception as e:
        print("Error switching to iframe:", e)
        print(driver.page_source)  # Print the page source for debugging
        return False

    # Locate the select field and change its value
    try:
        select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'CASETYPES[Notfalltermin UA 35]')))
        select = Select(select_element)
        select.select_by_value('1')
    except Exception as e:
        print("Error selecting value in the select field:", e)
        return False

    # Locate and click the submit button
    try:
        submit_button = driver.find_element(By.CLASS_NAME, 'WEB_APPOINT_FORWARDBUTTON')
        submit_button.click()
    except Exception as e:
        print("Error clicking the submit button:", e)
        return False

    # Wait for the new page to load
    time.sleep(5)

    # Switch to the iframe again on the new page
    try:
        WebDriverWait(driver, waiting_time).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'appointment')))
    except Exception as e:
        print("Error switching to iframe on the new page:", e)
        print(driver.page_source)  # Print the page source for debugging
        return False

    # Check for "Keine freien Termine am" for July 5th
    try:
        calendar_cells = driver.find_elements(By.CSS_SELECTOR, 'td.nat_calendar')

        for cell in calendar_cells:
            span_text = cell.find_element(By.TAG_NAME, 'span').text
            if 'Keine freien Termine am' in span_text and '5.7.2024' in span_text:
                print(f"'Keine freien Termine am 5.7.2024' found: {cell.text}")
                return True
        print("'Keine freien Termine am 5.7.2024' not found")
        return False
    except Exception as e:
        print(f"Error while checking availability: {e}")
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
                print("Availability check passed. Exiting...")
                break
            else:
                print("Check completed. Checking again in 60 seconds...")
        else:
            print("Outside operating hours. Waiting...")

        time.sleep(60)
finally:
    driver.quit()
