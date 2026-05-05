import json
from abc import *
from pathlib import Path

class AutoTrade(metaclass=ABCMeta):
    def __init__(self, trade_type: str):
        self.trade_type: str = trade_type

        config = self.read_config()
        self.access_key: str = config["access_key"]
        self.secret_key: str = config["secret_key"]

    def read_config(self):
        return json.load(Path(f"config/{self.trade_type}.json").open())

    @abstractmethod
    def get_tickers(self):
        pass

    @abstractmethod
    def get_current_price(self, ticker: str):
        pass

    @abstractmethod
    def get_candle(self, type: str, interval: int):
        """
        1분봉
        ex) type = "m", interval = 1
        일봉
        ex) type = "d", interval = 100(카운트)
        주봉
        ex) type = "w", interval = 100(카운트)
        월봉
        ex) type = "M", interval = 100(카운트)
        """
        pass

    ###########################################
    ############### private API ###############
    ###########################################

    # wallet API
    @abstractmethod
    def get_balance(self):
        pass

    # order API
    @abstractmethod
    def create_order(self, ticker: str, side: str, price: int, qty: int):
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        pass
