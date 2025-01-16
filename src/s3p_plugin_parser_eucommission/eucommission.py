from datetime import datetime
import time
import dateparser
import logging
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class EUCommission(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    HOST = "https://ec.europa.eu/commission/presscorner/home/en?parea=AI,FINSTAB,BUSINDUS,CYBER,DIGAG,RESINSC,SECU,TECH,TRANSPORT"
    
    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, restrictions: S3PPluginRestrictions, web_driver: WebDriver):
        super().__init__(refer, plugin, restrictions)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        self._driver.get(self.HOST)
        time.sleep(3)

        # more_btn = self._driver.find_element(By.XPATH, '//*[contains(text(),\'More criteria\')]')
        # self._driver.execute_script('arguments[0].click()', more_btn)
        #
        # time.sleep(0.5)
        #
        # policy_list = self._driver.find_element(By.XPATH,
        #                                        '//label[@for = \'filter-parea\']/..//div[@class = \'ecl-select__multiple\']')
        #
        # self._driver.execute_script("arguments[0].scrollIntoView();", policy_list)
        # time.sleep(0.5)
        #
        # self._driver.execute_script('arguments[0].click()', policy_list)
        # policy_list.click()
        #
        # policies = self._driver.find_elements(By.XPATH, '//div[@class = \'ecl-checkbox\']')
        #
        # for policy in policies:
        #     self.logger.debug(policy.text)
        #     if policy.text in self.POLICIES:
        #         policy.click()
        # self._driver.execute_script("arguments[0].scrollIntoView();", policy_list)
        # time.sleep(0.5)
        #
        # self._driver.execute_script('arguments[0].click()', policy_list)
        #
        # submit_btn = self._driver.find_element(By.XPATH, '//button[@type = \'submit\']')
        #
        # self._driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
        # time.sleep(0.5)
        #
        # submit_btn.click()

        while True:

            time.sleep(3)

            list_items = self._driver.find_elements(By.CLASS_NAME, 'ecl-list-item')

            for item in list_items:
                title = item.find_element(By.TAG_NAME, 'h3').text
                pub_date = dateparser.parse(item.find_elements(By.CLASS_NAME, 'ecl-meta__item')[1].text)
                doc_type = item.find_elements(By.CLASS_NAME, 'ecl-meta__item')[0].text
                web_link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                try:
                    abstract = item.find_element(By.TAG_NAME, 'p').text
                except:
                    abstract = None

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])

                self._initial_access_source(web_link, 3)
                self._wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'ecl-container')))

                self.logger.debug(f'Enter {web_link}')

                try:
                    text_content = self._driver.find_element(By.XPATH, "//*[contains(@role,'article')]/div").text
                except:
                    self.logger.debug('No Text, skipping')
                    self._driver.close()
                    self._driver.switch_to.window(self._driver.window_handles[0])
                    continue
                other_data = {'doc_type': doc_type}

                doc = S3PDocument(
                    id=None,
                    title=title,
                    abstract=abstract,
                    text=text_content,
                    link=web_link,
                    storage=None,
                    other=other_data,
                    published=pub_date,
                    loaded=datetime.now(),
                )

                self._find(doc)

                print(doc)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])

            try:
                next_pg = self._driver.find_element(By.XPATH, '//a[@title = \'Go to next page\']')
                self._driver.execute_script("arguments[0].scrollIntoView();", next_pg)
                time.sleep(0.5)

                next_pg.click()
            except:
                self.logger.debug('No Next page')
                break

        # ---
        # ========================================
        ...

    def _initial_access_source(self, url: str, delay: int = 2):
        self._driver.get(url)
        self.logger.debug('Entered on web page ' + url)
        time.sleep(delay)
