from utils.login import login
from utils.message_handler import start_handler, quote_handler
from utils.callback_handler import on_button_click
from utils.inline_handler import on_inline_query
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, InlineQueryHandler
from pyrogram import filters


app = login()


app.add_handler(MessageHandler(start_handler, filters.command('start')))
app.add_handler(MessageHandler(quote_handler, filters.command('q')))
app.add_handler(CallbackQueryHandler(on_button_click))
app.add_handler(InlineQueryHandler(on_inline_query))


if __name__ == '__main__':
    try:
        print("Bot is running")
        app.run()
    except KeyboardInterrupt:
        app.stop()
        pass
