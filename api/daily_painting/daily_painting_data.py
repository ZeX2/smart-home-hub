import os
import json
import random
from glob import glob

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

PAINTINGS1_DATA_PATH = os.path.join(FILE_DIR , 'paintings1_data.json')
PAINTINGS2_DATA_PATH = os.path.join(FILE_DIR , 'paintings2_data.json')


class DailyPaintingData():
    def __init__(self):
        with open(PAINTINGS1_DATA_PATH, 'r', encoding='utf-8') as f:
            paintings1_data = json.load(f)

        with open(PAINTINGS2_DATA_PATH, 'r', encoding='utf-8') as f:
            paintings2_data = json.load(f)

        self.data = [paintings1_data, paintings2_data]

        self.i = None
        self.j = None
        self.random_painting()

    def get_painting(self):
        painting = self.data[self.i][self.j]
        painting_img_path = glob(os.path.join(FILE_DIR , f'paintings{self.i+1}', f'{self.j}*'))[0]
        return painting['title'], painting['painter'], painting['description'], painting_img_path

    def random_painting(self):
        self.i = random.randint(0, len(self.data)-1)
        self.j = random.randint(0, len(self.data[self.i])-1)
        
        return self.get_painting()

    def next_painting(self):
        self.j = (self.j + 1) % len(self.data[self.i])
        if self.j == 0:
            self.i = (self.i + 1) % len(self.data)

        return self.get_painting()

    def previous_painting(self):
        self.j = (self.j - 1) % len(self.data[self.i])
        if self.j == len(self.data[self.i])-1:
            self.i = (self.i - 1) % len(self.data)
            self.j = len(self.data[self.i])-1

        return self.get_painting()
