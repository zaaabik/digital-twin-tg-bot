import json
from typing import Any

import requests

HEADERS = {"Accept": "application/json"}


class ChatBotAPI:
    """Class using to interact with chatbot API."""

    def __init__(self, api_path: str):
        self.api_path = api_path
        self.timeout = 60 * 3

    def get_user(self, telegram_user_id: str) -> Any:
        """Return user entity :param telegram_user_id:

        :ctx update:
        """
        path = f"{self.api_path}/dialog/{telegram_user_id}"
        answer = requests.get(path, headers=HEADERS, timeout=self.timeout)
        return json.dumps(answer.json(), ensure_ascii=False)

    def add_message(self, telegram_user_id: str, username: str, text: str):
        """Clear history command handler.

        Send to chat api request to remove user message history
        Args:
            telegram_user_id: id of user in telegram
            username: telegram username
            text: user message
        """
        path = f"{self.api_path}/dialog/{telegram_user_id}"
        answer = requests.patch(
            path,
            headers=HEADERS,
            timeout=self.timeout,
            json={
                "username": username,
                "text": text,
            },
        )
        return answer.json()

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
        path = f"{self.api_path}/dialog/{telegram_user_id}/context"
        answer = requests.delete(path, headers=HEADERS, timeout=self.timeout)
        return json.dumps(answer.json(), ensure_ascii=False)
