#  type: ignore
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
)

from api.ChatBotAPI import ChatBotAPI
from tg.constants import (
    API_NOT_AVAILABLE,
    HELP_MESSAGE,
    MAX_TEXT_LENGTH,
    NUMBERS,
    WAITING_FOR_RESPONSE,
)


class WaitingMessage:
    """Class to show waiting message while backend in working."""

    wait_message_id = None

    def __init__(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        self.chat_id = update.message.chat_id
        self.ctx = ctx
        self.update = update

    async def wait(self):
        """Show waiting message."""
        wait_message = await self.update.message.reply_text(WAITING_FOR_RESPONSE)
        self.wait_message_id = wait_message.message_id

    async def stop_wait(self):
        """Remove waiting message."""
        await self.ctx.bot.deleteMessage(message_id=self.wait_message_id, chat_id=self.chat_id)


class TgBot:
    def __init__(self, token: str, chat_bot: ChatBotAPI) -> None:
        self.app = ApplicationBuilder().token(token).build()
        self.chat_bot = chat_bot
        self.users = set()

    async def get_whole_user_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        # pylint: disable=unused-argument
        """Return whole user handler
        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        response = self.chat_bot.get_user(telegram_user_id)["context"]
        text = [f"{msg['role']} : {msg['context']}" for msg in response]
        response = "\n".join(text)

        if len(response) > MAX_TEXT_LENGTH:
            for x in range(0, len(response), MAX_TEXT_LENGTH):
                await update.message.reply_text(response[x : x + MAX_TEXT_LENGTH])
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

    def check_user(self, telegram_user_id: str, chat_id: str, username: str):
        if telegram_user_id not in self.users:
            self.chat_bot.create_user(
                chat_id=chat_id, username=username, telegram_user_id=str(telegram_user_id)
            )
            self.users.add(telegram_user_id)

    async def reply_handler(
        self,
        telegram_user_id: str,
        chat_id: str,
        delete_message_id: str,
        edit_message_id: str,
        text: str,
    ) -> None:
        """Handle reply edit model answer.

        Args:
            telegram_user_id: user id
            chat_id: id of chat
            delete_message_id: id of message will delete (user suggestion)
            edit_message_id:  id of message will edit (model answer)
            text: text using to replace model answer
        """

        self.chat_bot.update_user_custom_choice(
            telegram_user_id=telegram_user_id, message_id=edit_message_id, custom_text=text
        )

        await self.app.bot.editMessageText(chat_id=chat_id, message_id=edit_message_id, text=text)

        await self.app.bot.deleteMessage(chat_id=chat_id, message_id=delete_message_id)

    @staticmethod
    async def create_replay_markup(
        possible_contexts_ids: list[int], answer_id: str
    ) -> InlineKeyboardMarkup:
        """Create markup to choose model answer.

        Args:
            possible_contexts_ids: id of model answer messages to choose
            answer_id: id of answer from backend
        """

        buttons = []
        for message_id, number in zip(possible_contexts_ids, NUMBERS):
            callback_data = {
                "ids": [message_id] + list(set(possible_contexts_ids) - {message_id}),
                "db": answer_id,
            }
            button = InlineKeyboardButton(
                number, callback_data=json.dumps(callback_data, separators=(",", ":"))
            )
            buttons.append(button)

        keyboard = [
            buttons,
            [
                InlineKeyboardButton(
                    "💩", callback_data=json.dumps({"ids": possible_contexts_ids, "db": ""})
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        return reply_markup

    async def message_handler(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        """Any message handler, send request to chatbot to generate answer using LLM
        update:

        Args:
            update: bot update class
            ctx: bot context
        """
        telegram_user_id: str = str(update.effective_user.id)
        text = str(update.message.text)
        chat_id = str(update.message.chat_id)

        self.check_user(
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            username=update.effective_user.username,
        )

        if update.message.reply_to_message:
            delete_message_id = str(update.message.message_id)
            edit_message_id = str(update.message.reply_to_message.message_id)
            await self.reply_handler(
                telegram_user_id=telegram_user_id,
                chat_id=chat_id,
                delete_message_id=delete_message_id,
                edit_message_id=edit_message_id,
                text=text,
            )

            return

        wait_message = WaitingMessage(update, ctx)
        await wait_message.wait()

        response = self.chat_bot.add_message(telegram_user_id, text)
        if not response:
            await update.message.reply_text(API_NOT_AVAILABLE)
            return

        answers = response.messages
        answer_id = response.answer_id

        texts = [f"Вариант {number}:\n{answer}" for answer, number in zip(answers, NUMBERS)]

        possible_contexts_ids = []
        for text in texts:
            message = await update.message.reply_text(text)
            possible_contexts_ids.append(message.message_id)

        self.chat_bot.update_possible_context_id(
            telegram_user_id,
            answer_id,
            possible_contexts_ids=[
                str(possible_contexts_id) for possible_contexts_id in possible_contexts_ids
            ],
        )

        reply_markup = await self.create_replay_markup(
            possible_contexts_ids=possible_contexts_ids, answer_id=answer_id
        )
        await update.message.reply_text("Выберайте лучший ответ", reply_markup=reply_markup)
        await wait_message.stop_wait()

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

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()
        query_question_answer = json.loads(query.data)
        keep_id, *remove_ids = query_question_answer["ids"]
        for remove_message_id in remove_ids:
            await context.bot.deleteMessage(
                chat_id=query.message.chat_id, message_id=remove_message_id
            )
        if query_question_answer["db"]:
            text = self.chat_bot.update_user_choice(
                telegram_user_id=str(update.effective_user.id),
                answer_id=query_question_answer["db"],
                message_id=keep_id,
            )
            await context.bot.editMessageText(
                chat_id=update.callback_query.message.chat_id, message_id=keep_id, text=text
            )

        await query.delete_message()

    async def get_help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        # pylint: disable=unused-argument
        """Help message for user.

        Send to chat api request to remove user message history
        Args:
            update: bot update class
            ctx: bot context
        """
        help_msg = HELP_MESSAGE
        self.chat_bot.create_user(
            chat_id=str(update.message.chat_id),
            username=update.effective_user.username,
            telegram_user_id=str(update.effective_user.id),
        )

        await update.message.reply_text(help_msg)

    def run(self):
        """Run bot."""
        self.app.add_handler(CommandHandler(command="start", callback=self.get_help))
        self.app.add_handler(CallbackQueryHandler(self.button))
        self.app.add_handler(CommandHandler(command="help", callback=self.get_help))
        # self.app.add_handler(CommandHandler(command="get", callback=self.get_whole_user_handler))
        self.app.add_handler(CommandHandler(command="clear", callback=self.clear_history_handler))
        self.app.add_handler(MessageHandler(filters=None, callback=self.message_handler))
        self.app.run_polling()
