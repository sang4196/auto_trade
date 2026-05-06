import json
from abc import *
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo


from common.logging.app_logging import setup_logging, get_logger, set_log_context

class AutoTrade(metaclass=ABCMeta):
    def __init__(self, platform: str):
        self.platform: str = platform

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
    def buy(self, ticker: str, side: str, price: int, qty: int):
        pass

    @abstractmethod
    def sell(self, ticker: str, side: str, price: int, qty: int):
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        pass
