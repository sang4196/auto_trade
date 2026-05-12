import json
from abc import *
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

        self.quote_currency: str = ""
        self.trade_currency: str = ""

        self.load_config()
        self.logger = self.get_logger()

        self.logger.info(f"AutoTrade initialize. platform: {self.platform} algorythm: {self.algo_no}")

    def get_logger(self):
        setup_logging(
            level="INFO",
            app_name=f"autoTrade_{self.platform}_{self.algo_no}",
            log_format="console",
        )
        set_log_context(job_id=self.platform)

        return get_logger(__name__)

    def load_config(self):
        self.config = json.load(Path(f"config/{self.platform}.json").open())
        self.algorythm: dict = self.config["algorythm"][self.algo_no]
        self.access_key = self.config["access_key"]
        self.secret_key = self.config["secret_key"]

    def is_dst(self):
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        now_ny = now_kst.astimezone(ZoneInfo("America/New_York"))
        return now_ny.dst() != timedelta(0)

    @abstractmethod
    def start_trade(self) -> None:
        pass

    @abstractmethod
    def is_start(self) -> bool:
        pass

    @abstractmethod
    def get_cut_losses(self, high, low) -> Optional[float]:
        pass

    @abstractmethod
    def get_lock_gains(self, high, low) -> Optional[float]:
        pass

    @abstractmethod
    def _get_tickers(self) -> str:
        pass

    @abstractmethod
    def _get_current_price(self) -> float:
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
    def get_price_levels_by_minute(self) -> Optional[list]:
        pass

    ###########################################
    ############### private API ###############
    ###########################################

    # wallet API
    @abstractmethod
    def _get_signed_price(self, order_id: str):
        pass

    @abstractmethod
    def _is_order_complete(self, order_id: str):
        pass

    @abstractmethod
    def _get_balance(self, currency: str):
        pass

    @abstractmethod
    def _get_agv_price(self, currency: str):
        pass

    # order API
    @abstractmethod
    def _buy_limit(self, price: float, qty: float):
        pass

    @abstractmethod
    def _buy_market(self, price: str):
        """
        시장가
        """
        pass

    @abstractmethod
    def _sell_limit(self, price: float, qty: float):
        pass

    @abstractmethod
    def _sell_market(self, qty: float):
        """
        시장가
        """
        pass

    @abstractmethod
    def _cancel_order(self, order_id: str):
        pass
