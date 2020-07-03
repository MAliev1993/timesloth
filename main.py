import bs4
import requests
import smtplib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def getAvailableTimeSlot(rows: list) -> str:
    for week_row in rows:
        days = week_row.contents
        for day in days:
            types = list()
            types.append(type(day))
            if type(day) is bs4.element.Tag and len(day.contents) > 0:
                text = str(day.contents[0].contents[0])
                if text != 'Keine freien Termine am ':
                    return str(day.contents[1] + day.contents[2].contents[0])
    return "No available time slots"


def sendAlert(message: str):
    conn = smtplib.SMTP('smtp.gmail.com', 587)
    conn.ehlo()
    conn.starttls()
    conn.login('misha.freeway@gmail.com', '13krugovada')
    conn.sendmail('misha.freeway@gmail.com', 'm-z-a@yandex.ru', message)
    conn.quit()


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1200x600')

link = 'https://www.muenchen.de/rathaus/terminvereinbarung_fs.html?&loc=FS&ct=1071898'

driver = webdriver.Chrome(options=options)
driver.get(link)

driver.implicitly_wait(5)

driver.switch_to.frame(driver.find_element_by_xpath('//*[@id="appointment"]'))

driver.find_element_by_xpath('//*[@id="F00e214c9f52bf4cddab8ebc9bbb11b2b"]/fieldset/input[2]').click()

driver.implicitly_wait(3)

soup = bs4.BeautifulSoup(driver.page_source, 'html.parser')

week_rows = soup.contents[0].contents[2].contents[13].contents[1].contents[3].contents[1].contents[0].contents[1].contents[3].contents

result = getAvailableTimeSlot(week_rows)
#result = 'No available time slots'

if result != 'No available time slots':
    message = 'Subject: Available time slot: {}\n\n<a href="{}" target="_blank">link</a>'.format(result, link)
    sendAlert(message)

driver.quit()
