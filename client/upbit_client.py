import time
from typing import Literal, Optional
from datetime import datetime
from datetime import time as TimeClass
from zoneinfo import ZoneInfo
from upbit import Upbit
from upbit.types import ticker

from common.order_algorithm.order_algorithm import OrderAlgorithm
from common.registry.registry import register
from common.auto_trade import AutoTrade

PLATFORM = "upbit"

@register(PLATFORM)
class UpbitClient(AutoTrade):
    def __init__(self, algorythm_no:int):
        super().__init__(PLATFORM, algorythm_no)

        self.client = Upbit(access_key=self.access_key, secret_key=self.secret_key)
        self.ticker = self.algorythm["ticker"]
        self.quote_currency = self.ticker.split("-")[0]
        self.trade_currency = self.ticker.split("-")[1]

        self.logger.info(f"UpbitClient init {self.platform} {self.algo_no} succeed.")
        self.logger.info(f"UpbitClient ticker: {self.ticker}")

    def is_start(self):
        return True

    def start_trade(self):
        trade = OrderAlgorithm(self, self.algorythm["algorythm_type"])
        trade.run()

    def get_candle_type(self):
        return self.algorythm["candle_type"]

    def get_candle_count(self):
        return int(self.algorythm["candle_count"])

    def get_candle_unit(self):
        return int(self.algorythm["candle_unit"])

    ############# abstractmethod #############
    def get_cut_losses(self, high, low):
        return (high + low) / 2

    def get_lock_gains(self, high, low):
        return high + (self.get_cut_losses(high, low) - high) * 2

    def _get_tickers(self):
        pass

    def _get_current_price(self) -> float:
        rtn = 0
        result = self.client.trades.list(
            market=self.ticker,
        )
        if result:
            rtn = float(result[0].trade_price)
        return rtn

    def _get_candle(self, ticker: str, type: str, count:int, unit: int = 1):
        result = None
        if type == "m":
            result = self.client.candles.list_minutes(
                unit,
                market=ticker,
                count=count
            )
            return result

    def _get_balance(self, currency: str):
        rtn = 0
        result = self.client.accounts.list()
        if not result:
            return rtn

        for account in result:
            if account.currency == currency:
                rtn = float(account.balance)
        return rtn

    def _get_agv_price(self, currency: str):
        rtn = 0
        result = self.client.accounts.list()
        if not result:
            return rtn

        for account in result:
            if account.currency == currency:
                rtn = float(account.avg_buy_price)
        return rtn

    def _buy_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    def _buy_price(self, balance: str):
        rtn = None
        result = self.client.orders.create(
            market=self.ticker,
            side="bid",
            price=balance,
            ord_type="price",
        )
        if result:
            rtn = result.uuid
        return rtn

    def _sell_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    def _sell_price(self, balance: str):
        rtn = None
        result = self.client.orders.create(
            market=self.ticker,
            side="ask",
            price=balance,
            ord_type="price",
        )
        if result:
            rtn = result.uuid
        return rtn

    def _cancel_order(self, order_id: str):
        pass
    ########################################

    def get_price_levels_by_minute(self) -> Optional[list]:
        candle_type = self.get_candle_type()
        candle_count = self.get_candle_count()
        candle_unit = self.get_candle_unit()
        target_hour, target_min = map(int, self.algorythm["target_time"].split(":"))
        if self.is_dst():
            target_hour -= 1

        retry_cnt = 0
        while True:
            candle = self._get_candle(self.ticker, candle_type, candle_count, candle_unit)
            # 캔들이 완성된 걸 가져옴.
            # 인덱스0 - 캔들 생성중, 1 - 완성된 캔들의 최신
            target = candle[1]
            current_candle_hour = datetime.fromisoformat(target.candle_date_time_kst).hour
            current_candle_min = datetime.fromisoformat(target.candle_date_time_kst).minute
            if (current_candle_hour != target_hour and
                    current_candle_min != target_min):
                # retry interval 60sec
                time.sleep(60)

                retry_cnt += 1
                # 1시간마다 로깅
                if retry_cnt > 60:
                    retry_cnt = 0
                    self.logger.info(f"가격 레벨 세팅 진행중..서머타임:{self.is_dst()}")
                    self.logger.info(f"현재 캔들={current_candle_hour}:{current_candle_min}")
                    self.logger.info(f"타겟 캔들={target_hour}:{target_min}")
                continue

            return [float(target.high_price), float(target.low_price)]
