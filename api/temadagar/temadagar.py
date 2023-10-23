from datetime import datetime

from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

# I don't think you can really call this an API either
TIMEOUT = 100
API = '''https://temadagar.se/{day}-{month}'''

MONTHS = ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli', 'augusti', 'september', 'oktober', 'november', 'december']

class TemadagarApi():
    def __init__(self):
        self.s = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)

        today = datetime.now()
        self.day, self.month = today.day, MONTHS[today.month-1]
        self.temadagar = []

    def send(self, request):
        response = self.s.send(request.prepare(), timeout=TIMEOUT)
        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f'{self.__class__.__name__} failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response

    def get_temadagar(self):
        today = datetime.now()
        day, month = today.day, MONTHS[today.month-1]

        new_day = not ((day, month) == (self.day, self.month))
        
        if new_day:
            self.day, self.month = day, month

        if new_day or not self.temadagar:
            request = Request('GET', API.format(day=self.day, month=self.month))
            html = self.send(request).text

            soup = BeautifulSoup(html, features='html.parser')
            temadagar = soup.find('div', {'id': 'content'}).find_all(['p'])[0].find_all(['a'])
            self.temadagar = [temadag.get_text(strip=True).capitalize() for temadag in temadagar]

        return self.temadagar
