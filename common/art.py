import os

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'art')

def art_folder(name):
    return lambda filename: os.path.join(ART_DIR, name, filename)
