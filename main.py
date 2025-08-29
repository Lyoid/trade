from datetime import datetime
import time
from dataloader.LongPortOnline import LongPortOnline
import sys
from log import logger
from online_trader.strategy.TraderSelect import SelectStrategy
from online_trader.orderbook.OrderBook import OrderBook
from config import config


if __name__ == "__main__":

    # 配置
    stock_id = config["stock_id"]

    data = LongPortOnline()
    order_book = OrderBook()
    strategy = SelectStrategy(config["strategy"]["name"])()

    # # 初始化data类
    # data.get_last_trade_price(datetime(2025, 5, 1), stock_id)

    while True:
        logger.info("==========================")
        # 查看当前股票是否在交易时间
        if not data.is_trading(stock_id):
            # 待机60秒
            time.sleep(60)
            continue

        price, amount, order_side = strategy.Run()
        logger.info(
            f"Strategy returned - Price: {price}, Amount: {amount}, Order Side: {order_side}"
        )

        if order_side is not None:
            order_book.submit(
                stock_id,
                price,
                amount,
                order_side,
            )

        time.sleep(10)
        logger.info("==========================")
