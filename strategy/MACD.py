import backtrader as bt
from strategy.StrategySelfBase import StrategySelfBase
from factor.MACDFactor import MACDFactor
from dataloader.LongPortTest import dataset


# Create a Stratey
class MACD(StrategySelfBase):

    def __init__(self):
        super().__init__()

        self.macd_factor = MACDFactor(self.stock_id)

        for i, d in enumerate(self.datas):
            self.inds[d]["sma30"] = bt.ind.SMA(d.close, period=30)
            self.inds[d]["sma50"] = bt.ind.SMA(d.close, period=50)
            self.inds[d]["crossover"] = bt.ind.CrossOver(
                self.inds[d]["sma50"], self.inds[d]["sma30"]
            )

            # 跟踪订单状态以及买卖价格和佣金
            self.inds[d]["buyprice"] = None
            self.inds[d]["buycomm"] = None
            self.inds[d]["order"] = None

    def next(self):

        # Check if we are in the market
        # 入场条件
        candle = type(
            "Candle",
            (object,),
            {"open": self.data.open[0], "close": self.data.close[0]},
        )()
        if not self.position:
            if self.macd_factor.check(candle) == 1:
                self.buy()

        else:
            if self.macd_factor.check(candle) == 2:
                self.sell()
