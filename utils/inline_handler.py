from utils.keyboard import generate_keyboard
from utils.storage import load
from uuid import uuid4
from pyrogram.types import InlineQueryResultCachedSticker


async def on_inline_query(client, inline_query):
    storage = load()
    quotes = []
    user_id = inline_query.from_user.id
    for quote in storage['Quotes']:
        if (user_id in quote['likes'] or user_id in quote['dislikes']) and inline_query.query is not None and\
                quote['text'] is not None and inline_query.query.lower() in quote['text'].lower():
            quotes.append(quote)

    answers = []

    for quote in quotes:
        random_id = str(uuid4())
        answers.append(InlineQueryResultCachedSticker(id=random_id, sticker_file_id=quote['fileId'],
                                                      reply_markup=generate_keyboard(quote)))

    await client.answer_inline_query(
        inline_query_id=inline_query.id,
        results=answers,
        cache_time=0
    )
