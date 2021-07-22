import os

import pandas as pd
from rapidfuzz import fuzz, process

APPDIR_PATH = os.path.dirname(os.path.abspath(__file__))
ALL_DATA_PATH = os.path.join(APPDIR_PATH, 'SE.txt')
DATA_PATH = os.path.join(APPDIR_PATH, 'SE.pkl')

ALL_HEADER_NAMES = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude',' feature class', 'feature code', 'country code',
    'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code', 'population', 'elevation', 'dem', 'timezone', 'modification date']
KEEP_HEADER_NAMES = ['name', 'latitude', 'longitude']

class SEData():
    def __init__(self):
        # Check if pickle data is created or not
        if os.path.exists(DATA_PATH):
            self.data = pd.read_pickle(DATA_PATH)
        else:
            self.data = pd.read_table(ALL_DATA_PATH, delimiter='\t', index_col=0, names=ALL_HEADER_NAMES)
            self.data = self.data[KEEP_HEADER_NAMES]
            self.data.to_pickle(DATA_PATH)

    def get_names(self):
        return self.data['name']

    def search_names(self, name, max_returns):
        return process.extract(name, self.data['name'], limit=max_returns, scorer=fuzz.token_sort_ratio)
