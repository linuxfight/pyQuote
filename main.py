from os.path import exists
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultCachedSticker
import requests, uuid, simplejson
from aiogram.types.message import ContentType

def GetToken():
    return str(open("token.txt").read()).strip()

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
            return Load()

def Save(self):
    data = {
        'Quotes': self['Quotes'],
        'nextQuoteId': self['nextQuoteId']
    }
    open("save.json", 'w').write(simplejson.dumps(data))

bot = Bot(token=GetToken())
dp = Dispatcher(bot)
storage = Load()

def ConvertMessage(message : types.Message):
    result = {
        'from': {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username
        },
        'text': message.text,
        'reply_to_message': None,
        'media': None
    }
    if message.reply_to_message:
        result['reply_to_message'] = ConvertMessage(message.reply_to_message)
    if message.photo:
        result['media'] = {
            'file_id': message.photo[0].file_id,
            'type': "photo"
        }
        if message.caption:
            result['text'] = message.caption
    if message.sticker:
        result['media'] = {
            'file_id': message.sticker.file_id,
            'type': "sticker"
        }
    return result

def GetText(message: types.Message):
    msg = message.text

    if message.caption:
        msg = message.caption

    if message.sticker:
        msg = message.sticker.emoji

    return msg

def GenerateKeyboard(quote):
        buttons = InlineKeyboardMarkup(row_width=2)
        buttons.insert(InlineKeyboardButton(text="👍" + str(len(quote['likes'])), callback_data=str(quote['Id']) + ":like"))
        buttons.insert(InlineKeyboardButton(text="👎" + str(len(quote['dislikes'])), callback_data=str(quote['Id']) + ":dislike"))

        return buttons

def SetLike(userId, quote):
    if userId in quote['dislikes']:
        quote['dislikes'].remove(userId)

    if userId not in quote['likes']:
        quote['likes'].append(userId)

def SetDislike(userId, quote):
    if userId in quote['likes']:
        quote['likes'].remove(userId)

    if userId not in quote['dislikes']:
        quote['dislikes'].append(userId)

def RemoveReactions(userId, quote):
    if userId in quote['likes']:
        quote['likes'].remove(userId)

    if userId in quote['dislikes']:
        quote['dislikes'].remove(userId)

def GetReaction(userId, quote):
    if userId in quote['likes']:
        return "like"
    elif userId in quote['dislikes']:
        return "dislike"
    else:
        return "none"

async def CreateQuote(message : types.Message):
    requestObject = {
        'bot_token': GetToken(),
        'messages': [ConvertMessage(message)]
    }
    quote = {
        'Id': storage['nextQuoteId'],
        'text': GetText(message),
        'fileId': "",
        'likes': [],
        'dislikes': []
    }
    response = requests.post(url="https://quotes.vanutp.dev/generate", json=requestObject)
    storage['nextQuoteId'] += 1
    storage['Quotes'].append(quote)
    sent_message = await bot.send_sticker(chat_id=message.chat.id, sticker=response.content, reply_to_message_id=message.message_id, reply_markup=GenerateKeyboard(quote))
    quote['fileId'] = sent_message.sticker.file_id
    Save(storage)

@dp.message_handler(content_types=ContentType.TEXT)
async def GenerateMessageQuote(message):
    await CreateQuote(message)

@dp.message_handler(content_types=ContentType.STICKER)
async def GenerateStickerQuote(sticker):
    await CreateQuote(sticker)

@dp.message_handler(content_types=ContentType.PHOTO)
async def GeneratePhotoQuote(photo):
    await CreateQuote(photo)

def GetQuote(quoteId):
    for quoteFor in storage['Quotes']:
        if str(quoteFor['Id']) == quoteId:
            return quoteFor

@dp.callback_query_handler()
async def OnButtonClick(callbackQuery: types.CallbackQuery):
    data = callbackQuery.data.split(':')
    userId = callbackQuery.from_user.id
    quoteId = data[0]
    reaction = data[1]
    quote = GetQuote(quoteId)

    if reaction == GetReaction(userId, quote):
        RemoveReactions(userId, quote)
        await bot.answer_callback_query(
            callback_query_id=callbackQuery.id,
            text="Вы убрали реакцию"
        )
    elif reaction == "like":
        SetLike(userId, quote)
        await bot.answer_callback_query(
            callback_query_id=callbackQuery.id,
            text="Вы поставили лайк"
        )
    elif reaction == "dislike":
        SetDislike(userId, quote)
        await bot.answer_callback_query(
            callback_query_id=callbackQuery.id,
            text="Вы поставили дизлайк"
        )

    if callbackQuery.message:
        await bot.edit_message_reply_markup(
            chat_id=callbackQuery.message.chat.id,
            message_id=callbackQuery.message.message_id,
            reply_markup=GenerateKeyboard(quote)
        )
    else:
        await bot.edit_message_reply_markup(
            inline_message_id=callbackQuery.inline_message_id,
            reply_markup=GenerateKeyboard(quote)
        )

    Save(storage)

@dp.inline_handler()
async def OnInlineQuery(inlineQuery: types.InlineQuery):
    quotes = []
    userId = inlineQuery.from_user.id
    for quote in storage['Quotes']:
        if ((userId in quote['likes'] or userId in quote['dislikes']) and inlineQuery.query != None and quote['text'] != None and inlineQuery.query.lower() in quote['text'].lower()):
            quotes.append(quote)

    answers = []

    for quote in quotes:
        randomId = str(uuid.uuid4())
        answers.append(InlineQueryResultCachedSticker(id=randomId, sticker_file_id=quote['fileId'], reply_markup=GenerateKeyboard(quote)))

    await bot.answer_inline_query(
        inline_query_id=inlineQuery.id,
        results=answers,
        cache_time=0
    )

if __name__ == '__main__':
    try:
        print("Bot is running")
        executor.start_polling(dp)
    except KeyboardInterrupt:
        pass