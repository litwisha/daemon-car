from abc import ABCMeta, abstractmethod, abstractproperty
from functools import partial
from logging import getLogger

from requests import Session

from lxml.html import document_fromstring

logger = getLogger(__file__)


class BaseParser(
    metaclass=ABCMeta,
):
    FILTERS = {
        'mileage', 'color', 'power',
    }

    def __init__(self, name, search_url, **filter_params):
        if not filter_params.keys() < self.FILTERS:
            raise ValueError('Incorrect filter parameters')

        self.filter_params = filter_params
        self.name = name

        self.search_url = search_url

        self.session = Session()

    def check_filter_params(self, params):
        """

        :param params:
        :return:
        """
        return params.keys() < self.FILTERS

    def custom_filter(self, name, result_item):
        """
        Add custom filter on search results
        :param name: filter name
        :param result_item: xpath element of car to filter
        :return: True - if car fits the filter
        """
        search_xpath = self.XPATHS[name]
        reg_exp = self.REGEXPS[name]

        filter_value = self.filter_params[name]

        try:
            filter_elem = result_item.xpath(
                search_xpath,
            )[0]

            matched_value = reg_exp.match(filter_elem.text).group(1)
        except (IndexError, AttributeError):
            return False
        else:

            return matched_value == str(filter_value)

    @property
    def filter_rules(self):
        return [
            partial(
                self.custom_filter,
                name=name,
            )
            for name in self.filter_params
        ]

    def parse_response(self, response):
        root = document_fromstring(response.text)

        parsed_ads = root.xpath(
            self.XPATHS['car_ads']
        )

        filtered_ads = filter(
            lambda x: all(rule(x) for rule in self.filter_rules),
            parsed_ads
        )

        ads = {x.get('data-ad-id') for x in filtered_ads}

        new_ads = ads - self.seen_ads

        if new_ads:
            self.process_batch(new_ads)
            self.seen_ads |= new_ads
        else:
            logger.info('No new suitable ads')
