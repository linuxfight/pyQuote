from pyrogram import Client
from os.path import exists
from json import loads, dumps


def config(key):
    if exists("config.json"):
        data = loads(open("config.json", 'r').read())
        return str(data[key])
    else:
        data = {
            'bot_token': 'BOT_TOKEN',
            'api_hash': 'API_HASH',
            'api_id': 'API_ID'
        }
        open("config.json", 'w').write(dumps(data))
        quit(0)


def login():
    if exists("pyQuote_bot.session"):
        return Client("pyQuote_bot")
    return Client(
        "pyQuote_bot",
        api_id=config('api_id'),
        api_hash=config('api_hash'),
        bot_token=config('bot_token')
    )