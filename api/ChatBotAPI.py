import json
import requests

HEADERS = {'Accept': 'application/json'}


class ChatBotAPI:
    def __init__(self, api_path: str):
        self.api_path = api_path

    def get_user(self, telegram_user_id: str):
        path = f'{self.api_path}/dialog/{telegram_user_id}'
        answer = requests.get(
            path, headers=HEADERS
        )
        return json.dumps(answer.json(), ensure_ascii=False)

    def add_message(self, telegram_user_id: str, text: str):
        path = f'{self.api_path}/dialog/{telegram_user_id}?text={text}'
        answer = requests.patch(
            path, headers=HEADERS
        )
        return answer.json()

    def remove_user(self, telegram_user_id: str):
        path = f'{self.api_path}/dialog/{telegram_user_id}'
        answer = requests.delete(
            path, headers=HEADERS
        )
        return json.dumps(answer.json(), ensure_ascii=False)

    def clear_history(self, telegram_user_id: str):
        path = f'{self.api_path}/dialog/{telegram_user_id}/context'
        answer = requests.delete(
            path, headers=HEADERS
        )
        return json.dumps(answer.json(), ensure_ascii=False)