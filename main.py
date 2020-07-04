import bs4
import smtplib
from selenium import webdriver
import logging
# from datetime import datetime
from fake_useragent import UserAgent


def check(calendar_rows: list, link: str):
    # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for day in calendar_rows:
        if day.text != '' and day.text[:24] != 'Keine freien Termine am ':
            sendAlert('Subject: Time slot available! \n\n{} Text: {}'.format(link, day.text))
            logging.info("Success! Time slot found: %s", day.text)
            print("{}: Success! Time slot found: {}".format(current_time, day.text))
            break
    logging.info("Alas! No time slots found")
    # print("{}: Alas! No time slots found".format(current_time))


def sendAlert(message: str):
    conn = smtplib.SMTP('smtp.gmail.com', 587)
    conn.ehlo()
    conn.starttls()
    conn.login('misha.freeway@gmail.com', '13krugovada')
    conn.sendmail('misha.freeway@gmail.com', 'm-z-a@yandex.ru', message)
    conn.quit()


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

ua = UserAgent()
userAgent = ua.random
logging.info(userAgent)

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
