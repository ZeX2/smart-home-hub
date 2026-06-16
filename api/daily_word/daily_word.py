from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

# I don't think you can really call this an API
TIMEOUT = 100
ENG_API = 'https://www.merriam-webster.com/word-of-the-day'
ENG_API_DEF = '''https://www.merriam-webster.com/dictionary/{word}'''
SWE_API = 'https://www.dagensdatum.nu/dagens/ord'

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/124.0.0.0 Safari/537.36'),
    'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
               'image/avif,image/webp,*/*;q=0.8'),
    'Accept-Language': 'en-US,en;q=0.9',
    'Upgrade-Insecure-Requests': '1',
}

class DailyWordApi():
    def __init__(self):
        self.s = Session()
        self.s.headers.update(HEADERS)
        adapter = HTTPAdapter(max_retries=3)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)

    def send(self, request):
        response = self.s.send(self.s.prepare_request(request), timeout=TIMEOUT)
        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f'{self.__class__.__name__} failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response

    def get_eng_word_and_def(self):
        request = Request('GET', ENG_API)
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        word = soup.find('div', {'class': 'word-and-pronunciation'}).find_all(['h1', 'h2', 'h3', 'h4', 'h5'])[0].get_text(strip=True).capitalize()

        request = Request('GET', ENG_API_DEF.format(word=word))
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        definitions = soup.find('div', {'class': 'vg'}).find_all('div', {'class': 'vg-sseq-entry-item'})
        definitions = [d.find('span', {'class': 'dt'}).get_text().strip().lstrip(':').strip() for d in definitions]
        definitions = '; '.join(definitions).capitalize() +  '.'

        return word, definitions

    def get_swe_word_and_def(self):
        # Get word from SAOB
        request = Request('GET', SWE_API)
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        word = soup.find('div', {'class': 'card-body'}).find_all(['h1', 'h2', 'h3', 'h4', 'h5'])[0].get_text(strip=True).capitalize()
        definition = soup.find('p', {'class': 'card-text'}).get_text(strip=True).capitalize()

        return word, definition
