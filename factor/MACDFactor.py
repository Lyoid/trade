import backtrader as bt
from factor.FactorBase import FactorBase
from log import logger
from config import config


# Create a Factor
class MACDFactor(FactorBase):
    params = {
        "period_1": 30,  # 短期均线周期
        "period_2": 50,  # 长期均线周期
        "amount": 30,  #
    }

    def __init__(self, stock_id, hist_candlesticks=None) -> None:
        super().__init__(stock_id=stock_id, cfg=config)
        self.params["period_1"] = config["strategy"]["period_1"]
        self.params["period_2"] = config["strategy"]["period_2"]
        self.params["amount"] = config["strategy"]["amount"]

        if hist_candlesticks is not None:
            self.candlesticks = hist_candlesticks
        else:
            self.candlesticks = []

    def check(self, daily_data):
        logger.info("Start macd strategy")
        # 更新数据
        self.candlesticks.append(daily_data)

        if len(self.candlesticks) < self.params["period_2"]:
            logger.info("Not enough data to calculate MACD, waiting for more data")
            return 0

        # 计算MACD指标
        # 计算所有30日均线和50日均线
        closes = [candle.close for candle in self.candlesticks]

        ma_30_list = []
        ma_50_list = []
        if len(closes) >= self.params["period_2"]:
            for i in range(self.params["period_2"] - 1, len(closes)):
                ma_30 = (
                    sum(closes[i - self.params["period_1"] + 1 : i + 1])
                    / self.params["period_1"]
                )
                ma_50 = (
                    sum(closes[i - self.params["period_2"] + 1 : i + 1])
                    / self.params["period_2"]
                )
                ma_30_list.append(ma_30)
                ma_50_list.append(ma_50)
        else:
            ma_30_list = []
            ma_50_list = []

        # 判断金叉（短期均线上穿长期均线）和死叉（短期均线下穿长期均线）
        golden_cross = False
        death_cross = False
        if len(ma_30_list) >= 2 and len(ma_50_list) >= 2:
            # 前一时刻短期均线在下，当前时刻上穿
            if ma_30_list[-2] < ma_50_list[-2] and ma_30_list[-1] > ma_50_list[-1]:
                golden_cross = True
            # 前一时刻短期均线在上，当前时刻下穿
            elif ma_30_list[-2] > ma_50_list[-2] and ma_30_list[-1] < ma_50_list[-1]:
                death_cross = True

        # 金叉
        if golden_cross:
            logger.info("Golden cross detected, placing buy order")
            return 1

        # 死叉
        elif death_cross:
            logger.info("Death cross detected, placing sell order")
            return 2

        logger.info("Nothing to do, waiting for next cycle")
        return 0

    def delete_last_candlestick(self):
        if len(self.candlesticks) > 0:
            self.candlesticks.pop()
