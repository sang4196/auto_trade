import time
from typing import Optional
from datetime import datetime
from upbit import Upbit

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

        self.logger.info(f"UpbitClient initialize.")
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
        return high + (high - self.get_cut_losses(high, low)) * 2

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

    def _get_order(self, order_id: str):
        return self.client.orders.retrieve(
            uuid=order_id,
        )

    def _get_signed_price(self, order_id: str):
        rtn = 0
        result = self._get_order(order_id)

        if not result:
            return rtn

        trades_count = int(result.trades_count)
        if trades_count > 0:
            rtn = float(result.trades[0].price or "0")

        if trades_count > 1:
            self.logger.warning(f"trades_count > 1. {trades_count}")

        return rtn

    def _is_order_complete(self, order_id: str):
        rtn = False
        result = self._get_order(order_id)

        if result:
            rtn = result.state in {"done", "cancel"}
        # state
        # wait: 체결 대기
        # watch: 예약 주문 대기
        # done: 체결 완료
        # cancel: 주문 취소
        return rtn

    def _get_balance(self, currency: str):
        rtn = 0
        result = self.client.accounts.list()
        if not result:
            return rtn

        for account in result:
            if account.currency == currency:
                rtn = float(account.balance)
                break
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

    def _buy_limit(self, price: float, qty: float):
        rtn = None
        result = self.client.orders.create(
            market=self.ticker,
            side="bid",
            volume=str(qty),
            price=str(price),
            ord_type="limit",
        )
        if result:
            rtn = result.uuid
        return rtn

    def _buy_market(self, balance: str):
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

    def _sell_limit(self, price: float, qty: float):
        rtn = None
        result = self.client.orders.create(
            market=self.ticker,
            side="ask",
            volume=str(qty),
            price=str(price),
            ord_type="limit",
        )
        if result:
            rtn = result.uuid
        return rtn

    def _sell_market(self, qty: float):
        rtn = None
        result = self.client.orders.create(
            market=self.ticker,
            side="ask",
            volume=str(qty),
            ord_type="market",
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
        # retry interval 60sec
        sleep_interval = 60
        # 1시간마다 로깅
        logging_interval = sleep_interval * 60
        while True:
            candle = self._get_candle(self.ticker, candle_type, candle_count, candle_unit)
            # 캔들이 완성된 걸 가져옴.
            # 인덱스0 - 캔들 생성중, 1 - 완성된 캔들의 최신
            target = candle[1]
            current_candle_hour = datetime.fromisoformat(target.candle_date_time_kst).hour
            current_candle_min = datetime.fromisoformat(target.candle_date_time_kst).minute
            if (current_candle_hour != target_hour or
                    current_candle_min != target_min):
                retry_cnt += 1

                if retry_cnt > logging_interval:
                    retry_cnt = 0
                    self.logger.info(f"가격 레벨 세팅 진행중..서머타임:{self.is_dst()}. "
                                     f"현재 캔들={current_candle_hour}:{current_candle_min}, "
                                     f"타겟 캔들={target_hour}:{target_min}")

                time.sleep(sleep_interval)
                continue

            return [float(target.high_price), float(target.low_price)]

if __name__ == "__main__":
    print("test")