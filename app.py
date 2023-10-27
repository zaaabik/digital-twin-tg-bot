#  type: ignore

import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
)

from api.ChatBotAPI import ChatBotAPI

api_path = os.environ["CHAT_API_ADDRESS"]
tg_bot_token = os.environ["TG_BOT_TOKEN"]


class TgBot:
    def __init__(self, token: str, chat_bot: ChatBotAPI):
        self.app = ApplicationBuilder().token(token).build()
        self.chat_bot = chat_bot

    async def get_whole_user_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        # pylint: disable=unused-argument
        """Return whole user handler
        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        response = self.chat_bot.get_user(telegram_user_id)
        await update.message.reply_text(response)

    async def remove_user_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        # pylint: disable=unused-argument
        """Handler for removing user whole entity via chatbot service.

        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        response = self.chat_bot.remove_user(telegram_user_id)
        await update.message.reply_text(response)

    async def message_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        """Any message handler, send request to chatbot to generate answer using LLM
        update:

        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        user_name = str(update.effective_user.username)
        text = str(update.message.text)
        response = self.chat_bot.add_message(telegram_user_id, user_name, text)
        text_answer = response["bot_answer"]["context"]
        await update.message.reply_text(text_answer)
        await ctx.bot.send_chat_action(chat_id=ctx._chat_id, action="typing")

    async def clear_history_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        # pylint: disable=unused-argument
        """Clear history command handler.

        Send to chat api request to remove user message history
        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        response = self.chat_bot.clear_history(telegram_user_id)
        await update.message.reply_text(response)

    def run(self):
        """Run bot."""
        self.app.add_handler(CommandHandler(command="get", callback=self.get_whole_user_handler))
        # self.app.add_handler(CommandHandler(
        #     command='remove',
        #     callback=self.remove_user_handler
        # ))
        self.app.add_handler(CommandHandler(command="clear", callback=self.clear_history_handler))
        self.app.add_handler(MessageHandler(filters=None, callback=self.message_handler))
        self.app.run_polling()


chat_bot_api = ChatBotAPI(api_path=api_path)
bot = TgBot(tg_bot_token, chat_bot_api)
bot.run()
