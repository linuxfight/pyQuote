import asyncio
import httpx
import aiofiles
import json
import uuid
import tempfile


from os.path import exists
from pathlib import Path
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultCachedSticker, InlineQuery, CallbackQuery, Message


def config(key):
    if exists("config.json"):
        data = json.loads(open("config.json", 'r').read())
        return str(data[key])
    else:
        data = {
            'emoji_library': 'twemoji',
            'background_color': '#1b1429',
            'bot_token': 'BOT_TOKEN',
            'api_hash': 'API_HASH',
            'api_id': 'API_ID',
            'url': "https://quotes.vanutp.dev/generate"
        }
        open("config.json", 'w').write(json.dumps(data))
        quit(0)


def load():
    if exists("save.json"):
        data = open("save.json", 'r').read()
        return json.loads(data)
    else:
        data = {
            'Quotes': [],
            'nextQuoteId': 0
        }
        open("save.json", 'w').write(json.dumps(data))
        return load()


async def save(self):
    data = {
        'Quotes': self['Quotes'],
        'nextQuoteId': self['nextQuoteId']
    }
    async with aiofiles.open("save.json", 'w') as file:
        await file.write(json.dumps(data))
    quote_id = data['nextQuoteId'] - 1


def login():
    if exists("pyQuote_bot.session"):
        return Client("pyQuote_bot")
    return Client(
        "pyQuote_bot",
        api_id=config('api_id'),
        api_hash=config('api_hash'),
        bot_token=config('bot_token')
    )


app = login()
storage = load()
emoji_library = config('emoji_library')
background_color = config('background_color')
url = config('url')


def convert_entities(entities):
    result = []
    for entity in entities:
        entity_name = str(entity.type.name).lower()
        converted_entity = {
            "offset": entity.offset,
            "length": entity.length,
            "type": entity_name
        }
        if entity_name == "custom_emoji":
            converted_entity["custom_emoji_id"] = str(entity.custom_emoji_id)
        result.append(converted_entity)
    return result


def convert_message(message: Message, value: bool):
    if value is False:
        if not message.sticker and message.caption:
            message.text = get_text(message, value)
    result = {
        'from': get_from(message),
        'text': message.text,
        'entities': None,
        'reply_to_message': None,
        'media': get_media(message)
    }
    if message.entities:
        result['entities'] = convert_entities(message.entities)
    if message.reply_to_message:
        reply = message.reply_to_message
        reply.text = get_text(message.reply_to_message, True)
        result['reply_to_message'] = convert_message(reply, True)
    return result


def get_from(message: Message):
    result = None
    if message.from_user:
        result = {
            'id': message.from_user.id,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username
        }
    if message.forward_from_chat:
        result = {
            'id': message.forward_from_chat.id,
            'name': message.forward_from_chat.title,
            'username': message.forward_from_chat.username
        }
    if message.forward_from or message.forward_sender_name or message.forward_from_chat:
        if message.forward_from_chat:
            result = {
                'id': message.forward_from_chat.id,
                'name': message.forward_from_chat.title,
                'username': message.forward_from_chat.username
            }
        elif message.forward_sender_name:
            result = {
                'id': message.forward_sender_name.__hash__(),
                'name': message.forward_sender_name,
                'username': "HiddenSender"
            }
        else:
            result = {
                'id': message.forward_from.id,
                'first_name': message.forward_from.first_name,
                'last_name': message.forward_from.last_name,
                'username': message.forward_from.username
            }
    return result


def get_media(message: Message):
    media = None
    if message.photo:
        media = {
            'file_id': message.photo.file_id,
            'type': "photo"
        }
    if message.sticker:
        media = {
            'file_id': message.sticker.file_id,
            'type': "sticker"
        }
    return media


def get_text(message: Message, is_reply: bool):
    msg = message.text

    if message.photo:
        if message.caption:
            if is_reply:
                msg = "🖼️ " + message.caption
            else:
                msg = message.caption
        else:
            msg = "🖼️"

    if message.sticker:
        if message.sticker.emoji:
            if is_reply:
                msg = "Стикер " + message.sticker.emoji
            else:
                msg = message.sticker.emoji
        else:
            msg = "Стикер"

    return msg


def generate_keyboard(quote):
    buttons = [[
        InlineKeyboardButton(
            text="👍" + str(len(quote['likes'])),
            callback_data=str(quote['Id']) + ":like"
        ),
        InlineKeyboardButton(
            text="👎" + str(len(quote['dislikes'])),
            callback_data=str(quote['Id']) + ":dislike"
        )]]
    return InlineKeyboardMarkup(
        buttons
    )


def set_like(user_id, quote):
    if user_id in quote['dislikes']:
        quote['dislikes'].remove(user_id)

    if user_id not in quote['likes']:
        quote['likes'].append(user_id)


def set_dislike(user_id, quote):
    if user_id in quote['likes']:
        quote['likes'].remove(user_id)

    if user_id not in quote['dislikes']:
        quote['dislikes'].append(user_id)


def remove_reactions(user_id, quote):
    if user_id in quote['likes']:
        quote['likes'].remove(user_id)

    if user_id in quote['dislikes']:
        quote['dislikes'].remove(user_id)


