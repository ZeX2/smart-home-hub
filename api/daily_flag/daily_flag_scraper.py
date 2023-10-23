import os
import json
import urllib.request

from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

TIMEOUT = 100
API = 'https://en.wikipedia.org/wiki/Gallery_of_sovereign_state_flags'

class DailyFlagScraper():
    def __init__(self):
        self.s = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)

    def send(self, request):
        response = self.s.send(request.prepare(), timeout=TIMEOUT)
        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f'{self.__class__.__name__} failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response

    def get_flags(self):
        request = Request('GET', API)
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        soup = soup.find_all('li', {'class': 'gallerybox'}, recursive=True)

        os.makedirs(os.path.join(FILE_DIR, 'flags'), exist_ok=True)
        flags = []

        for i, flag_soup in enumerate(soup):
            print(i)
            country = flag_soup.find('div', {'class': 'gallerytext'}).text.strip()
            if ', ' in country:
                country = country.split(', ')[1] + ' ' + country.split(', ')[0]

            img_link = 'https:' + flag_soup.find('img').get('src').split('.svg/')[0].replace('/thumb', '') + '.svg'
            urllib.request.urlretrieve(img_link, os.path.join(FILE_DIR, 'flags', f'{i}.svg'))

            flag = {'id': i,
                        'country': country,
            }

            flags.append(flag)

        with open(os.path.join(FILE_DIR, 'flags_data.json'), 'w', encoding='utf-8') as f:
            json.dump(flags, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    scraper = DailyFlagScraper()
    scraper.get_flags()