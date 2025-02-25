import requests
import json
from typing import Dict

class TelegramClient:
    """
    텔레그램 bot 대화방에 메시지를 발송한다.
    
    Alias: telegram_client
    """
    def __init__(self, **kwargs):
        self.token = kwargs["token"]
        self.chat_id = kwargs["chat_id"]
    
    def send_message(self, message):
        """
        ⭕️ 메시지를 텔레그램으로 발송한다.

        Args:
            message : 발송하려는 메시지
        """
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
        }
        response = requests.post(url, data=payload)
        return response.json()

    def send_message_with_log(self, message):
        """
        ⭕️ 메시지를 텔레그램으로 발송 및 출력한다.

        Args:
            message : 발송하려는 메시지
        """
        self.send_message(message)
        print(message)

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.abspath("../../../"))
    import SystemConfig

    api_file_path = SystemConfig.Path.telegram
    telegram = TelegramClient(api_file_path)

    message = (f" 🚀 프로그램 시작\n"
               f"   💻 오류발생")
    telegram.send_message(message)
    telegram.send_message_with_log(message)