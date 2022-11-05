from os.path import exists
from json import loads, dumps
import aiofiles


def load():
    if exists("save.json"):
        data = open("save.json", 'r').read()
        return loads(data)
    else:
        data = {
            'Quotes': [],
            'nextQuoteId': 0
        }
        open("save.json", 'w').write(dumps(data))
        return load()


async def save(self):
    data = {
        'Quotes': self['Quotes'],
        'nextQuoteId': self['nextQuoteId']
    }
    async with aiofiles.open("save.json", 'w') as file:
        await file.write(dumps(data))
