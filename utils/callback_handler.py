from utils.storage import save, load
from utils.keyboard import generate_keyboard


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


def get_quote(quote_id, storage):
    quotes = storage['Quotes']
    for quote in quotes:
        if str(quote['Id']) == quote_id:
            return quote


async def on_button_click(client, callback_query):
    storage = load()
    data = callback_query.data.split(':')
    user_id = callback_query.from_user.id
    quote_id = data[0]
    reaction = data[1]
    quote = get_quote(quote_id, storage)

    if reaction == get_reaction(user_id, quote):
        remove_reactions(user_id, quote)
        await client.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы убрали реакцию"
        )
    elif reaction == "like":
        set_like(user_id, quote)
        await client.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы поставили лайк"
        )
    elif reaction == "dislike":
        set_dislike(user_id, quote)
        await client.answer_callback_query(
            callback_query_id=callback_query.id,
            text="Вы поставили дизлайк"
        )

    if callback_query.message:
        await client.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            reply_markup=generate_keyboard(quote)
        )
    else:
        await callback_query.edit_message_reply_markup(
            reply_markup=generate_keyboard(quote)
        )

    await save(storage)
