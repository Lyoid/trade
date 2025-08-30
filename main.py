from datetime import datetime
import time
from dataloader.LongPortOnline import LongPortOnline
import sys
from log import logger
from online_trader.strategy.TraderSelect import SelectStrategy
from online_trader.orderbook.OrderBook import OrderBook
from config import config


if __name__ == "__main__":

    data = LongPortOnline()
    order_book = OrderBook()
    strategy = SelectStrategy(config["strategy"]["name"])()

    # # 初始化data类
    # data.get_last_trade_price(datetime(2025, 5, 1), stock_id)

    while True:
        logger.info("==========================")

        order_list = strategy.Run()
        
        if order_list is None or order_list is []:
            continue

        for order in order_list:
            logger.info(
                f"Strategy returned Stock: {order['stock_id']}, Price: {order['price']}, Amount: {order['amount']}, Order Side: {order['order_side']}"
            )

            if order['order_side'] is not None:
                order_book.submit(
                    order['stock_id'],
                    order['price'],
                    order['amount'],
                    order['order_side'],
                )

        time.sleep(10)
        logger.info("==========================")
