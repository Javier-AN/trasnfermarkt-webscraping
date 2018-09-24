import logging

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from time import sleep


class WebScraper:
    base_url = ''

    @staticmethod
    def get_soup(url, external=False, retry=999):
        try:
            if not external:
                url = WebScraper.base_url + url
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            client = urlopen(req)
            page_html = client.read()
            client.close()
            return BeautifulSoup(page_html, 'html.parser')
        except:
            if retry:
                logging.warning("Retry connection ({}): {}".format(retry, url))
                sleep(5)
                return WebScraper.get_soup(url, True, retry - 1)
            return None

    @staticmethod
    def format(string):
        return ''.join(e for e in string.strip().lower().replace(' ', '-') if e.isalnum() or e == '-')

    @staticmethod
    def get_vars(url):
        return url.strip().split('/')
