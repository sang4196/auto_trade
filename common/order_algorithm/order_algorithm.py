from common.auto_trade import AutoTrade
from common.enum.enums import TradeType
from common.order_algorithm.algorithm1 import Algorithm1

class OrderAlgorithm:
    def __init__(self, object: AutoTrade, trade_type: TradeType):
        self.strategy = object
        self.trade_type = trade_type

    def run(self):
        if self.trade_type == TradeType.AT_ALGORITHM_1.value:
            Algorithm1(self.strategy)

