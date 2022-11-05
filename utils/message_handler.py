from utils.keyboard import generate_keyboard
from utils.login import config
from utils.convert import get_text, convert_message
from utils.storage import save, load
from httpx import AsyncClient
from tempfile import TemporaryDirectory
from pathlib import Path
from aiofiles import open
from pyrogram import enums


def get_args(text: str):
    args = {
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


async def start_handler(client, message):
    await client.send_message(
        chat_id=message.chat.id,
        reply_to_message_id=message.id,
        text='Привет, я бот для создания цитат-стикеров из сообщений.\n'
             'Отправь мне сообщение, ответь на него используя /q и я отправлю тебе цитату.'
    )


async def send_request(data, method):
    async with AsyncClient() as client:
        response = await client.request(
            url='https://quotes.vanutp.dev/generate',
            json=data,
            method=method
        )
        while response.status_code == 429:
            await asyncio.sleep(int(response.headers['retry-after']))
            response = await client.request(
                url='https://quotes.vanutp.dev/generate',
                json=data,
                method=method
            )
        return response


async def quote_handler(client, message):
    storage = load()
    args = get_args(message.text)
    if not message.reply_to_message:
        await client.send_message(
            chat_id=message.chat.id,
            text="Команду необходимо писать в ответ на сообщение",
            reply_to_message_id=message.id
        )
        return
    request_object = {
        'bot_token': config('bot_token'),
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
        result = await client.get_messages(chat_id=message.reply_to_message.chat.id, message_ids=messages, replies=-1)
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
    with TemporaryDirectory() as tmp:
        filename = Path(tmp) / 'quote.webp'

        async with open(filename, 'wb') as quote_file:
            await quote_file.write(response.content)

            await client.send_chat_action(
                chat_id=message.chat.id,
                action=enums.ChatAction.CHOOSE_STICKER
            )

            sent_message = await client.send_sticker(
                chat_id=message.chat.id,
                sticker=str(filename),
                reply_to_message_id=message.id,
                reply_markup=generate_keyboard(quote)
            )
    quote['fileId'] = sent_message.sticker.file_id
    storage['nextQuoteId'] += 1
    storage['Quotes'].append(quote)
    await save(storage)
