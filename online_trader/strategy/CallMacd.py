from datetime import datetime
from longport.openapi import OrderStatus
import time
from dataloader.LongPortOnline import LongPortOnline
from factor.MACDFactor import MACDFactor
from online_trader.strategy.TraderStrategy import TraderStrategy
from log import logger
from online_trader.orderbook.OrderBook import OrderBook
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
        self.stock_ids = config["stock_id"]

        # self.market = self.stock_id.split(".")[1]
        # if self.market == "HK":
        #     self.current_time = TimeCheck.get_beijing_time()
        # elif self.market == "US":
        #     self.current_time = TimeCheck.get_us_time()

        global data
        global order_book
        global last_order
        # 初始化数据类
        data = LongPortOnline()
        order_book = OrderBook()
        self.init_strategy()

    def init_strategy(self) -> None:
        last_order = ""
        self.candlesticks = data.get_history_candlesticks(self.stock_ids)
        self.current_price = data.get_current_price(self.stock_ids)

        self.macd_factors = [
            MACDFactor(stock_id=self.stock_ids[index], hist_candlesticks=self.candlesticks[index])
            for index,stock_id in enumerate(self.stock_ids)
        ]

    def Run(self) -> None:
        logger.info("Start macd strategy")
        # 更新数据
        
        is_next_day = TimeCheck.check_next_day()

        if is_next_day:
            logger.info("New day, re-initialize strategy")
            self.init_strategy()

        data.update_info()
        self.current_price = data.get_current_price(self.stock_ids)

        # Check if we are in the market
        # 入场条件
        for index, stock_id in enumerate(self.stock_ids):
            candle = type(
                "Candle",
                (object,),
                {"open": self.current_price[index], "close": self.current_price[index]},
            )()

            result = self.macd_factors[index].check(candle)

            if result == 1:
                logger.info("macd buy")
                feishu.message(f"macd buy {stock_id} {self.current_price[index]}")

            elif result == 2:
                logger.info("macd sell")
                feishu.message(f"macd sell {stock_id} {self.current_price[index]}")

            self.macd_factors[index].delete_last_candlestick()

        return None, None, None
