import pyupbit
import json
from pathlib import Path

from common.auto_trade import AutoTrade

class Upbit(AutoTrade):
    def __init__(self):
        super().__init__()