from common.registry.registry import register
from common.auto_trade import AutoTrade

PLATFORM = "upbit"

@register(PLATFORM)
class Upbit(AutoTrade):
    def __init__(self):
        super().__init__(PLATFORM)
