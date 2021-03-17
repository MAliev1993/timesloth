import bs4
import smtplib
from selenium import webdriver
import logging
from fake_useragent import UserAgent


def check(calendar_rows: list, link: str):
    for day in calendar_rows:
        if day.text != '' and day.text[:24] != 'Keine freien Termine am ':
            sendAlert('Subject: Time slot available! \n\n{} Text: {}'.format(link, day.text))
            logger.info("Success! Time slot found: %s", day.text)
            break
    logger.info("Alas! No time slots found")


def sendAlert(message: str):
    from = 'a@example.org';
    to = 'b@example.org';
    pass = '12345';
    smtp_host = 'host.example.org';
    port = 587;
    conn = smtplib.SMTP(smtp_host, port)
    conn.ehlo()
    conn.starttls()
    conn.login(email, pass)
    conn.sendmail(from, to, message)
    conn.quit()


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

url = 'https://www.muenchen.de/rathaus/terminvereinbarung_fs.html?&loc=FS&ct=1071898'
waiting_time = 3

driver = webdriver.Chrome(options=options)
driver.get(url)

driver.implicitly_wait(waiting_time)

driver.switch_to.frame(driver.find_element_by_xpath('//*[@id="appointment"]'))

driver.find_element_by_xpath('//*[@id="F00e214c9f52bf4cddab8ebc9bbb11b2b"]/fieldset/input[2]').click()

driver.implicitly_wait(waiting_time)

soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

check(soup.findAll('td', {'class': 'nat_calendar'}), url)

driver.quit()
