from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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