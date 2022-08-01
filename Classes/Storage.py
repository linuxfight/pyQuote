from os.path import exists
import simplejson

class Storage:
    @staticmethod
    def Load():
        if exists("save.json"):
            data = open("save.json", 'r').read()
            return simplejson.loads(data)
        else:
            data = {
                'Quotes': [],
                'nextQuoteId': 0
            }
            open("save.json", 'w').write(simplejson.dumps(data))
            return Storage().Load()


    @staticmethod
    def Save(self):
        data = {
            'Quotes': self['Quotes'],
            'nextQuoteId': self['nextQuoteId']
        }
        open("save.json", 'w').write(simplejson.dumps(data))
