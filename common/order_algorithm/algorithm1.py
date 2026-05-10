import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from common.auto_trade import AutoTrade

@dataclass
class Algo1_info:

    ticker: str
    time_usa: str
    time_korea: str
    candle_count: int
    candle_unit: int

    @classmethod
    def from_json(cls, filepath: Path) -> "Algo1_info":
        data: dict[str, Any] = json.loads(filepath.read_text(encoding='utf-8'))
        return cls(**data)

class Algorithm1:
    def __init__(self, object: AutoTrade):
        self.o = object
        self.logger = self.o.logger
        self.last_trade_time = datetime.now() + timedelta(days=-1)
        self.win = 0
        self.lose = 0
        self.total_profit = 0

        # price levels
        self.high_price = 0
        self.low_price = 0
        self.cut_losses = 0
        self.take_profit = 0

    def run(self):
        while True:
            # 하루 한번만 거래
            if self.last_trade_time.date() <= datetime.now().date() and self.o.is_start():
                self.last_trade_time = datetime.now()
                start_balance = self.o._get_balance(self.o.quote_currency)

                self.logger.info(f"{self.o.platform} Algorithm1 거래 시작.")
                self.logger.info(f"시작 잔고: {start_balance}")
                self.trade()
                self.logger.info(f"{self.o.platform} Algorithm1 거래 종료.")

                end_balance = self.o._get_balance(self.o.quote_currency)
                self.logger.info(f"종료 잔고: {end_balance}")
                self.logger.info(f"수익: {end_balance - start_balance}")
                self.total_profit += end_balance - start_balance
                self.logger.info(f"총 수익: {self.total_profit}")

                win_rate = 0
                if self.win != 0 or self.lose != 0:
                    win_rate = self.win / (self.win + self.lose) * 100
                self.logger.info(f"win: {self.win}, lose: {self.lose}. 승률: {win_rate}%")

            time.sleep(60)

    def trade(self):
        # 가격 세팅
        price_levels = self.o.get_price_levels_by_minute()
        if not price_levels:
            self.logger.info("가격 세팅 실패. 거래 종료.")
            return
        self.high_price = price_levels[0]
        self.low_price = price_levels[1]
        self.cut_losses = self.o.get_cut_losses(self.high_price, self.low_price)
        self.take_profit = self.o.get_lock_gains(self.high_price, self.low_price)
        self.logger.info(f"high_price: {self.high_price}, low_price: {self.low_price}")
        self.logger.info(f"cut_losses: {self.cut_losses}, take_profit: {self.take_profit}")

        # 매수시점 조회
        current_price = self._poll_price_until_high(self.high_price)
        if current_price == -1:
            self.logger.info("매수시점 조회 실패. 거래 종료.")
            return
        self.logger.info(f"매수시점 가격: {current_price}")

        # 잔고조회
        balance = self.o._get_balance(self.o.quote_currency)

        # 수수료 조회
        # shlee todo

        available_balance = balance
        self.logger.info(f"잔고({self.o.quote_currency}): {balance} -> {available_balance}")

        if available_balance < 5000:
            self.logger.info("잔액 부족. 거래 종료.")
            return

        # 시장가 매수 요청
        bid_uuid = self.o._buy_price(str(available_balance))
        self.logger.info(f"매수요청 - {bid_uuid}")

        # 매수 확인
        # shlee todo 매수 얼마에 체결되었는지도 확인
        # if not self._ensure_buy_or_retry(bid_uuid):
        #     return
        # shlee todo 매수 확인 후 체크하도록.
        # agv_buy_price = self.o._get_agv_price(self.o.trade_currency)
        agv_buy_price = 0
        self.logger.info(f"{self.o.trade_currency} 매수 평단가: {agv_buy_price}")

        # 잔고조회
        btc_balance = self.o._get_balance(self.o.trade_currency)

        # 시장가 매도
        ask_uuid = self.o._sell_price(str(btc_balance))
        self.logger.info(f"매도요청 - {ask_uuid}")
        # shlee todo 여기서 실제 매도 금액을 가져오면 좋을듯. 매수확인과 같은 함수쓰면될듯

    def _poll_price_until_high(self, high: float) -> float:
        """
        현재 가격이 최고가에 도달할 때까지 조회
        """
        current_price = self.o._get_current_price()
        cnt = 0
        while current_price < high:
            time.sleep(1)
            current_price = self.o._get_current_price()

            cnt += 1
            # 300번에 한번씩 로깅
            if cnt >= 300:
                self.logger.info(f"현재가 : {current_price}")
                cnt = 0

            # 설정된 시간내에 매수시점 못 잡을 시 거래 종료(기본 60분)
            trade_duration_min = self.o.algorythm.get("trade_duration_min", 60)
            if self.last_trade_time + timedelta(hours=3) < datetime.now():
                return -1
        return current_price

    def _sell_on_threshold(self) -> None:
        """
        현재가가 self.take_profit 보다 위로 가거나
        현재가가 self.cut_losses보다 아래로 가면 매도
        """
        # shlee todo
        while True:
            current_price = self.o._get_current_price()

            if current_price >= self.take_profit:
                self.o._sell_price(current_price)
                self.win += 1
                break
            elif current_price <= self.cut_losses:
                self.o._sell_price(current_price)
                self.lose += 1
                break

    def _ensure_buy_or_retry(self, order_id: str) -> bool:
        """
        매수요청 확인.
        매수가 되지 않는다면 취소하고 다시 요청.
        """
        # shlee todo
        # 체결되었는지 확인. 체결되었다면 단가 및 수량 확인?
        retry_cnt = 0
        while True:
            retry_cnt += 1
            if retry_cnt > 5:
                self.logger.info(f"재시도 요청 끝. 거래 종료.")
                self.logger.info(f"매수요청({order_id}) 취소.")
                return False

            time.sleep(3)
            # todo 요청확인
            if True:
                break

            self.logger.info(f"매수요청 재시도..{retry_cnt}/5")

            # 요청 취소
            self.logger.info(f"매수요청({order_id}) 취소.")

            # 매수요청
            current_price = 120
            order_id = self.o.buy(current_price)
            self.logger.info(f"매수요청({order_id}): {current_price}")
        return True