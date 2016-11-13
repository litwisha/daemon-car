from abc import ABCMeta, abstractmethod, abstractproperty
from datetime import date
from functools import partial
from logging import getLogger

from requests import Session

from lxml.html import document_fromstring

from . import redis_client

logger = getLogger(__file__)


class BaseParser(
    metaclass=ABCMeta,
):
    FILTERS = {
        'mileage', 'color', 'power',
    }

    def __init__(self, search_name, search_url, **filter_params):
        if not filter_params.keys() < self.FILTERS:
            raise ValueError('Incorrect filter parameters')

        self.filter_params = filter_params
        self.search_name = '{parser}_{search_name}'.format(
            parser=self.NAME,
            search_name=search_name,
        )

        self.search_url = search_url

        self.session = Session()

    @abstractproperty
    def car_url(self):
        pass

    @abstractmethod
    def get_car_ids(self, elements):
        pass

    @property
    def filter_rules(self):
        return [
            partial(
                self.custom_filter,
                name=name,
            )
            for name in self.filter_params
        ]

    @property
    def today_ads(self):
        if not hasattr(self, '_today_ads'):
            key = '{search_name}_{date}'.format(
                search_name=self.search_name,
                date=date.today().strftime('%d_%m_%y')
            )
            self._today_ads = redis_client.smembers(key)

        return self._today_ads

    @today_ads.setter
    def today_ads(self, ads):
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

        if not hasattr(self, '_seen_ads'):
            self._seen_ads = redis_client.smembers(self.search_name)

        return self._seen_ads

    @seen_ads.setter
    def seen_ads(self, ads):
        key = self.search_name

        new_ads = ads - self.seen_ads

        for ad in new_ads:
            redis_client.sadd(key, ad)

        # invalidate cached property
        del self._seen_ads

    def custom_filter(self, name, result_item):
        """
        Add custom filter on search results
        :param name: filter name
        :param result_item: xpath element of car to filter
        :return: True - if car fits the filter
        """
        search_xpath = self.XPATHS[name]

        filter_value = self.filter_params[name]

        try:
            filter_elem = result_item.xpath(
                search_xpath,
            )[0]

            value = filter_elem.text

            if name in self.REGEXPS:
                reg_exp = self.REGEXPS[name]
                value = reg_exp.match(value).group(1)

        except (IndexError, AttributeError):
            return False
        else:

            return value == str(filter_value)

    def parse_response(self, response):
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
        else:
            logger.info('No new suitable ads')

    def request(self):
        try:
            response = self.session.get(
                self.search_url,
            )

            if response.status_code == 200:
                self.parse_response(response)
            else:
                msg = '{name} has responsed with {code}'.format(
                    name=self.search_name,
                    code=str(response.status_code)
                )
                logger.debug(msg)

        except IOError as e:
            logger.exception(e)

