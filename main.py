import sys
import hjson
from gui import randomize

def main(settings):
    if not randomize(settings):
        print('Failed!')

if __name__=='__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python main.py settings.json')
    with open(sys.argv[1], 'r') as file:
        settings = hjson.load(file)
    main(settings)
