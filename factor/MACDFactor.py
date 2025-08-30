import backtrader as bt
from factor.FactorBase import FactorBase
from log import logger
from config import config

import pandas as pd


# Create a Factor
class MACDFactor(FactorBase):
    params = {
        "period_1": 30,  # 短期均线周期
        "period_2": 50,  # 长期均线周期
        "period_3": 50,  # 信号线周期
    }

    def __init__(self, stock_id, hist_candlesticks=None) -> None:
        super().__init__(stock_id=stock_id, cfg=config)
        self.params["period_1"] = config["strategy"]["period_1"]
        self.params["period_2"] = config["strategy"]["period_2"]
        self.params["period_3"] = config["strategy"]["period_3"]

        if hist_candlesticks is not None:
            self.candlesticks = hist_candlesticks
        else:
            self.candlesticks = []

    def algo(self, prices):
        # logger.info(f"input: {len(prices)}")
        # logger.info(f"input: {prices}")
        # # 示例数据：假设数组为股票收盘价
        close_prices = pd.Series(prices)

        # 计算短期（12日）和长期（26日）EMA
        short_ema = close_prices.ewm(span=self.params["period_1"], adjust=False).mean()  # 快速EMA
        long_ema = close_prices.ewm(span=self.params["period_2"], adjust=False).mean()   # 慢速EMA

        # 计算MACD线（短期EMA - 长期EMA）
        macd_line = short_ema - long_ema

        # 计算信号线（MACD线的9日EMA）
        signal_line = macd_line.ewm(span=self.params["period_3"], adjust=False).mean()

        # 计算柱状图（MACD线 - 信号线）
        histogram = macd_line - signal_line

        # 判断金叉（零轴上方）
        golden_cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1)) 

        # 判断死叉（零轴下方）
        death_cross = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        # 计算最近30日的价格与柱状图峰值/谷值
        window = 30
        price_peak = close_prices.rolling(window).max()
        price_trough = close_prices.rolling(window).min()
        hist_peak = histogram.rolling(window).max()
        hist_trough = histogram.rolling(window).min()

        # 判断顶背离（价格新高但柱状图未新高）
        top_divergence = (close_prices.iloc[-1] > price_peak.iloc[-2]) & (histogram.iloc[-1] <= hist_peak.iloc[-2])

        # 判断底背离（价格新低但柱状图未新低）
        bottom_divergence = (close_prices.iloc[-1] < price_trough.iloc[-2]) & (histogram.iloc[-1] >= hist_trough.iloc[-2])

        logger.info(f"顶背离信号:{top_divergence}")
        logger.info(f"底背离信号:{bottom_divergence}")

        logger.info(f"金叉信号位置:{golden_cross[golden_cross].index.tolist()}")
        logger.info(f"死叉信号位置:{death_cross[death_cross].index.tolist()}")

        # 输出结果
        logger.info(f"MACD线:, {macd_line.tolist()[-1]}")
        logger.info(f"信号线:, {signal_line.tolist()[-1]}")
        logger.info(f"柱状图:, {histogram.tolist()[-1]}")

        today_index = len(close_prices) - 1

        return golden_cross[golden_cross].index.tolist(),death_cross[death_cross].index.tolist(),top_divergence,bottom_divergence



    def check(self, daily_data):
        logger.info("Start macd strategy")
        # 更新数据
        self.candlesticks.append(daily_data)

        if len(self.candlesticks) < self.params["period_2"]:
            logger.info("Not enough data to calculate MACD, waiting for more data")
            return 0,False,False

        # 计算MACD指标
        # 计算所有30日均线和50日均线
        closes = [candle.close for candle in self.candlesticks]

        golden_cross,death_cross,top_divergence,bottom_divergence = self.algo(closes)

        
        today_index = len(self.candlesticks) - 1
        if len(golden_cross) > 0 and golden_cross[-1] == today_index:
            logger.info("Golden cross detected, placing buy order")
            return 1,top_divergence,bottom_divergence
        
        if len(death_cross) > 0 and death_cross[-1] == today_index:
            logger.info("Death cross detected, placing sell order")
            return 2,top_divergence,bottom_divergence

        logger.info("Nothing to do, waiting for next cycle")
        return 0,top_divergence,bottom_divergence

    def delete_last_candlestick(self):
        if len(self.candlesticks) > 0:
            self.candlesticks.pop()
