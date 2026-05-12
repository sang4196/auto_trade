import math
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from common.auto_trade import AutoTrade

@dataclass
class Config:

    algorythm_type: str
    ticker: str
    target_time: str
    candle_type: str
    candle_count: int
    candle_unit: int
    trade_duration_min: int

    @classmethod
    def from_json(cls, data: Optional[dict]) -> Optional["Config"]:
        if data is None:
            return None
        return cls(**data)

class Algorithm1:
    def __init__(self, object: AutoTrade):
        self.o = object
        self.logger = self.o.logger
        self.last_trade_time = datetime.now() + timedelta(days=-1)
        self.config = Config.from_json(self.o.algorythm)

        self.win = 0
        self.lose = 0
        self.total_profit = 0

        # price levels
        self.high_price = 0
        self.low_price = 0
        self.cut_losses = 0
        self.take_profit = 0

    def run(self):
        sleep_interval = 60
        while True:
            # 하루 한번만 거래
            if self.last_trade_time.date() <= datetime.now().date() and self.o.is_start():

                self.logger.info(f"{self.o.platform} Algorithm1 거래 시작.")
                self.trade()
                self.logger.info(f"{self.o.platform} Algorithm1 거래 종료.")

                self.calc_win_rate()

            time.sleep(sleep_interval)

    def calc_win_rate(self) -> None:
        win_rate = 0
        if self.win != 0 or self.lose != 0:
            win_rate = self.win / (self.win + self.lose) * 100
        self.logger.info(f"win: {self.win}, lose: {self.lose}. 승률: {win_rate}%")

    def set_price_levels(self, high: float, low: float) -> None:
        self.high_price = high
        self.low_price = low
        self.cut_losses = self.o.get_cut_losses(self.high_price, self.low_price)
        self.take_profit = self.o.get_lock_gains(self.high_price, self.low_price)
        self.logger.info(f"high_price: {self.high_price}, low_price: {self.low_price}")
        self.logger.info(f"cut_losses: {self.cut_losses}, take_profit: {self.take_profit}")

    def check_signed(self, uuid: str) -> float:
        time.sleep(1)
        while not self.o._is_order_complete(uuid):
            self.logger.info("체결 대기중..")
            time.sleep(1)
        self.logger.info("체결 완료.")

        return self.o._get_signed_price(uuid)

    def trade(self) -> None:
        # 가격 세팅
        self.logger.info("가격 레벨 세팅 시작.")
        price_levels = self.o.get_price_levels_by_minute()
        if not price_levels or len(price_levels) < 2:
            self.logger.info("가격 레벨 세팅 실패. 거래 종료.")
            return

        self.set_price_levels(price_levels[0], price_levels[1])
        # 거래 시작 시점
        self.last_trade_time = datetime.now()

        # 매수시점 조회
        current_price = self._poll_price_until_high(self.high_price)
        if current_price == -1:
            self.logger.info("매수시점 조회 실패. 거래 종료.")
            return
        self.logger.info(f"매수시점 가격: {current_price}")

        # 잔고조회
        start_balance = balance = self.o._get_balance(self.o.quote_currency)
        self.logger.info(f"시작 잔고: {start_balance}")

        # 수수료 조회
        # shlee todo 수수료 조회 api가 있나?
        trade_fee = math.ceil(balance * 0.0005)

        available_balance = balance - trade_fee
        self.logger.info(f"거래가능 금액({self.o.quote_currency}): {balance} -> {available_balance}")

        if available_balance < 5000:
            self.logger.info("잔액 부족. 거래 종료.")
            return

        # 시장가 매수 요청
        bid_uuid = self.o._buy_market(str(available_balance))
        self.logger.info(f"매수요청 - {bid_uuid}")

        # 매수 가격 확인
        signed_price = self.check_signed(bid_uuid)

        self.logger.info(f"{self.o.trade_currency} 매수 가격: {signed_price}")
        if self.high_price < signed_price:
            self.logger.info("매수 가격이 기존 고가가격보다 높습니다. 가격 레벨을 조정합니다.")
            self.high_price = signed_price
            self.set_price_levels(self.high_price, self.low_price)

        # 잔고조회
        btc_balance = self.o._get_balance(self.o.trade_currency)

        # 시장가 매도
        ask_uuid = self._sell_on_threshold(btc_balance)
        self.logger.info(f"매도요청 - {ask_uuid}")

        # 매도 가격 확인
        signed_price = self.check_signed(ask_uuid)

        self.logger.info(f"{self.o.trade_currency} 매도 가격: {signed_price}")

        end_balance = self.o._get_balance(self.o.quote_currency)
        self.logger.info(f"종료 잔고: {end_balance}")
        self.logger.info(f"수익: {end_balance - start_balance}")
        self.total_profit += end_balance - start_balance
        self.logger.info(f"총 수익: {self.total_profit}")

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
            # 5분마다 한번씩 로깅
            if cnt >= 300:
                self.logger.info(f"매수 시점 잡는중..현재가 : {current_price}")
                cnt = 0

            # 설정된 시간내에 매수시점 못 잡을 시 거래 종료(기본 60분)
            trade_duration_min = self.o.algorythm.get("trade_duration_min", 60)
            if self.last_trade_time + timedelta(minutes=trade_duration_min) < datetime.now():
                return -1
        return current_price

    def _sell_on_threshold(self, qty: float) -> str:
        """
        현재가가 self.take_profit 보다 위로 가거나
        현재가가 self.cut_losses보다 아래로 가면 매도
        """
        rtn = ""
        retry_cnt = 0
        sleep_interval = 0.1
        # 5분마다 로깅
        logging_interval = (sleep_interval * 10 * 60) * 5
        while True:
            current_price = self.o._get_current_price()

            if retry_cnt > logging_interval:
                retry_cnt = 0
                self.logger.info(f"매도 시점 잡는중..현재가 : {current_price}")

            if self.cut_losses < current_price and current_price < self.take_profit:
                time.sleep(sleep_interval)
                retry_cnt += 1
                continue

            rtn = self.o._sell_market(qty)

            if current_price >= self.take_profit:
                self.win += 1
            elif current_price <= self.cut_losses:
                self.lose += 1

            break

        return rtn
