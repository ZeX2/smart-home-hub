from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

from .note_id import NOTE_ID

# I don't think you can really call this an API 
TIMEOUT = 100
API = 'https://app.simplenote.com/p'

class SimpleNoteApi():
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
                raise Exception(f'SimpleNote API failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response
    
    def get_note(self):
        request = Request('GET', f'{API}/{NOTE_ID}')
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        soup.find('p', {'id': 'title'}).decompose()
        data = soup.findAll('div', {'class': 'note note-detail-markdown'})[0]

        return str(data)
