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

            # 市场
            self.market = None
            self.market_during_time = None

            # 市场时间
            # 9:30-16:00​​
            self.market_time = {
                "US": {
                    "pre_market_quote": {
                        "begin": "16:00:00",
                        "end": "21:30:00",
                    },
                    "on_market": {
                        "begin": "22:30:00",
                        "end": "05:00:00",
                    },
                    "post_market_quote": {
                        "begin": "05:00:00",
                        "end": "09:30:00",
                    },
                },
                "HK": {
                    "on": {
                        "begin": "09:30:00",
                        "end": "16:00:00",
                    }
                },
            }

            self.symbol_name = None
            # 当前价格
            self.current_price = 0.0
            # 上一时刻价格
            self.last_price = 0.0

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
                sleep(2)
                last_price.append(Decimal(0.0))
                continue
        return last_price

    def get_current_price(self, stock_id):
        # resp = ctx.quote(["700.HK", "AAPL.US", "TSLA.US", "NFLX.US"])
        resp = self.quote_ctx.quote(stock_id)
        logger.info(resp)

        # 检查市场
        market = []
        for name in stock_id:
            market.append(name.split(".")[1])

        # 返回价格
        prices = []
        is_beijing_market, is_us_market = self.check_market()
        logger.info(
            f"is_beijing_market: {is_beijing_market}, is_us_market: {is_us_market}"
        )
        for index, item in enumerate(resp):
            logger.info(f"Current price for {item.symbol}: {item.last_done}")
            if market[index] == "HK":
                if is_beijing_market:
                    prices.append(item.last_done)
                else:
                    prices.append(item.last_done)
            elif market[index] == "US":
                if is_us_market == "on_market":
                    prices.append(item.last_done)
                elif is_us_market == "pre_market_quote":
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

    def is_trading(self, stock_ids):

        # 判断是否在工作日
        is_beijing_workday = TimeCheck.is_hong_kong_workday()
        is_us_workday = TimeCheck.is_us_eastern_workday()
        logger.info(
            f"is_beijing_workday: {is_beijing_workday}, is_us_workday: {is_us_workday}"
        )

        # 补充 symbol_name
        resp = self.quote_ctx.static_info(stock_ids)
        # self.symbol_name = resp[0].name_en
        # logger.info(f"symbol_name {self.symbol_name}")

        # 获取股票所在市场
        markets = []
        for stock_id in stock_ids:
            market = stock_id.split(".")[1]
            markets.append(market)
            logger.info(f"market: {market}")

        is_beijing_market, is_us_market = self.check_market()
        for market in markets:
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
                candlesticks.append(None)

        return candlesticks

    # 更新信息
    def update_info(self):
        # # 价格、成交量
        # price = self.get_current_price(stock_id)
        # if price is not self.current_price:
        #     self.last_price = self.current_price
        #     self.current_price = price
        #     logger.info(f"Current price for {stock_id}: {self.current_price}")
        # else:
        #     logger.info(f"No change current price for {stock_id}")

        # 账户信息
        try:
            self.account_balance = self.trade_ctx.account_balance()
            logger.info(f"Account balance: {self.account_balance}")
            # 持仓信息
            self.stock_positions = self.trade_ctx.stock_positions()
            logger.info(f"Stock positions: {self.stock_positions}")
        except Exception as e:
            logger.error(f"Failed to fetch account balance: {e}")

        # # 历史烛图
        # self.history_candlesticks = self.get_history_candlesticks(stock_id)
        # # 历史交易记录
        # self.get_last_trade_price(datetime.today(), stock_id)
        # logger.info(f"Last trader price: {self.last_trader_price}")
        # 市场信息
        # self.check_market(stock_id)
        # logger.info(f"Market: {self.market}")
        # logger.info(f"Market during time: {self.market_during_time}")


dataset = LongPortOnline()
