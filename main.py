from httpx import Client, Cookies
from selectolax.parser import HTMLParser
from dataclasses import dataclass
from dotenv.main import load_dotenv
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import os
from urllib.parse import urljoin
import pandas as pd

load_dotenv()

@dataclass
class Ferrscrape:
    base_url: str = 'https://www.eurospares.co.uk'
    cookies: Cookies = None
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

    def webdriversetup(self):
        ff_opt = Options()
        ff_opt.add_argument('-headless')
        ff_opt.add_argument('--no-sandbox')
        ff_opt.set_preference("general.useragent.override", self.user_agent)
        ff_opt.page_load_strategy = 'eager'
        driver = WebDriver(options=ff_opt)

        return driver

    def get_cookies(self):
        url = urljoin(self.base_url, '/Identity/Account/Login?returnurl=%2F')
        driver = self.webdriversetup()
        driver.maximize_window()
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # login
        creds = os.getenv('EMAIL') + Keys.TAB + os.getenv('PASS') + Keys.RETURN
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'input[data-val-email="The Email field is not a valid e-mail address."]'))).send_keys(creds)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'i.fa-address-book')))
        cookies = driver.get_cookies()

        httpx_cookies = Cookies()
        for cookie in cookies:
            httpx_cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        self.cookies = httpx_cookies

        driver.close()

    def fetch(self, endpoint):
        url = urljoin(scraper.base_url, endpoint)
        headers = {
            # 'User-Agent':'Mozilla/5.0 (X11; Linux x86_64)'
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'
        }

        with Client(headers=headers) as client:
            client.cookies.update(self.cookies)
            response = client.get(url)
        if response.status_code != 200:
            response.raise_for_status()

        return response

    def parse(self, response):
        datas = list()
        tree = HTMLParser(response.text)
        part_elems = tree.css('div.parts-table > div.row')
        for elem in part_elems:
            description_elem = elem.css_first('div.col-12')
            detail_part_elems = description_elem.css('div.row.bg-box > div.col-12')
            for detail_part_elem in detail_part_elems:
                data = dict()
                data['#'] = elem.css_first('div.col-3').text(strip=True)
                data['part_number'] = elem.css_first('div.col-9').text(strip=True)
                data['description'] = elem.css_first('div.col-12').text(strip=True)
                try:
                    data['key'] = elem.css_first('button.btn.btn-success.btn-icon.btn-sm').text(strip=True)
                except:
                    data['key'] = elem.css_first('button.btn.btn-outline-secondary.btn-icon.btn-sm')
                data['detail'] = detail_part_elem.css_first('a.part-name').text(strip=True)
                data['price'] = detail_part_elem.css_first('span.cart-price-animation').text(strip=True)
                datas.append(data)

        return datas


if __name__ == '__main__':
    scraper = Ferrscrape()
    scraper.get_cookies()
    endpoints = ['/Ferrari/Daytona_SP3/Daytona_SP3/PartDiagrams/E_61/BATTERY_INSTALLATION',
                 '/Ferrari/Daytona_SP3/Daytona_SP3/PartDiagrams/F_01/BATTERIES',
                 '/Ferrari/512/512_BB/PartDiagrams/003/Cylinder_Head_(Right)']
    responses = list()
    results = list()
    for endpoint in endpoints:
        responses.append(scraper.fetch(endpoint))
    for response in responses:
        results.extend(scraper.parse(response))

    result_df = pd.DataFrame.from_records(results)
    print(result_df)
    result_df.to_csv('sample_result.csv', index=False)

