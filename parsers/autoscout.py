from urllib.parse import parse_qs, urlparse

from selenium import webdriver

from .base import BaseParser
from config import settings


class AutoScoutParser(BaseParser):
    NAME = 'auto_scout'

    XPATHS = {
        'car_ads': '//div[@id="listOutput"]//div[contains(@class, "list-item")]',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.driver = webdriver.PhantomJS(
            executable_path=settings.PHANTOMJS_PATH,
        )

    @property
    def car_url(self):
        return 'https://www.autoscout24.ru/Details.aspx?id={car_id}'

    @property
    def search_url(self):
        return '{search_url}&page={p_number}'.format(
            search_url=self._search_url,
            p_number=self.current_page,
        )

    def get_car_ids(self, results):
        ids = set()

        for result in results:
            url = result.xpath('div/div/a')[0].get('href')

            params = parse_qs(
                urlparse(url).query
            )

            ids.add(
                params['id'][0]
            )

        return ids

    def get_pages_amount(self, root):
        """
        Get last page number in pagination bar.
        There are two html blocks, where pagination bar may be spotted
        :param root:
        :return:
        """
        p_numbers = root.xpath('//ul[@class="paging"]/li[@class="page"]/text()')

        if p_numbers:
            return max(
                int(numb) for numb in p_numbers,
            )

    def request(self):
        """
        Send request to source website by means of Selenium driver
        :return:
        """
        try:
            self.driver.get(self.search_url)

            # hack: send plaint request to get status code
            response = self.session.get(self.search_url)

            if response.status_code == 200:
                self.parse_response(
                    self.driver.page_source,
                )

            else:
                msg = '{name} has responsed with {code}'.format(
                    name=self.search_name,
                    code=response.status_code
                )
                self.logger.error(msg)

        except IOError as e:
            self.logger.exception(e)
