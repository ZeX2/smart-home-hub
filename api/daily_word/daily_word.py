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
        word = soup.find('div', {'class': 'word-and-pronunciation'}).find('h1').get_text(strip=True).capitalize()
        definition = soup.find('div', {'class': 'wod-definition-container'}).find('p').get_text(strip=True)

        return word, definition

    def get_swe_word_and_def(self):
        # Get word from SAOB
        request = Request('GET', f'{SWE1_API}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        word = soup.find('div', {'class': 'eb-one-third equus dagens'}).find_next('a').get_text(strip=True).capitalize()
        def_link = soup.find('div', {'class': 'eb-one-third equus dagens'}).find_next('a').get('href')

        # Try to first get definition from SAOB
        request = Request('GET', f'{SWE1_API}/{def_link}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        definitions = soup.find('div', {'class': 'rawcontent'}).find_all('div', {'class': ['udda', 'jamn']})
        definitions = [tag for tag in definitions if tag.find_next('span', {'class': 'StorAntikva'}).get('class') == ['StorAntikva']]  
        definitions = [tag.find('span', {'class': 'StorAntikva'}) for tag in definitions]
        if definitions:
            definition = ''.join([tag.text for tag in definitions[:3] if tag])
            return word, definition

        # Otherwise, try to get definition from synonymer.se
        request = Request('GET', f'{SWE2_API}/{word.lower()}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        if soup.find('div', {'data-section': 'Vad betyder'}):
            definition = soup.find('div', {'data-section': 'Vad betyder'}).find('div', {'class': 'body'}).find_next('li')
            definition = definition.get_text(strip=True).split('||')[0]
        else:
            definition = soup.find('div', {'data-section': 'Synonymer till'}).find('div', {'class': 'body'}).find_next('li')
            definition = definition.get_text(strip=True)

        return word, definition
