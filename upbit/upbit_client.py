import time
from typing import Union, Literal
from datetime import datetime

from pip._internal.utils import datetime

from upbit import Upbit
from common.registry.registry import register
from common.auto_trade import AutoTrade

PLATFORM = "upbit"

@register(PLATFORM)
class UpbitClient(AutoTrade):
    def __init__(self):
        super().__init__(PLATFORM)

        self.client = Upbit(self.access_key, self.secret_key)
        self.item = self.config["item"]

    ############# abstractmethod #############
    def get_cut_losses(self, high, low):
        return (high + low) / 2

    def get_lock_gains(self, high, low):
        return high + (self.get_cut_losses(high, low) - high) * 2

    def _get_tickers(self):
        pass

    def _get_current_price(self) -> Union[str, None]:
        rtn = None
        result = self.client.trades.list(
            market=self.item,
        )
        if result:
            rtn = result[0].trade_price
        return rtn

    def _get_candle(self, item: str, type: str, count:int, unit: Literal[1, 3, 5, 10, 15, 30, 60, 240] = 1):
        result = None
        if type == "m":
            result = self.client.candles.list_minutes(
                unit,
                market=item,
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
                rtn = account.balance
        return rtn

    def _buy_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    def _buy_price(self, balance: str):
        rtn = None
        result = self.client.orders.create(
            market=self.item,
            side="bid",
            price=balance,
            ord_type="price",
        )
        if result:
            rtn = result.uuid
        return rtn

    def _sell_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    def _sell_price(self, ticker: str, side: str, price: int, qty: int):
        pass

    def _cancel_order(self, order_id: str):
        pass
    ########################################

    def get_price_levels_by_minute(self, type: str, unit: int, minutes: int) -> Union[list, None]:
        """
        Fetches price levels (high and low) for a specific minute from a candle chart.

        This method retrieves the high and low prices from the most recently completed
        candle chart for a specific minute. If the targeted minute is not found in the
        chart data, the method retries until the maximum retry limit (based on the unit)
        is reached.

        Parameters:
        type: str
            The type of the candle chart to retrieve, such as "minute" or "day".
        unit: int
            The time unit of the candles (e.g., 1-minute candles, 5-minute candles, etc.).
        minutes: int
            The minute value to target within the candle data.

        Returns:
        list or None
            A list containing the high price and low price of the targeted minute if found.
            Otherwise, returns None if the retry limit is exceeded.
        """
        retry_cnt = 0
        while True:
            # 해당 분봉 만큼 retry
            # ex) unit = 5. 5분봉 최대 retry횟수 5.
            if retry_cnt > unit:
                return None
            candle = self._get_candle(self.item, type, 2, unit)
            # 캔들이 완성된 걸 가져옴.
            # 인덱스0 - 캔들 생성중, 1 - 완성된 캔들의 최신
            target = candle[1]
            if datetime.fromisoformat(target.candle_date_time_kst).minute != minutes:
                # retry interval 60sec
                time.sleep(60)
                continue

            return [target.high_price, target.low_price]


