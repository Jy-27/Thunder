"""코드 hint 제공을 위한 라이브러리"""

from typing import Tuple, List, Optional
import utils

class FunctionGroup:
    """
    Main Class의 복잡성을 감소하기 위하여 내부함수를 별도로 분리하여 관리하기 위한 class
    """
    def __init__(self):
        """
        1. 기능: 클래스 초기화.
        2. 매개변수: 없음.
        3. 반환값: 없음.
        4. 오류 검증 기능: 해당 없음.
        """
        pass

    # KLINE DATA 데이터 유효성을 검토한다.
    def _validate_kline_data(self, value: List) -> bool:
        """
        1. 기능: KLINE DATA의 유효성을 검토하고 결과를 True 또는 False로 반환한다.
        2. 매개변수:
            - value (List): KLINE DATA의 최하위 리스트.
        3. 반환값 (bool):
            - True: 유효한 데이터일 경우.
            - False: 유효하지 않은 데이터일 경우.
        """
        # 예상 데이터 길이 및 타입 정의
        data_length = 12
        integer_indices = [0, 6]  # 정수여야 하는 인덱스

        # 1. 리스트 타입 확인
        if not isinstance(value, list):
            return False

        # 2. 리스트 길이 확인
        if len(value) != data_length:
            return False

        # 3. 정수 요소 확인
        if not all(isinstance(value[i], int) for i in integer_indices):
            return False

        return True

    # KLINE 데이터의 개별 항목에서 OpenTimestamp와 CloseTimestamp를 추출하여 반환한다.
    def __extract_timestamps(self, kline_entry):
        """
        1. 기능: KLINE 데이터의 개별 항목에서 OpenTimestamp와 CloseTimestamp를 추출하여 반환한다.
        2. 매개변수:
            1) kline_entry (List): KLINE 데이터의 개별 항목 리스트.
        3. 반환값 (Tuple):
            1) open_timestamp: 시작 타임스탬프.
            2) close_timestamp: 종료 타임스탬프.
        4. 오류 검증 기능: 해당 없음.
        """
        open_timestamp = kline_entry[0]
        close_timestamp = kline_entry[6]
        return open_timestamp, close_timestamp


    def __find_matching_index(self, interval_data, start_timestamp, end_timestamp):
        """
        1. 기능: 특정 interval 데이터에서 주어진 시작 및 종료 타임스탬프를 포함하는 인덱스를 반환한다.
        2. 매개변수:
            1) interval_data (List[List]): 특정 interval의 KLINE 데이터 리스트.
            2) start_timestamp (int): 시작 타임스탬프.
            3) end_timestamp (int): 종료 타임스탬프.
        3. 반환값 (Optional[int]): 포함되는 interval 데이터의 인덱스. 없을 경우 None 반환.
        4. 오류 검증 기능:
            - 조건을 만족하는 인덱스를 찾지 못할 경우 None 반환.
        """
        return next(
            (
                idx
                for idx, entry in enumerate(interval_data)
                if (
                    start_timestamp >= self.__extract_timestamps(entry)[0]
                    and end_timestamp <= self.__extract_timestamps(entry)[1]
                )
            ),
            None,
        )

    def get_matching_indices(self, kline_data):
        """
        1. 기능: 여러 interval 간 매칭되는 KLINE 데이터의 인덱스를 찾는다.
        2. 매개변수:
            1) kline_data (Dict[str, List]): interval 이름을 키로, KLINE 데이터를 값으로 가지는 딕셔너리.
        3. 반환값 (List[List[int]]): 각 interval에서 매칭된 인덱스 리스트.
        4. 오류 검증 기능:
            - 데이터 간 매칭이 불가능한 경우 해당 데이터는 결과에서 제외.
        """
        # 1. interval 이름 리스트 추출
        interval_names = list(kline_data.keys())

        # 2. 매칭된 인덱스를 저장할 리스트
        matching_indices = []

        # 3. 첫 번째 interval 데이터에 대해 순회
        for base_index, base_entry in enumerate(kline_data[interval_names[0]]):
            # 3.1. 현재 KLINE 항목의 시작 및 종료 타임스탬프 추출
            start_timestamp, end_timestamp = self.__extract_timestamps(base_entry)

            # 3.2. 매칭된 인덱스를 저장할 리스트 초기화
            interval_indices = [base_index]

            # 3.3. 나머지 interval에서 매칭 인덱스를 찾기
            for interval_name in interval_names[1:]:
                interval_data = kline_data.get(interval_name)
                matched_index = self.__find_matching_index(interval_data, start_timestamp, end_timestamp)
                interval_indices.append(matched_index)

            # 3.4. 하나라도 매칭되지 않은 경우 결과에 추가하지 않음
            if None in interval_indices:
                continue

            # 3.5. 매칭된 인덱스를 결과 리스트에 추가
            matching_indices.append(interval_indices)
            utils._std_print(matching_indices[-1])  # 디버깅용 출력

        return matching_indices