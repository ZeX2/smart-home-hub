import os
import re
import json
import urllib.request

from bs4 import BeautifulSoup
from requests import Session, Request
from requests.adapters import HTTPAdapter

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

TIMEOUT = 100
API1 = 'https://www.atxfinearts.com/blogs/news/100-most-famous-paintings-in-the-world'
API2 = 'https://www.boredpanda.com/famous-paintings/?utm_source=google&utm_medium=organic&utm_campaign=organic'

class DailyPaintingsScraper():
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

    def get_paintings1(self):
        request = Request('GET', API1)
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        soup = soup.find('div', {'itemprop': 'articleBody'}, recursive=True)

        os.makedirs(os.path.join(FILE_DIR, 'paintings1'), exist_ok=True)
        paintings = []
        previous_title = ''
        i = 0
        painting = dict()
        for element in soup.find_all():
            child_element_a = element.find('a')
            child_element_span = element.find('span')
            if element.name == 'h3' and child_element_a and child_element_a.get('title'):
                title, painter = re.split(' By | by | - |\xa0by', child_element_a.get('title').strip())

                if title != previous_title:
                    if painting:
                        paintings.append(painting)
                    previous_title = title
                    painting = {'id': i,
                        'title': title,
                        'painter': painter,
                        'description': ''
                    }
                    i += 1
            elif element.name == 'h3' and child_element_span and 'by' in child_element_span.text:
                title, painter = re.split(' By | by | - |\xa0by', element.text.strip())
                if title != previous_title:
                    if painting:
                        paintings.append(painting)
                    previous_title = title
                    painting = {'id': i,
                        'title': title,
                        'painter': painter,
                        'description': ''
                    }
                    i += 1
            elif element.name == 'h3' and 'by' in element.text:
                title, painter = re.split(' By | by | - |\xa0by', element.text.strip())
                if title != previous_title:
                    if painting:
                        paintings.append(painting)
                    previous_title = title
                    painting = {'id': i,
                        'title': title,
                        'painter': painter,
                        'description': ''
                    }
                    i += 1
            elif element.name == 'img':
                img_link = f'https:{element.get("src").split("?v")[0]}'
                img_format = img_link.split('.')[-1]
                urllib.request.urlretrieve(img_link, os.path.join(FILE_DIR, 'paintings1', f'{i-1}.{img_format}'))
            elif element.text and not element.text.isspace() and element.name == 'p' and i > 0:
                if not painting['description']:
                    painting['description'] = element.text.replace(u'\xa0', u' ')
                if i == 100 and len(paintings) < 100:
                        paintings.append(painting)

        with open(os.path.join(FILE_DIR, 'paintings_data1.json'), 'w', encoding='utf-8') as f:
            json.dump(paintings, f, ensure_ascii=False, indent=4)

    def get_paintings2(self):
        request = Request('GET', API2)
        html = self.send(request).text

        soup = BeautifulSoup(html, features='html.parser')
        soup = soup.find('div', {'class': 'open-list-items clearfix'})

        os.makedirs(os.path.join(FILE_DIR, 'paintings2'), exist_ok=True)
        paintings = []
        for i, element in enumerate(soup.find_all('div', {'class': 'open-list-item open-list-block clearfix'})):
            print(i)
            title, painter =  re.split(' By | by | - ', element.find('h2').text.strip())
            img_link = element.find('img').get('src')
            img_format = img_link.split('.')[-1]
            description = element.find('div', {'class': 'bordered-description'})
            if description:
                description = description.text.replace(description.find('strong').text, '')

            urllib.request.urlretrieve(img_link, os.path.join(FILE_DIR, 'paintings2', f'{i}.{img_format}'))

            painting = {'id': i,
                        'title': title,
                        'painter': painter,
                        'description': description
            }
            paintings.append(painting)

        with open(os.path.join(FILE_DIR, 'paintings_data2.json'), 'w', encoding='utf-8') as f:
            json.dump(paintings, f, ensure_ascii=False, indent=4)

    def crop_images(self, dir, new_dir_name):
        import cv2
        import numpy as np

        dir = os.path.join(FILE_DIR, dir)
        files = os.listdir(dir)
        os.makedirs(os.path.join(FILE_DIR, new_dir_name), exist_ok=True)
        for file in files:
            img = cv2.imread(os.path.join(dir, file)) # image file
            #cv2.imshow("Image", img) # Show it
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = 255*(gray < 128).astype(np.uint8) # To invert the text to white
            gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((2, 2), dtype=np.uint8)) # Perform noise filtering
            coords = cv2.findNonZero(gray) # Find all non-zero points (text)
            x, y, w, h = cv2.boundingRect(coords) # Find minimum spanning bounding box
            rect = img[y:y+h-1, x:x+w-1] # Crop the image - note we do this on the original image
            #cv2.imshow("Cropped", rect) # Show it
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()
            cv2.imwrite(os.path.join(FILE_DIR, new_dir_name, os.path.basename(file)) , rect) # Save the image

if __name__ == '__main__':
    scraper = DailyPaintingsScraper()
    #scraper.get_paintings1()
    scraper.crop_images('paintings1', 'paintings1')