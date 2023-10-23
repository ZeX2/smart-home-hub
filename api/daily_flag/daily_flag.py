import os
import json
import random

FILE_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS_DATA_PATH = os.path.join(FILE_DIR , 'data.json')

class DailyFlagData():
    def __init__(self):
        with open(FLAGS_DATA_PATH, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.i = None
        self.random_flag()

    def get_flag(self):
        flag = self.data[self.i]
        flag_img_path = os.path.join(FILE_DIR, 'flags', f'{self.i}.svg')
        return flag['country'], flag_img_path

    def random_flag(self):
        self.i = random.randint(0, len(self.data)-1)
        return self.get_flag()

    def next_flag(self):
        self.i = (self.i + 1) % len(self.data)
        return self.get_flag()

    def previous_flag(self):
        self.i = (self.i - 1) % len(self.data)
        return self.get_flag()
