from typing import Optional, Dict, List, Any

class AccountBalanceStatus:
    """
    fetch_account_balance함수에서 수신된 정보를 활용하여 계좌 상태를 업데이트한다.

    Returns:
        Dict: 계좌상태를 Dict형태로 전환하여 반환. 
    """
    __slots__ = (
        "feeTier", "canTrade", "canDeposit", "canWithdraw", "feeBurn",
        "tradeGroupId", "updateTime", "multiAssetsMargin", "totalInitialMargin",
        "totalMaintMargin", "totalWalletBalance", "totalUnrealizedProfit",
        "totalMarginBalance", "totalPositionInitialMargin", "totalOpenOrderInitialMargin",
        "totalCrossWalletBalance", "totalCrossUnPnl", "availableBalance", "maxWithdrawAmount"
    )
    
    def __init__(self):
        """초기화: 모든 속성을 None으로 설정"""
        for slot in self.__slots__:
            setattr(self, slot, None)
    
    def set_data(self, **kwargs):
        """
        💾 수신된 데이터를 저장하도록 한다.(덮어쓰기)
        """
        for key, value in kwargs.items():
            if key in self.__slots__:  # 유효한 속성만 업데이트
                setattr(self, key, value)

    def get_data(self) -> Dict[str, Optional[Any]]:
        """
        🔎 저장된 데이터의 전체를 Dict형태로 반환한다.
        """
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def get_selected_data(self, field: str) -> Any:
        """
        🔎 저장된 데이터의 특정 값만 반환한다.

        Args:
            key (str): field명

        Returns:
            Any: field값
        """
        if not hasattr(self, field):
            return ValueError(f"key 입력 오류: {field}")
        return getattr(self, field)
        
    def __repr__(self):
        return str(self.get_data())
