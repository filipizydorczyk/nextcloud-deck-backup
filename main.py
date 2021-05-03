import json
import os
import sys
from utils import DeckDownloader, DeckSender

FILE_NAME = 'nextcloud-decks.json'

mode = sys.argv[1] if len(sys.argv) > 1 else None
host = sys.argv[2] if len(sys.argv) > 2 else None
username = sys.argv[3] if len(sys.argv) > 3 else None
passwd = sys.argv[4] if len(sys.argv) > 4 else None

urlFrom = os.getenv('NEXTCLOUD_HOST') or host
authFrom = (os.getenv('NEXTCLOUD_USER') or username, os.getenv(
    'NEXTCLOUD_PASSWORD') or passwd)

urlTo = os.getenv('NEXTCLOUD_HOST') or host or 'http://localhost:8080'
authTo = (os.getenv('NEXTCLOUD_USER') or username or 'test', os.getenv(
    'NEXTCLOUD_PASSWORD') or passwd or 'test')

if((mode == 'backup' or mode == None) and (urlFrom != None and authFrom[0] != None and authFrom[0] != None)):
    dd = DeckDownloader(urlFrom, authFrom)

    data = dd.fetchBoards()

    with open(FILE_NAME, 'w') as outfile:
        json.dump(data, outfile, indent=4)

elif(mode == 'send'):
    ds = DeckSender(urlTo, authTo)
    # ds.sendBoard(data)
else:
    raise ValueError('Unknown mode or missing properites.')
