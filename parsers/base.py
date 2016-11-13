import logging
from abc import ABCMeta, abstractmethod, abstractproperty
from datetime import date
from functools import partial

from lxml.html import document_fromstring
from requests import Session

from config import settings

redis_client = settings.redis_client


class BaseParser(
    metaclass=ABCMeta,
):
    FILTERS = {
        'mileage', 'color', 'power',
    }

    def __init__(self, search_name, search_url, max_pages=5, **filter_params):
        # check if input filter params are valid
        if not filter_params.keys() < self.FILTERS:
            raise ValueError('Incorrect filter parameters')

        self.filter_params = filter_params

        self.search_name = '{parser}_{search_name}'.format(
            parser=self.NAME,
            search_name=search_name,
        )

        self._search_url = search_url

        self.current_page = 1
        self.max_pages = max_pages

        self.logger = logging.getLogger(self.search_name)
        self.logger.setLevel(logging.DEBUG)

        self.session = Session()

    @abstractproperty
    def car_url(self):
        """
        Full url with a car. Used for final results
        :return:
        """
        pass

    @abstractproperty
    def search_url(self):
        """
        Search url based on page number
        :return:
        """
        pass

    @abstractmethod
    def get_car_ids(self, results):
        """
        Get cars ids
        :param results: search results with a car
        :return:
        """
        pass

    @abstractmethod
    def get_pages_amount(self, root):
        """
        Get last page number in pagination bar.
        :param root:
        :return:
        """
        pass

    @property
    def filter_rules(self):
        """
        Get filters for search results.
        Available filters: mileage, power, color,
        :return:
        """
        return [
            partial(
                self.custom_filter,
                filter_name=name,
            )
            for name in self.filter_params
        ]

    @property
    def today_ads(self):
        """
        Cached property with cars found today.
        :return:
        """
        if not hasattr(self, '_today_ads'):
            key = '{search_name}_{date}'.format(
                search_name=self.search_name,
                date=date.today().strftime('%d_%m_%y')
            )
            self._today_ads = redis_client.smembers(key)

        return self._today_ads

    @today_ads.setter
    def today_ads(self, ads):
        """
        Setter for cached property with cars found today.
        :return:
        """

        key = '{search_name}_{date}'.format(
            search_name=self.search_name,
            date=date.today().strftime('%d_%m_%y')
        )
        new_ads = ads - self.today_ads

        for ad in new_ads:
            redis_client.sadd(key, ad)

        # invalidate cached property
        del self._today_ads

    @property
    def seen_ads(self):
        """
        Cached property with already seen ads.
        :return:
        """

        if not hasattr(self, '_seen_ads'):
            self._seen_ads = redis_client.smembers(self.search_name)

        return self._seen_ads

    @seen_ads.setter
    def seen_ads(self, ads):
        """
        Setter for cached property with already seen ads.
        :return:
        """
        key = self.search_name

        new_ads = ads - self.seen_ads

        for ad in new_ads:
            redis_client.sadd(key, ad)

        # invalidate cached property
        del self._seen_ads

    def custom_filter(self, result_item, filter_name):
        """
        Add custom filter on search results
        :param name: filter name
        :param result_item: xpath element of car to filter
        :return: True - if car fits the filter
        """
        search_xpath = self.XPATHS[filter_name]

        filter_value = self.filter_params[filter_name]

        try:
            filter_elem = result_item.xpath(
                search_xpath,
            )[0]

            value = filter_elem.text

            if filter_name in self.REGEXPS:
                reg_exp = self.REGEXPS[filter_name]
                value = reg_exp.match(value).group(1)

        except (IndexError, AttributeError):
            return False
        else:

            return value == str(filter_value)

    def request(self):
        """
        Send request to source website
        :return:
        """
        try:
            response = self.session.get(
                self.search_url,
            )

            if response.status_code == 200:
                self.parse_response(response)

            else:
                msg = '{name} has responsed with {code}'.format(
                    name=self.search_name,
                    code=response.status_code
                )
                self.logger.error(msg)

        except IOError as e:
            self.logger.exception(e)

    def parse_response(self, response):
        """
        Parse response and process results
        :param response:
        :return:
        """
        root = document_fromstring(response.text)

        parsed_ads = root.xpath(
            self.XPATHS['car_ads']
        )

        filtered_ads = filter(
            lambda x: all(rule(x) for rule in self.filter_rules),
            parsed_ads
        )

        ads = self.get_car_ids(filtered_ads)

        new_ads = ads - self.seen_ads

        if new_ads:
            self.seen_ads = new_ads
            self.today_ads = new_ads

            self.logger.info(
                'Parsing {page}: {new_ads} new ads found'.format(
                    page=self.current_page,
                    new_ads=len(new_ads),
                )
            )

        else:
            self.logger.info('No new suitable ads')

        # get information about maximum amount of pages
        max_pages = self.get_pages_amount(root)

        if max_pages and max_pages < self.max_pages:
            self.max_pages = max_pages

    def start(self):
        """
        Startpoint for running a parser
        :return:
        """
        while self.current_page <= self.max_pages:
            self.request()

            self.current_page += 1
