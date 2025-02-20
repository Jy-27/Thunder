
import requests
import websocket
import json
import threading
import time

# 🔹 바이낸스 선물 API 정보
FUTURES_API_URL = "https://fapi.binance.com"
API_KEY = 
HEADERS = {"X-MBX-APIKEY": API_KEY}

class BinanceFuturesWebSocket:
    def __init__(self):
        self.listen_key = None
        self.ws = None
        self.running = True  # WebSocket 실행 상태
        self.lock = threading.Lock()

    def get_listen_key(self):
        """
        🔹 Listen Key를 생성하여 반환 (선물 계정용)
        """
        response = requests.post(f"{FUTURES_API_URL}/fapi/v1/listenKey", headers=HEADERS)
        self.listen_key = response.json().get("listenKey")
        if not self.listen_key:
            print("❌ Listen Key 생성 실패")
        else:
            print(f"✅ Listen Key 발급 완료: {self.listen_key}")

    def refresh_listen_key(self):
        """
        🔹 Listen Key를 30분마다 갱신하여 만료되지 않도록 유지
        """
        while self.running:
            time.sleep(1800)  # 30분마다 갱신
            response = requests.put(f"{FUTURES_API_URL}/fapi/v1/listenKey", headers=HEADERS)
            if response.status_code == 200:
                print("🔄 Listen Key 갱신 완료")
            else:
                print("⚠️ Listen Key 갱신 실패, WebSocket 재연결 필요")
                self.reconnect()

    def on_message(self, ws, message):
        """
        🔹 WebSocket 메시지 수신 핸들러 (체결 정보 출력)
        """
        data = json.loads(message)
        print(f"📩 수신 데이터: {data}")

        if data.get("e") == "executionReport":
            print(f"✅ 체결 정보 수신: {data}")

    def on_error(self, ws, error):
        """
        🔹 WebSocket 오류 핸들러
        """
        print(f"❌ WebSocket 에러 발생: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """
        🔹 WebSocket 종료 핸들러 (자동 재연결)
        """
        print("🔴 WebSocket 연결 종료됨, 재연결 시도...")
        self.reconnect()

    def on_open(self, ws):
        """
        🔹 WebSocket 연결 성공 시 실행
        """
        print("🟢 WebSocket 연결 성공")

    def start_websocket(self):
        """
        🔹 WebSocket을 시작하고 실행 유지
        """
        with self.lock:  # 스레드 안전성 확보
            if not self.listen_key:
                self.get_listen_key()
            ws_url = f"wss://fstream.binance.com/ws/{self.listen_key}"
            print(f"🛠️ WebSocket 연결 중: {ws_url}")

            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            self.ws.on_open = self.on_open
            self.ws.run_forever()

    def reconnect(self):
        """
        🔹 WebSocket 재연결 로직
        """
        with self.lock:
            if self.ws:
                self.ws.close()
            self.get_listen_key()
            self.start_websocket()

    def run(self):
        """
        🔹 WebSocket 및 Listen Key 자동 갱신을 병렬 실행
        """
        # Listen Key 갱신 스레드 실행
        threading.Thread(target=self.refresh_listen_key, daemon=True).start()

        # WebSocket 실행
        self.start_websocket()

if __name__ == "__main__":
    """
    🔹 메인 실행부
    """
    binance_ws = BinanceFuturesWebSocket()
    binance_ws.run()
