import time
from datetime import datetime, timedelta

from common.auto_trade import AutoTrade

class Algorithm1:
    def __init__(self, object: AutoTrade):
        self.o = object
        self.logger = self.o.logger
        self.last_trade_time = datetime.now() + timedelta(days=-1)
        self.win = 0
        self.lose = 0

    def run(self):
        while True:
            if self.last_trade_time.date() <= datetime.now().date() and self.o.is_start():
                self.last_trade_time = datetime.now()
                self.logger.info(f"{self.o.platform} Algorithm1 거래 시작.")
                self.trade()
                self.logger.info(f"{self.o.platform} Algorithm1 거래 종료.")
                win_rate = 0
                if self.win != 0 or self.lose != 0:
                    win_rate = self.win / (self.win + self.lose) * 100
                self.logger.info(f"win: {self.win}, lose: {self.lose}. 승률: {win_rate}%")

            time.sleep(60)

    def trade(self):
        high_price = 120
        low_price = 100
        cut_losses = self.o.get_cut_losses(high_price, low_price)
        lock_gains = self.o.get_lock_gains(high_price, low_price)
        self.logger.info(f"high_price: {high_price}, low_price: {low_price}")
        self.logger.info(f"cut_losses: {cut_losses}, lock_gains: {lock_gains}")

        # 매수시점 조회
        current_price = self._poll_price_until_high(high_price)
        if current_price == -1:
            self.logger.info("매수시점 조회 실패. 거래 종료.")
            return
        self.logger.info(f"매수시점 가격: {current_price}")

        # 매수 요청
        order_id = self.o.buy(current_price)
        self.logger.info(f"매수요청({order_id}): {current_price}")

        # 매수 확인
        if not self._ensure_buy_or_retry(order_id):
            return

        # 매도
        order_id = self._sell_on_threshold(lock_gains, cut_losses)
        self.logger.info(f"매도요청({order_id}): {current_price}")

    def _poll_price_until_high(self, high: float) -> float:
        """
        현재 가격이 최고가에 도달할 때까지 조회
        """
        # todo 현재가 조회
        current_price = 120
        cnt = 0
        while current_price < high:
            time.sleep(1)
            # todo 현재가 조회
            current_price = 120

            cnt += 1
            # 300번에 한번씩 로깅
            if cnt >= 300:
                self.logger.info(f"현재가 : {current_price}")
                cnt = 0

            # 20시간 내에 매수시점 못 잡을 시 거래 종료
            if self.last_trade_time < datetime.now() + timedelta(hours=20):
                return -1
        return current_price

    def _sell_on_threshold(self, high: float, low: float) -> None:
        """
        현재가가 high보다 위로 가거나
        현재가가 low보다 아래로 가면 매도
        """
        while True:
            # todo 현재가 조회
            current_price = 120

            if current_price >= high:
                self.o.sell(current_price)
                self.win += 1
                break
            elif current_price <= low:
                self.o.sell(current_price)
                self.lose += 1
                break

    def _ensure_buy_or_retry(self, order_id: str) -> bool:
        """
        매수요청 확인.
        매수가 되지 않는다면 취소하고 다시 요청.
        """
        retry_cnt = 0
        while True:
            retry_cnt += 1
            if retry_cnt > 5:
                self.logger.info(f"재시도 요청 끝. 거래 종료.")
                self.logger.info(f"매수요청({order_id}) 취소.")
                return False

            time.sleep(3)
            # todo 요청확인
            if True:
                break

            self.logger.info(f"매수요청 재시도..{retry_cnt}/5")

            # 요청 취소
            self.logger.info(f"매수요청({order_id}) 취소.")

            # 매수요청
            current_price = 120
            order_id = self.o.buy(current_price)
            self.logger.info(f"매수요청({order_id}): {current_price}")
        return True