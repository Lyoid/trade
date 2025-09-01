from datetime import datetime
from longport.openapi import OrderStatus
import time
from dataloader.LongPortOnline import LongPortOnline
from .TraderStrategy import TraderStrategy
from log import logger
from online_trader.orderbook.OrderBook import OrderBook
from config import config

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


class NetTrader(TraderStrategy):
    """A base class for trader strategies."""

    def __init__(self) -> None:
        super().__init__()
        self.first_amount = config["strategy"]["first_amount"]
        self.amount = config["strategy"]["amount"]
        self.delta_price = config["strategy"]["delta_price"]
        self.stock_id = config["stock_id"]

        global data
        global order_book
        global last_order
        # 初始化数据类
        data = LongPortOnline()
        order_book = OrderBook()
        last_order = ""
        # 历史交易记录
        self.last_trader_price = data.get_last_trade_price(
            datetime(2025, 2, 1), self.stock_id
        )[0]

    def Run(self) -> None:

        re = []
        result = dict()
        result['stock_id'] = self.stock_id[0]

        # 查看当前股票是否在交易时间
        if not data.is_trading(self.stock_id[0]):
            # 待机60秒
            time.sleep(60)
            return None



        logger.info("Run NetTrader Strategy")
        # 查看仓位 空仓则下单
        if data.check_stock_positions(self.stock_id[0]) == 0:
            logger.info("not have stock position create order")
            current_price = data.get_current_price(self.stock_id)
            self.last_trader_price = current_price[0]
            result['price'] = current_price[0]
            result['amount'] = config["strategy"]["first_amount"]
            result['order_side'] = OrderSide.Buy
            re.append(result)
            return re

        # 开始网格交易
        logger.info("Start NetTrade")
        logger.info(f"last_trader_price: {self.last_trader_price}")

        # 历史交易记录
        self.last_trader_price = data.get_last_trade_price(
            datetime(2025, 2, 1), self.stock_id
        )[0]

        prices = data.get_current_price(self.stock_id)
        current_price = prices[0]
        current_delta = current_price - self.last_trader_price

        logger.info(f"current_price: {current_price}")
        logger.info(f"current_delta: {current_delta}")

  
        result['price'] = None
        result['amount'] = None
        result['order_side'] = None

        if current_delta > self.delta_price:
            result['price'] = current_price
            result['amount'] = self.amount
            result['order_side'] = OrderSide.Sell

        elif current_delta < -self.delta_price:
            result['price'] = current_price
            result['amount'] = self.amount
            result['order_side'] = OrderSide.Buy

        re.append(result)

        return re
