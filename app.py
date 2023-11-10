import os

from api.ChatBotAPI import ChatBotAPI
from tg import TelegramBotApplication

if __name__ == "__main__":
    api_path = os.environ["CHAT_API_ADDRESS"]
    tg_bot_token = os.environ["TG_BOT_TOKEN"]

    chat_bot_api = ChatBotAPI(api_path=api_path)
    bot = TelegramBotApplication(tg_bot_token, chat_bot_api)
    bot.run()
