import argparse
import time

from config import config
from dataloader.LongPortOnline import LongPortOnline
from log import logger
from online_trader.strategy.TraderSelect import SelectStrategy
from tools.Scheduler import get_scheduler_config, wait_until_next

ORDER_STRATEGIES = frozenset({"NetTrader", "MACD"})


def run_strategy_once(strategy, order_book) -> None:
    logger.info("==========================")
    order_list = strategy.Run()

    if not order_list:
        return

    for order in order_list:
        logger.info(
            f"Strategy returned Stock: {order['stock_id']}, Price: {order['price']}, "
            f"Amount: {order['amount']}, Order Side: {order['order_side']}"
        )
        if order_book is None:
            continue
        if order.get("order_side") is not None:
            order_book.submit(
                order["stock_id"],
                order["price"],
                order["amount"],
                order["order_side"],
            )
    logger.info("==========================")


def main() -> None:
    parser = argparse.ArgumentParser(description="Trade online strategy runner")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan immediately and exit (for cron / launchd)",
    )
    args = parser.parse_args()

    sched = get_scheduler_config(config)
    strategy_name = config["strategy"]["name"]
    strategy = SelectStrategy(strategy_name)()

    order_book = None
    if strategy_name in ORDER_STRATEGIES:
        from online_trader.orderbook.OrderBook import OrderBook

        LongPortOnline()
        order_book = OrderBook()

    if args.once:
        logger.info("Single run (--once)")
        run_strategy_once(strategy, order_book)
        return

    if sched["enabled"] and sched["mode"] == "daily":
        logger.info(
            f"Daily scheduler on: {sched['run_times']} ({sched['timezone']})"
        )
        while True:
            wait_until_next(
                sched["run_times"],
                sched["timezone"],
                logger,
            )
            run_strategy_once(strategy, order_book)
        return

    # Default: continuous polling (NetTrader / legacy MACD loop)
    if strategy_name not in ORDER_STRATEGIES:
        LongPortOnline()

    logger.info("Continuous mode (poll every 10s)")
    while True:
        run_strategy_once(strategy, order_book)
        time.sleep(10)


if __name__ == "__main__":
    main()
