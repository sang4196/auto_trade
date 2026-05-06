from common.registry.registry import register
from common.auto_trade import AutoTrade

PLATFORM = "upbit"

@register(PLATFORM)
class Upbit(AutoTrade):
    def __init__(self):
        super().__init__(PLATFORM)

    def get_cut_losses(self, high, low):
        return (high + low) / 2

    def get_lock_gains(self, high, low):
        return high + (self.get_cut_losses(high, low) - high) * 2

    def get_tickers(self):
        pass

    def get_current_price(self, ticker: str):
        pass

    def get_candle(self, type: str, interval: int):
        pass

    def get_balance(self):
        pass

    def create_order(self, ticker: str, side: str, price: int, qty: int):
        pass

    def cancel_order(self, order_id: str):
        pass
