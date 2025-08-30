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


class MACD(TraderStrategy):
    """A base class for trader strategies."""

    def __init__(self) -> None:
        super().__init__()
        self.period_1 = config["strategy"]["period_1"]
        self.period_2 = config["strategy"]["period_2"]
        self.amount = config["strategy"]["amount"]
        self.stock_id = config["stock_id"][0]

        self.market = self.stock_id.split(".")[-1]
        if self.market == "HK":
            self.current_time = TimeCheck.get_beijing_time()
        elif self.market == "US":
            self.current_time = TimeCheck.get_us_time()

        global data
        global order_book
        global last_order
        # 初始化数据类
        data = LongPortOnline()
        order_book = OrderBook()
        self.init_strategy()

    def init_strategy(self) -> None:
        last_order = ""
        self.candlesticks = data.get_history_candlesticks(self.stock_id)
        self.current_price = data.get_current_price([self.stock_id])
        self.macd_factor = MACDFactor(
            stock_id=self.stock_id, hist_candlesticks=self.candlesticks
        )

    def Run(self) -> None:
        # 查看当前股票是否在交易时间
        if not data.is_trading(self.stock_id):
            # 待机60秒
            time.sleep(60)
            return None, None, None

        logger.info("Start macd strategy")
        # 更新数据
        if self.market == "US":
            is_next_day = TimeCheck.check_next_day()
            self.current_time = TimeCheck.get_us_time()
        elif self.market == "HK":
            is_next_day = TimeCheck.check_next_day()
            self.current_time = TimeCheck.get_beijing_time()

        if is_next_day:
            logger.info("New day, re-initialize strategy")
            self.init_strategy()

        data.update_info()
        self.current_price = data.get_current_price([self.stock_id])

        # Check if we are in the market
        # 入场条件
        candle = type(
            "Candle",
            (object,),
            {"open": self.current_price[0], "close": self.current_price[0]},
        )()

        result = self.macd_factor.check(candle)
        order_side = None
        if result == 1:
            logger.info("macd buy")
            order_side = OrderSide.Buy

        elif result == 2:
            logger.info("macd sell")
            order_side = OrderSide.Sell

        self.macd_factor.delete_last_candlestick()

        return self.current_price, self.amount, order_side
