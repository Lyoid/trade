from datetime import datetime
from longport.openapi import OrderStatus
import time
from dataloader.LongPortOnline import LongPortOnline
from factor.MACDFactor import MACDFactor
from online_trader.strategy.TraderStrategy import TraderStrategy
from log import logger
from config import config
from tools.TimeCheck import TimeCheck
from tools.FeiShu import feishu

from longport.openapi import (
    QuoteContext,
    Config,
    SubType,
    PushQuote,
    Period,
    AdjustType,
    TradeContext,
    OrderType,
    OrderSide,
    TimeInForceType,
    OpenApiException,
    OrderStatus,
    Market,
)

class CallMacd(TraderStrategy):
    """A base class for trader strategies."""

    def __init__(self) -> None:
        super().__init__()
        self.period_1 = config["strategy"]["period_1"]
        self.period_2 = config["strategy"]["period_2"]

        global data
        global order_book
        global last_order
        # 初始化数据类
        data = LongPortOnline()

        self.stock_ids = data.watchlists_by_symbol()

        self.init_strategy()

    def init_strategy(self) -> None:
        last_order = ""
        self.candlesticks = data.get_history_candlesticks(self.stock_ids)
        self.start_call = [True for i in self.stock_ids]


        self.macd_factors = [
            MACDFactor(stock_id=self.stock_ids[index], hist_candlesticks=self.candlesticks[index])
            for index,stock_id in enumerate(self.stock_ids)
        ]

    def init_factor(self, index) -> None:
        self.candlesticks = data.get_history_candlesticks([self.stock_ids[index]])
        self.macd_factors[index] = MACDFactor(stock_id=self.stock_ids[index], hist_candlesticks=self.candlesticks[0])
        

    def Run(self) -> None:

        if data.is_tradings():
            # 更新数据 
            self.current_price = data.get_current_price(self.stock_ids)
        else:
            logger.info("非交易时间，等待8小时")
            time.sleep(3600*8)
            return None

        for index, stock_id in enumerate(self.stock_ids):
            logger.info(f"Processing stock: {stock_id}")
            # 查看当前股票是否在交易时间
            if not data.is_trading(stock_id):
                self.init_factor(index)
                self.start_call[index] = True
                continue

            logger.info("Start macd strategy")

            # Check if we are in the market
            # 入场条件
            candle = type(
                "Candle",
                (object,),
                {"open": self.current_price[index], "close": self.current_price[index]},
            )()

            result,top_divergence,bottom_divergence = self.macd_factors[index].check(candle)

            if self.start_call[index] == True:
                if top_divergence:
                    strline = "顶背离发生"
                    feishu.message(f"macd {stock_id} {strline}")
                if bottom_divergence:
                    strline = "底背离发生"
                    feishu.message(f"macd {stock_id} {strline}")

                if result == 1:
                    logger.info("macd buy")
                    feishu.message(f"macd buy {stock_id} {self.current_price[index]}")

                elif result == 2:
                    logger.info("macd sell")
                    feishu.message(f"macd sell {stock_id} {self.current_price[index]}")

                self.start_call[index] = False


            self.macd_factors[index].delete_last_candlestick()

        return None
