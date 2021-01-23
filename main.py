import os
import random
import hjson
import sys
sys.path.append('src')
from gui import randomize

def main(settings):
    randomize(settings)
    
if __name__=='__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python main.py settings.json')
    with open(sys.argv[1], 'r') as file:
        settings = hjson.load(file)
    main(settings)
