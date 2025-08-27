import backtrader as bt
import pandas as pd
from log import logger
import yaml
from config import config


# Create a Stratey
class StrategySelfBase(bt.Strategy):

    def __init__(self, doprint=True):
        # 配置
        self.stock_id = config["stock_id"]
        self.config = config

        self.doprint = doprint
        self.listordermsg = []
        self.inds = dict()
        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]["firstbaropen"] = d.open[1]
            self.inds[d]["earnmoney"] = 0.0

    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        if self.doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def next(self):
        self.log("Warning Run StrategySelfBase!")

    def stop(self):
        pass
        # for i, d in enumerate(self.datas):
        #     self.log("(earnmoney: %.2f, Name: %s)" % (self.inds[d]["earnmoney"], i))
        #     self.profit = (
        #         (d.close[0] - self.inds[d]["firstbaropen"])
        #         * 100
        #         / self.inds[d]["firstbaropen"]
        #     )
        #     self.log(
        #         "(FirstBarOpen: %.2f, LastBarClose: %.2f, Profit: %.2f)"
        #         % (self.inds[d]["firstbaropen"], d.close[0], self.profit)
        #     )

    def notify_order(self, order):
        # 订单状态为提交和接受，不做处理
        if order.status in [order.Submitted, order.Accepted]:
            return

        # 检查订单是否成交
        # 注意，没有足够现金的话，订单会被拒绝。
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "Buy Executed. Price: %.2f, Cost: %.2f, Comm %.2f, dt %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                        order.executed.dt,
                    )
                )
                self.buyprice = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    "Sell Executed. Price: %.2f, Cost: %.2f, Comm %.2f , dt %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                        order.executed.dt,
                    )
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.inds[trade.data]["earnmoney"] += trade.pnlcomm

        self.log(
            "Operation Profit, 此次交易不计算佣金 %.2f, 计算佣金 %.2f"
            % (trade.pnl, trade.pnlcomm)
        )

    def hello():
        print("Hello, this is StrategySelfBase!")
        logger.info("Hello, this is StrategySelfBase!")
        return "Hello, this is StrategySelfBase!"
