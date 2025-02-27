from abc import ABC, abstractmethod

class Client(ABC):
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """
        👻 API에 필요한 headers를 생성한다.

        Returns:
            Dict[str, str]: headers값
        """
        pass

    @abstractmethod
    def _sign_params(self, params: Dict) -> Dict:
        """
        👻 API 요청의 매개변수에 서명을 추가한다.

        Args:
            params (Dict): 요청관련 정보

        Returns:
            Dict: 서명추가 params
        """
        pass

    @abstractmethod
    def _send_request(self, method: str, endpoint: str, params: dict) -> dict:
        """
        👻 API 요청 생성 및 서버 전송, 응답 처리한다.

        Args:
            method (str): 수행 작업 지시
            endpoint (str): endpoint 주소
            params (dict): 함수별 수집된 params

        Returns:
            dict: 처리결과 피드백
        """
        pass

    @abstractmethod
    def send_fund_transfer(
        self, amount: float, transfer_type: int, asset: str = "USDT"
    ) -> Dict:
        pass

    # 현물시장, 선물시장 계좌 잔고 조회
    @abstractmethod
    def fetch_account_balance(self) -> Dict:
        """
        🚀 계좌 정보를 수신 및 반환한다.

        Returns:
            Dict: 계좌정보
        """
        pass

    # Ticker의 미체결 주문상태 조회 및 반환
    @abstractmethod
    def fetch_order_status(self, symbol: Optional[str] = None) -> Dict:
        """
        🚀 미체결 주문상태를 조회한다.

        Args:
            symbol (str, optional): 심볼값
        
        Returns:
            _type_: 조회 결과값
        """
        pass

    # Ticker의 전체 주문내역 조회 및 반환
    @abstractmethod
    def fetch_order_history(self, symbol: str, limit: int = 500) -> Dict:
        """
        🚀 전체 주문 내역을 조회한다.(체결, 미체결, 취소 등등)

        Args:
            symbol (str): 심볼값
            limit (int, optional): 검색량 (max 500)

        Returns:
            Dict: 주문내역 결과값
        """
        pass

    # Ticker의 거래내역 조회 및 반환
    @abstractmethod
    def fetch_trade_history(self, symbol: str, limit: int = 500) -> Dict:
        """
        🚀 지정 심볼값의 거래내역을 조회한다.

        Args:
            symbol (str): 심볼값
            limit (int, optional): 검색량 (max 500)

        Returns:
            Dict: 조회 결과
        """
        pass

    # 현재 주문상태를 상세 조회(체결, 미체결 등등...)
    @abstractmethod
    def fetch_order_details(self, symbol: str, order_id: int) -> Dict:
        """
        현재 주문 상태를 상세히 조회한다. (체결, 미체결)

        Args:
            symbol (str): 심볼값
            order_id (int): 주문 ID (fetch_order_history에서 조회)

        Returns:
            Dict: 결과값
        """
        pass

    # 미체결 취소 주문 생성 및 제출
    @abstractmethod
    def send_cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        미체결 주문을 취소한다.

        Args:
            symbol (str): 심볼값
            order_id (int): 주문 ID (fetch_order_history에서 조회)

        Returns:
            Dict: 결과 피드백
        """
        pass