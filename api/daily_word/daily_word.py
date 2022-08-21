from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

# I don't think you can really call this an API 
TIMEOUT = 100
ENG_API = 'https://www.merriam-webster.com/word-of-the-day'
SWE1_API = 'https://www.saob.se'
SWE2_API = 'https://www.synonymer.se/sv-syn/'

class DailyWordApi():
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
                raise Exception(f'DailyWord API failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response

    def get_eng_word_and_def(self):
        request = Request('GET', f'{ENG_API}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        word = soup.find('div', {'class': 'word-and-pronunciation'}).find('h1').text.capitalize()
        definition = soup.find('div', {'class': 'wod-definition-container'}).find('p').text

        return word, definition

    def get_swe_word_and_def(self):
        request = Request('GET', f'{SWE1_API}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        word = soup.find('div', {'class': 'eb-one-third equus dagens'}).find_next('a').text.strip().capitalize()

        request = Request('GET', f'{SWE2_API}/{word.lower()}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        definition = soup.find('div', {'data-section': 'Vad betyder'}).find('div', {'class': 'body'}).find_next('li').text
        definition = definition.strip().split('||')[0]

        return word, definition
