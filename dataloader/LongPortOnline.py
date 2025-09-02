from datetime import datetime, timedelta
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
import pandas as pd
from decimal import Decimal
import time
from log import logger
from config import config
from typing import Dict
from tools.TimeCheck import TimeCheck
import re


class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class LongPortOnline(Borg):
    def __init__(self) -> None:
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print(
                '"LongPortOnline" instance already exists, returning existing instance.'
            )
        else:
            # 如果没有实例存在，则初始化
            print("initiate the first instance with default state.")
            super().__init__()
            cfg = Config(
                app_key=config["longport"]["app_key"],
                app_secret=config["longport"]["app_secret"],
                access_token=config["longport"]["access_token"],
                enable_overnight=True,
            )
            self.trade_ctx = TradeContext(cfg)
            self.quote_ctx = QuoteContext(cfg)

            # 账户信息
            self.account_balance = self.trade_ctx.account_balance()
            # 持仓信息
            self.stock_positions = self.trade_ctx.stock_positions()

            # 历史烛图
            self.history_candlesticks = None
            self.candlestick_amount = config["longport"]["candlestick_amount"]

            # logger.info(self.account_balance)
            # logger.info(self.stock_positions)

    def get_last_trade_price(self, start_date, stock_id):
        last_price = []
        for name in stock_id:
            # 先找当日成交记录
            try:
                resp = self.trade_ctx.today_executions(symbol=name)
                if resp:
                    last_trader_price = resp[len(resp) - 1].price
                    last_price.append(last_trader_price)
                    continue

                # 再找历史成交记录
                resp = self.trade_ctx.history_executions(
                    # symbol = "700.HK",
                    symbol=name,
                    # start_at = datetime(2022, 5, 9),
                    start_at=start_date,
                    end_at=datetime.today(),
                )
                if resp:
                    last_trader_price = resp[len(resp) - 1].price
                    last_price.append(last_trader_price)
                    continue

                last_price.append(Decimal(0.0))

            except Exception as e:
                logger.error(f"Failed to fetch stock positions: {e}")
                last_price.append(Decimal(0.0))
                continue
        return last_price

    def get_current_price(self, stock_id):
        # resp = ctx.quote(["700.HK", "AAPL.US", "TSLA.US", "NFLX.US"])
        resp = self.quote_ctx.quote(stock_id)
        # logger.info(resp)

        # 检查市场
        market = []
        for name in stock_id:
            market.append(name.split(".")[-1])

        # 返回价格
        prices = []
        is_beijing_market, is_us_market = self.check_market()
        logger.info(
            f"is_beijing_market: {is_beijing_market}, is_us_market: {is_us_market}"
        )
        for index, item in enumerate(resp):
            # logger.info(f"Current price for {item.symbol}: {item.last_done}")
            if market[index] == "HK":
                if is_beijing_market:
                    prices.append(item.last_done)
                else:
                    prices.append(item.last_done)
            elif market[index] == "US":
                if is_us_market == "on_market":
                    prices.append(item.last_done)
                # 周末盘前运行会报错
                elif is_us_market == "pre_market_quote":
                    if item.pre_market_quote is None:
                        logger.info(f"pre_market_quote is None, set to 0")
                        prices.append(0)
                    else:
                        logger.info(f"pre_market_quote: {item.pre_market_quote}")
                        prices.append(item.pre_market_quote.last_done)
                elif is_us_market == "post_market_quote":
                    prices.append(item.post_market_quote.last_done)
                else:
                    prices.append(item.last_done)

        return prices

    def check_stock_positions(self, stock_id):
        while True:
            try:
                self.stock_positions = self.trade_ctx.stock_positions()
            except Exception as e:
                logger.error(f"Failed to fetch stock positions: {e}")
                sleep(2)
                continue

            logger.info(self.stock_positions)
            # 有坑，symbol 前面是不带0的
            for stock_position in self.stock_positions.channels[0].positions:
                print(stock_position.symbol, stock_id)
                if stock_position.symbol in stock_id:
                    if stock_position.quantity > 0:
                        return True

            return False

    def check_market(self):

        # 9:30-16:00​​
        beijing_time = TimeCheck.get_beijing_time()
        us_time = TimeCheck.get_us_time()
        # 判断北京时间是否在9:30-16:00之间
        start = "09:30:00"
        end = "16:00:00"
        beijing_time_str = beijing_time.strftime("%H:%M:%S")
        is_beijing_market = start <= beijing_time_str <= end

        # logger.info(
        #     f"beijing_time: {beijing_time_str}, is_beijing_market: {is_beijing_market}"
        # )

        # 判断美国时间是在盘前还是盘后
        us_time_str = us_time.strftime("%H:%M:%S")
        logger.info(f"us_time: {us_time_str}")
        if "04:00:00" <= us_time_str < "09:30:00":
            logger.info("当前为美股盘前时段")
            is_us_market = "pre_market_quote"
        elif "09:30:00" <= us_time_str < "16:00:00":
            logger.info("当前为美股盘中时段")
            is_us_market = "on_market"
        elif "16:00:00" <= us_time_str < "20:00:00":
            logger.info("当前为美股盘后时段")
            is_us_market = "post_market_quote"
        else:
            logger.info("当前为美股夜盘时段")
            is_us_market = "night_market"
        
            

        return is_beijing_market, is_us_market

    # 单股接口
    def is_trading(self, stock_id):

        # 判断是否在工作日
        is_beijing_workday = TimeCheck.is_hong_kong_workday()
        is_us_workday = TimeCheck.is_us_eastern_workday()
        logger.info(
            f"is_beijing_workday: {is_beijing_workday}, is_us_workday: {is_us_workday}"
        )

        # 补充 symbol_name
        # resp = self.quote_ctx.static_info(stock_id)
        # self.symbol_name = resp[0].name_en
        # logger.info(f"symbol_name {self.symbol_name}")

        # 获取股票所在市场
        market = stock_id.split(".")[-1]
        logger.info(f"market: {market}")

        is_beijing_market, is_us_market = self.check_market()
        
        if market == "HK":
            if is_beijing_market and is_beijing_workday:
                logger.info("当前为港股交易时间")
                return True
            else:
                logger.info("当前为非港股交易时间")
                return False
        elif market == "US":
            if not is_us_workday:
                logger.info("当前为美股节假日")
                return False
            if is_us_market == "on_market":
                logger.info("当前为美股交易时间")
                return True
            elif is_us_market == "pre_market_quote":
                logger.info("当前为美股盘前交易时间")
                # logger.info("盘前市场没有访问权限,价格会返回0")
                return True
            elif is_us_market == "post_market_quote":
                logger.info("当前为美股盘后交易时间")
                return True
            elif is_us_market == "night_market":
                logger.info("当前为美股夜盘交易时间，没有交易权限")
                return False
            else:
                logger.info("当前为非美股交易时间")
                return False
        else:
            logger.info("未知市场")
            return False

    # 查看当前账户信息
    def get_account_balance(self):
        self.account_balance = self.trade_ctx.account_balance()
        logger.info(self.account_balance)
        return self.account_balance

    def get_history_candlesticks(self, stock_id, period=Period.Day):
        """
        获取历史烛图数据
        :param stock_id: 股票代码
        :param period: 烛图周期
        :return: 历史烛图数据
        """
        candlesticks = []
        for name in stock_id:
            try:
                candlestick = self.quote_ctx.candlesticks(
                    name,
                    period,
                    self.candlestick_amount,
                    AdjustType.ForwardAdjust,
                )
                candlesticks.append(candlestick)
            except OpenApiException as e:
                logger.error(f"Error fetching candlestick data: {e}")
                logger.info(f"stock: {name}")
                candlesticks.append(None)

        return candlesticks

    # 退市、停牌、非市场内股、期权、牛证过滤
    def watchlists_by_symbol(self):
        symbol_lists = []
        resp = self.quote_ctx.watchlist()
        for group in resp:
            if len(group.securities):
                for stock in group.securities:
                    if stock.symbol.split(".")[-1] not in ["HK","US"]:
                        continue
                    symbol_lists.append(stock.symbol)
        logger.info(f"symbol_lists: {symbol_lists}")
        return list(set(symbol_lists))

    # 多股接口
    def is_tradings(self):
        #节假日判断
        is_us_eastern_workday = TimeCheck.is_us_eastern_workday()
        is_hong_kong_workday = TimeCheck.is_hong_kong_workday()

        logger.info(f"is_us_eastern_workday: {is_us_eastern_workday}, is_hong_kong_workday: {is_hong_kong_workday}")

        return (is_us_eastern_workday or is_hong_kong_workday)


dataset = LongPortOnline()
