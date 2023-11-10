import json
from dataclasses import dataclass
from typing import Any

import requests

HEADERS = {"Accept": "application/json", "Encoding": "UTF-8"}


@dataclass
class GenerationChoiceResponse:
    messages: list
    answer_id: str

    def __init__(self, messages, answer_id):
        super().__init__()
        self.messages = messages
        self.answer_id = answer_id


class ChatBotAPI:
    """Class using to interact with chatbot API."""

    def __init__(self, api_path: str):
        self.api_path = api_path
        self.timeout = 60 * 3

    def create_user(self, telegram_user_id: str, username: str, chat_id: str):
        """Create new user
        Args:
            telegram_user_id: user id
            username: telegram username
            chat_id: unique chat id
        """
        path = f"{self.api_path}/users"
        answer = requests.post(
            path,
            json={"username": username, "user_id": telegram_user_id, "chat_id": chat_id},
            headers=HEADERS,
            timeout=self.timeout,
        )
        return json.dumps(answer.json(), ensure_ascii=False)

    def get_user(self, telegram_user_id: str) -> Any:
        """Return user entity :param telegram_user_id:

        :ctx update:
        """
        path = f"{self.api_path}/users/{telegram_user_id}"
        answer = requests.get(path, headers=HEADERS, timeout=self.timeout)
        return answer.json()

    def add_message(self, telegram_user_id: str, text: str):
        """Clear history command handler.

        Send to chat api request to generate answer based on conversation
        Args:
            telegram_user_id: id of user in telegram
            text: user message
        """
        path = f"{self.api_path}/users/{telegram_user_id}/context/generate"
        answer = requests.patch(
            path,
            headers=HEADERS,
            timeout=self.timeout,
            json={
                "text": text,
            },
        )
        if answer.status_code == 500:
            return None
        print(answer.json())
        return GenerationChoiceResponse(**answer.json())

    def remove_user(self, telegram_user_id: str):
        """
        Remove user from database by telegram id
        Args:
            telegram_user_id: id of user in telegram
        """
        path = f"{self.api_path}/dialog/{telegram_user_id}"
        answer = requests.delete(path, headers=HEADERS, timeout=self.timeout)
        return json.dumps(answer.json(), ensure_ascii=False)

    def clear_history(self, telegram_user_id: str):
        """Clear user message history.

        Args:
            telegram_user_id: id of user in telegram
        """
        path = f"{self.api_path}/users/{telegram_user_id}/context"
        answer = requests.delete(path, headers=HEADERS, timeout=self.timeout)
        return json.dumps(answer.json(), ensure_ascii=False)

    def update_possible_context_id(
        self, telegram_user_id: str, answer_id: str, possible_contexts_ids: list[str]
    ):
        """Update possible context id in message.

        Args:
            telegram_user_id: id of user in telegram
            possible_contexts_ids: possible message id that user will choose
            answer_id: database id on answer
        """

        path = (
            f"{self.api_path}/users/{telegram_user_id}/context/{answer_id}/possible_contexts_ids"
        )
        answer = requests.post(
            path,
            json={"possible_contexts_ids": possible_contexts_ids},
            headers=HEADERS,
            timeout=self.timeout,
        )
        return json.dumps(answer.json(), ensure_ascii=False)

    def update_user_choice(self, telegram_user_id: str, answer_id: str, message_id: str):
        """Update possible context id in message.

        Args:
            telegram_user_id: id of user in telegram
            message_id: message id to update
            answer_id: id of answer
        """

        path = f"{self.api_path}/users/{telegram_user_id}/context/{answer_id}/user_choice"
        answer = requests.post(
            path, json={"message_id": message_id}, headers=HEADERS, timeout=self.timeout
        ).json()
        return answer["text"]

    def update_user_custom_choice(self, telegram_user_id: str, message_id: str, custom_text: str):
        """Update possible context id in message.

        Args:
            telegram_user_id: id of user in telegram
            message_id: id of message you want to improve
            custom_text: replace bad message with your text
        """

        path = f"{self.api_path}/users/{telegram_user_id}/context/messages/custom_answer"
        answer = requests.post(
            path,
            json={"message_id": message_id, "custom_text": custom_text},
            headers=HEADERS,
            timeout=self.timeout,
        )
        return json.dumps(answer.json(), ensure_ascii=False)
