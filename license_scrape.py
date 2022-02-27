from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import datetime

from time import sleep
import pathlib
import pandas as pd

script_path = str(pathlib.Path(__file__).parents[0])
options = Options()
options.add_argument('log-level=3')
s=Service(ChromeDriverManager().install())
browser = Chrome(service=s, options = options)
browser.get('https://mylicense.in.gov/everification/Search.aspx')

def check_presence(el_name):
    try:
        element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, el_name))
            )
    except TimeoutException:
        print("Element not found. Retrying.")
        sleep(5)
    return element
print('Starting web scrape...')
profession = Select(check_presence('t_web_lookup__profession_name')).select_by_visible_text('Real Estate Commission')
license_type = Select(check_presence('t_web_lookup__license_type_name')).select_by_visible_text('Real Estate Broker')
license_status = Select(check_presence('t_web_lookup__license_status_name')).select_by_visible_text('Referral/Expired')
search = check_presence('sch_button').click()

def scrape(data):
            # scrape data
        for i in range(2,41):
            entry = {
                'name': browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[{i}]/td[1]/table/tbody/tr[1]/td').text,
                'license#':browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[{i}]/td[2]/span').text,
                'address':browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[{i}]/td[6]/span').text,
            }
            data.append(entry)
        return data

pages_left = True
pages_scraped = []
scraped_data = []
# current_page = None
while pages_left:
    pages = [el.text for el in browser.find_elements(By.XPATH, '//*[@id="datagrid_results"]/tbody/tr[42]/td')][0].split()   
    # nav pages
    #if its the 1st results page
    if pages[0] != '...' and pages[-1]=='...':
        for index, page in enumerate(pages[:-1]): 
            scrape(scraped_data)
            pages_scraped.append(page)
            print(f'Last page scraped: {pages_scraped[-1]}', end='\r')
            browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[42]/td/a[{index+1}]').click()
    #if its not the 1st or last page  
    elif pages[0] == '...' and pages[-1]=='...':
        for index, page in enumerate(pages[:-1]):
            pages_scraped.append(page)
            #skip backpage
            if page == '...' and index == 0:
                print(f'Last page scraped: {pages_scraped[-1]}', end='\r')
                browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[42]/td/a[{index+2}]').click()
            else:
                print(f'Last page scraped: {pages_scraped[-1]}', end='\r')
                browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[42]/td/a[{index+1}]').click()
    #if its the last page
    elif pages[0] == '...' and pages[-1] != '...':
        for index, page in enumerate(pages):
            if pages.index(page) < pages.index(pages_scraped[-2]):
                continue
            elif pages[index] == pages[-1]:
                print(f"All pages scraped. Saving results to {script_path}\{(datetime.date.today()).strftime('%b_%d_%Y')}_referral_expired_licenses.csv")
                scrape(scraped_data)
                df = pd.DataFrame(scraped_data)
                df.to_csv(f"{(datetime.date.today()).strftime('%b_%d_%Y')}_referral_expired_licenses.csv",index=False,)
                pages_left = False
            else:
                pages_scraped.append(page)
                scrape(scraped_data)
                browser.find_element(By.XPATH, f'//*[@id="datagrid_results"]/tbody/tr[42]/td/a[{index+1}]').click()
                print(f'Last page scraped: {pages_scraped[-1]}', end='\r')
browser.close()