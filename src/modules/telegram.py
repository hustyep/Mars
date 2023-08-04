import telegram

bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
chat_id = '805381440'
bot = telegram.Bot(token=bot_token)
bot.send_message(chat_id=chat_id, text='Hello, World!')