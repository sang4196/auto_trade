import json
from abc import *
from pathlib import Path
from typing import Optional


from common.logging.app_logging import setup_logging, get_logger, set_log_context

class AutoTrade(metaclass=ABCMeta):
    def __init__(self, platform: str, algorythm_no:int):
        self.platform: str = platform
        self.client = None
        self.algo_no = algorythm_no

        self.config: Optional[dict] = None
        self.access_key: Optional[str] = None
        self.secret_key: Optional[str] = None
        self.algorythm: Optional[dict] = None

        self.load_config()
        self.logger = self.get_logger()

    def get_logger(self):
        setup_logging(
            level="INFO",
            app_name="autoTrade",
            log_format="console",
        )
        set_log_context(job_id=self.platform)

        return get_logger(__name__)

    def load_config(self):
        self.config = json.load(Path(f"config/{self.platform}.json").open())
        self.algorythm: dict = self.config["algorythm"][self.algo_no]

    @abstractmethod
    def start_trade(self):
        pass

    @abstractmethod
    def is_start(self):
        pass

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
    def _get_candle(self, ticker:str, type: str, count:int, unit: int = 0):
        """
        ticker = pair or ticker
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
    def get_price_levels_by_minute(self, type: str, unit: int, minutes: int) -> Optional[list]:
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
