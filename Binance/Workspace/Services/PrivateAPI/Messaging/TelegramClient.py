import requests
import json
from typing import Dict

class TelegramClient:
    """
    텔레그램 bot 대화방에 메시지를 발송한다.
    
    Alias: telegram_client
    """
    def __init__(self, api_file_path:str):
        self.api_key:Dict = self._load_api_keys(api_file_path)
    
    def _load_api_keys(self, api_file_path: str) -> Dict[str, str]:
        """
        ⭕️ token값과 chat_id값이 저장된 파일을 불러온다.

        Args:
            api_file_path (str): 파일 주소

        Raises:
            KeyError: 불러온 파일안에 "token"과 "chat_id"가 없음
            FileNotFoundError: 파일 주소에 파일이 존재하지 않음
            ValueError: 파일 형태에 문제가 있음.

        Returns:
            Dict[str, str]: _description_
        """
        try:
            with open(api_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if "chat_id" not in data or "token" not in data:
                raise KeyError("JSON 파일에 'chat_id' 또는 'token' 키가 없습니다.")

            return data

        except FileNotFoundError:
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {api_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"올바른 JSON 형식이 아닙니다: {api_file_path}")
    
    def send_message(self, message):
        """
        ⭕️ 메시지를 텔레그램으로 발송한다.

        Args:
            message : 발송하려는 메시지
        """
        url = f"https://api.telegram.org/bot{self.api_key["token"]}/sendMessage"
        payload = {
            "chat_id": self.api_key["chat_id"],
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