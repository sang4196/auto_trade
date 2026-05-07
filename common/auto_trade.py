import json
from abc import *
from pathlib import Path
from datetime import datetime, time
from typing import Union
from zoneinfo import ZoneInfo


from common.logging.app_logging import setup_logging, get_logger, set_log_context

class AutoTrade(metaclass=ABCMeta):
    def __init__(self, platform: str):
        self.platform: str = platform
        self.client = None

        self.config = self.read_config()
        self.access_key: str = self.config["access_key"]
        self.secret_key: str = self.config["secret_key"]
        self.algorythm: str = self.config["algorythm"]

        self.logger = self.get_logger()

    def get_logger(self):
        setup_logging(
            level="INFO",
            app_name="autoTrade",
            log_format="console",
        )
        set_log_context(job_id=self.platform)

        return get_logger(__name__)

    def read_config(self):
        return json.load(Path(f"config/{self.platform}.json").open())

    def is_start(self, is_regular: bool = True):
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        ny = now_kst.astimezone(ZoneInfo("America/New_York"))
        if is_regular:
            if ny.weekday() >= 5:  # Sat/Sun
                return False
        return time(9, 40) <= ny.timetz() < time(16, 0)

    @abstractmethod
    def get_cut_losses(self, high, low):
        pass

    @abstractmethod
    def get_lock_gains(self, high, low):
        pass

    @abstractmethod
    def _get_tickers(self):
        pass

    @abstractmethod
    def _get_current_price(self):
        pass

    @abstractmethod
    def _get_candle(self, item:str, type: str, count:int, unit: int = 0):
        """
        item = pair or event
        1분봉
        ex) type = "m", unit = 1,3,5..
        일봉
        ex) type = "d"
        주봉
        ex) type = "w"
        월봉
        ex) type = "M"
        """
        pass

    @abstractmethod
    def get_price_levels_by_minute(
            self, type: str, count: int, unit: int, minutes: int) -> Union[list, None]:
        pass

    ###########################################
    ############### private API ###############
    ###########################################

    # wallet API
    @abstractmethod
    def _get_balance(self, currency: str):
        pass

    # order API
    @abstractmethod
    def _buy_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    @abstractmethod
    def _buy_price(self, price: str):
        """
        시장가
        """
        pass

    @abstractmethod
    def _sell_limit(self, ticker: str, side: str, price: int, qty: int):
        pass

    @abstractmethod
    def _sell_price(self, ticker: str, side: str, price: int, qty: int):
        """
        시장가
        """
        pass

    @abstractmethod
    def _cancel_order(self, order_id: str):
        pass
