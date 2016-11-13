import regex

from .base import BaseParser


class MobileDeParser(BaseParser):
    NAME = 'mobile_de'

    XPATHS = {
        'car_ads': '//div[@class="cBox-body cBox-body--resultitem"]/a',
        'power': 'div/div[@class="g-col-9"]/div[2]/div/div[@class="rbt-regMilPow"]',
        'pagination': '//*[@class="pagination"]/li'
    }

    REGEXPS = {
        'power': regex.compile(r'^.*\((\d+).PS\)$'),
    }

    @property
    def car_url(self):
        return 'http://suchen.mobile.de/fahrzeuge/details.html?id={car_id}'

    @property
    def search_url(self):
        return '{search_url}&pageNumber={p_number}'.format(
            search_url=self._search_url,
            p_number=self.current_page,
        )

    def get_car_ids(self, results):
        return {x.get('data-ad-id') for x in results}

    def get_pages_amount(self, root):
        """
        Get last page number in pagination bar.
        There are two html blocks, where pagination bar may be spotted
        :param root:
        :return:
        """
        p_numbers_v1 = root.xpath('//*[@class="pagination"]/li/a/text()')
        p_numbers_v2 = root.xpath('//*[@class="paginationAB"]/li/span/text()')

        p_numbers = []

        for num in (p_numbers_v1 or p_numbers_v2):
            try:
                p_numbers.append(
                    int(num)
                )
            except ValueError:
                continue

        if p_numbers:
            return max(p_numbers)
