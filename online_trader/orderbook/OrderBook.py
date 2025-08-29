import asyncio
from concurrent.futures import ThreadPoolExecutor
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
from decimal import Decimal
from typing import Dict, Protocol, Type
from log import logger
from config import config
import time
from dataloader.LongPortOnline import dataset


class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class OrderBook(Borg):
    def __init__(self) -> None:
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print('"OrderBook" instance already exists, returning existing instance.')
        else:
            print("Initialize the order book with empty lists for bids and asks.")
            super().__init__()
            self.order_book = {}
            self.stock_id = config["stock_id"]
            self.data = dataset
            self.trade_ctx = self.data.trade_ctx
            self.quote_ctx = self.data.quote_ctx
            resp = self.trade_ctx.today_orders(
                symbol=self.stock_id,
            )
            for order in resp:
                if (
                    order.status != OrderStatus.Filled
                    and order.status != OrderStatus.Canceled
                    and order.status != OrderStatus.Rejected
                ):
                    self.order_book[order.order_id] = order

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.check_order_status)
            print("Order status check thread started (not awaited)..")

    def check_order_status(self):
        print("Check In check_order_status")

        while True:
            for order_id, detail in self.order_book.items():
                logger.info(f"Order {order_id} In order books.")
                # Check the order status
                try:
                    resp = self.trade_ctx.order_detail(
                        order_id=order_id,
                    )
                    if resp.status != detail.status:
                        self.order_book[order_id] = detail
                    if (
                        resp.status == OrderStatus.Filled
                        or resp.status == OrderStatus.Canceled
                        or resp.status == OrderStatus.Rejected
                    ):
                        del self.order_book[order_id]
                        logger.info(f"Order {order_id} has been filled or canceled.")

                except OpenApiException as e:
                    logger.info(f"Error checking order {order_id}: {e}")
                    continue

            # Sleep for a while before checking again
            # logger.info(f"check_order_status alive {len(self.order_book)}")
            time.sleep(2)

    def submit_order(self, stock_id, price, amount, order_side):
        """Submit an order to the order book."""
        try:
            logger.info(f"Submitting order: {stock_id}, {price}, {amount}, {order_side}")
            resp = self.trade_ctx.submit_order(
                stock_id,
                OrderType.LO,
                order_side,
                Decimal(amount),
                TimeInForceType.Day,
                submitted_price=Decimal(price),
                remark="Hello from Python SDK",
            )

            detail = self.trade_ctx.order_detail(
                order_id=resp.order_id,
            )
            self.order_book[resp.order_id] = detail
            return resp.order_id
        except OpenApiException as e:
            logger.info("submit buy order error")
            logger.info(e)

    def cancel_order(self, order_id):
        """Cancel an order in the order book."""
        try:
            order = self.order_book.get(order_id)
            if order:
                resp = self.trade_ctx.cancel_order(order.order_id)
                if resp.status == OrderStatus.Canceled:
                    del self.order_book[order.order_id]
                    logger.info(f"Order {order.order_id} canceled successfully.")
                else:
                    logger.info(f"Failed to cancel order {order.order_id}.")
            else:
                logger.info(f"Order {order_id} not found in the order book.")
        except OpenApiException as e:
            logger.info(f"Error canceling order {order_id}: {e}")

    # 这个要改成stock id是否存在
    def check_stockid(self, stock_id):
        # 检查订单是否存在且未成交
        for order_id in self.order_book:
            detail = self.order_book[order_id]
            if detail.symbol in stock_id:
                logger.info(f"Order {order_id} is valid for stock {stock_id}.")
                if (
                    detail.status == OrderStatus.New
                    or detail.status == OrderStatus.WaitToNew
                ):
                    logger.info(f"Order {order_id} is already New.")
                    return order_id
                elif detail.status in [
                    OrderStatus.Canceled,
                    OrderStatus.Rejected,
                ]:
                    logger.info(f"Order {order_id} is canceled or rejected.")
                    del self.order_book[order_id]
                    return None

        logger.info(f"{stock_id} Order does not exist.")
        return None

    def submit(self, stock_id, price, amount, order_side, order_id=None):
        order_id = self.check_stockid(stock_id)
        if order_id is not None:
            logger.info(f"Order {order_id} is valid, proceeding with replacement.")
            self.cancel_order(order_id)
            order_id = self.submit_order(stock_id, price, amount, order_side)
        else:
            logger.info(f"Order is None, submitting a new order.")
            order_id = self.submit_order(stock_id, price, amount, order_side)

        return order_id


oder_book = OrderBook()
