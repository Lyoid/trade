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
        static_info = data.get_stock_info(self.stock_ids)
        logger.info(f"static inof {static_info}")
        self.stocks_info = dict(zip(self.stock_ids, data.get_stock_info(self.stock_ids)))
        self.recall = True

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

        if not data.is_tradings():
            logger.info("非交易时间，等待8小时")
            time.sleep(3600*8)
            return None

        for index, stock_id in enumerate(self.stock_ids):
            logger.info(f"Processing stock: {stock_id}")
            # 查看当前股票是否在交易时间
            if not data.is_trading(stock_id):
                self.init_factor(index)
                self.start_call[index] = True
                self.recall = True
                continue

            # 针对美股盘中，再报送一次消息
            if data.is_on_market(stock_id) and self.recall:
                logger.info(f"{stock_id} is in market time")
                self.start_call[index] = True
                self.recall = False

            logger.info("Start macd strategy")
            # 更新数据 
            current_price = data.get_current_price([stock_id])[0]
            # Check if we are in the market
            # 入场条件
            candle = type(
                "Candle",
                (object,),
                {"open": current_price, "close": current_price},
            )()

            result,top_divergence,bottom_divergence = self.macd_factors[index].check(candle)

            if self.start_call[index] == True:
                if top_divergence:
                    self.msg(stock_id, "顶背离发生")

                if bottom_divergence:
                    self.msg(stock_id, "底背离发生")

                if result == 1:
                    logger.info("macd buy")
                    self.msg(stock_id, "买入信号", current_price)
                elif result == 2:
                    logger.info("macd sell")
                    self.msg(stock_id, "卖出信号", current_price)

                self.start_call[index] = False


            self.macd_factors[index].delete_last_candlestick()
            time.sleep(5)
        
        return None

    def msg(self, stock_id, strline, price=None):
        msg = (
            f" id：{stock_id}"
            f" 名字：{self.stocks_info[stock_id].name_cn} {self.stocks_info[stock_id].name_en}"
            f" 状态：{strline}"
            f" 价格：{price if price is not None else data.get_current_price([stock_id])[0]}"
            f" 策略：MACD"
            f" 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        feishu.message(msg)