def get_reaction(user_id, quote):
    if user_id in quote['likes']:
        return "like"
    elif user_id in quote['dislikes']:
        return "dislike"
    else:
        return "none"


def get_args(text: str):
    args = {
        'color': config('background_color'),
        'messages': 1,
        'reply': False,
        'png': False,
        'img': False,
        'rate': False
    }
    data = text.split()
    for argument in data:
        if argument.isnumeric():
            if 1 < int(argument) < 6:
                args['messages'] = int(argument)
        if argument == "reply":
            args['reply'] = True
        if argument == "rate":
            args['rate'] = True
        if argument == "png":
            args['png'] = True
        if argument == "img":
            args['img'] = True
    return args


async def send_request(data, method):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            url=url,
            json=data,
            method=method
        )
        while response.status_code == 429:
            await asyncio.sleep(int(response.headers['retry-after']))
            response = await client.request(
                url=url,
                json=data,
                method=method
            )
        return response


async def create_quote(message: Message, args):
    if not message.reply_to_message:
        await app.send_message(
            chat_id=message.chat.id,
            text="Команду необходимо писать в ответ на сообщение",
            reply_to_message_id=message.id
        )
        return
    request_object = {
        'bot_token': config('bot_token'),
        'emoji_library': emoji_library,
        'background_color': background_color,
        'messages': [convert_message(message.reply_to_message, False)]
    }
    if args['reply']:
        request_object['messages'] = [
            convert_message(message.reply_to_message.reply_to_message, False),
            convert_message(message.reply_to_message, False)
        ]
    if args['messages'] != 1:
        num = message.reply_to_message.id
        messages = []
        while num != message.reply_to_message.id - args['messages']:
            messages.append(num)
            num -= 1
        result = await app.get_messages(chat_id=message.reply_to_message.chat.id, message_ids=messages, replies=-1)
        request_object['messages'] = []
        num = args['messages']
        while num != 0:
            request_object['messages'].append(convert_message(result[num - 1], False))
            num -= 1
    quote = {
        'Id': storage['nextQuoteId'],
        'text': get_text(message.reply_to_message, False),
        'fileId': "",
        'likes': [],
        'dislikes': []
    }
    quote_id = storage['nextQuoteId']
    response = await send_request(data=request_object, method="POST")
    with tempfile.TemporaryDirectory() as tmp:
        filename = Path(tmp) / 'quote.webp'

        async with aiofiles.open(filename, 'wb') as quote_file:
            await quote_file.write(response.content)

            await app.send_chat_action(
                chat_id=message.chat.id,
                action=enums.ChatAction.CHOOSE_STICKER
            )

            sent_message = await app.send_sticker(
                chat_id=message.chat.id,
                sticker=str(filename),
                reply_to_message_id=message.id,
                reply_markup=generate_keyboard(quote)
            )
    quote['fileId'] = sent_message.sticker.file_id
    storage['nextQuoteId'] += 1
    storage['Quotes'].append(quote)
    await save(storage)


@app.on_message(filters.command(["q"]))
async def message_handler(client, message: Message):
    await create_quote(message=message, args=get_args(message.text))


def get_quote(quote_id):
    for quoteFor in storage['Quotes']:
        if str(quoteFor['Id']) == quote_id:
            return quoteFor


@app.on_callback_query()
async def on_button_click(client, callback_query: CallbackQuery):
    data = callback_query.data.split(':')
    user_id = callback_query.from_user.id
    quote_id = data[0]
    reaction = data[1]
    quote = get_quote(quote_id)

    if reaction == get_reaction(user_id, quote):
        remove_reactions(user_id, quote)
        await app.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы убрали реакцию"
        )
    elif reaction == "like":
        set_like(user_id, quote)
        await app.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы поставили лайк"
        )
    elif reaction == "dislike":
        set_dislike(user_id, quote)
        await app.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы поставили дизлайк"
        )

    if callback_query.message:
        await app.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            reply_markup=generate_keyboard(quote)
        )
    else:
        await callback_query.edit_message_reply_markup(
            reply_markup=generate_keyboard(quote)
        )

    await save(storage)


@app.on_inline_query()
async def on_inline_query(client, inline_query: InlineQuery):
    quotes = []
    user_id = inline_query.from_user.id
    for quote in storage['Quotes']:
        if (user_id in quote['likes'] or user_id in quote['dislikes']) and inline_query.query is not None and\
                quote['text'] is not None and inline_query.query.lower() in quote['text'].lower():
            quotes.append(quote)

    answers = []

    for quote in quotes:
        random_id = str(uuid.uuid4())
        answers.append(InlineQueryResultCachedSticker(id=random_id, sticker_file_id=quote['fileId'],
                                                      reply_markup=generate_keyboard(quote)))

    await app.answer_inline_query(
        inline_query_id=inline_query.id,
        results=answers,
        cache_time=0
    )


if __name__ == '__main__':
    try:
        print("Bot is running")
        app.run()
    except KeyboardInterrupt:
        app.stop()
        pass
