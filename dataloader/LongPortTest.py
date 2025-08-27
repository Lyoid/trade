import backtrader as bt
import datetime
from longport.openapi import (
    QuoteContext,
    Config,
    SubType,
    PushQuote,
    Period,
    AdjustType,
    TradeContext,
)
import pandas as pd
from config import config


class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class LongPortTest(Borg):
    """
    从longport读取香港股票数据日线
    """

    def __init__(self, isplot=True):
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print(
                '"LongPortTest" instance already exists, returning existing instance.'
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
            self.isplot = isplot
            self.data = []

    # 从longport在线读取数据
    def fetch_data(self, stock_ids, start_time=None, end_time=None):

        dt_start_time = datetime.datetime.strptime(start_time, "%Y%m%d")
        dt_end_time = datetime.datetime.strptime(end_time, "%Y%m%d")

        # 前7列必须是 ['open','high', 'low', 'close','volume', 'openinterest']
        columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "openinterest",
            "datetime",
            "name",
        ]

        self.dfs = []
        stock_ids = stock_ids.split(",")
        for i in stock_ids:
            print(i)
        for stock_id in stock_ids:
            data_dict = {col: [] for col in columns}

            try:
                # 加载数据
                candlesticks = self.quote_ctx.history_candlesticks_by_date(
                    stock_id,
                    Period.Day,
                    AdjustType.NoAdjust,
                    dt_start_time,
                    dt_end_time,
                )
                for row in candlesticks:
                    data_dict["open"].append(float(row.open))
                    data_dict["high"].append(float(row.high))
                    data_dict["low"].append(float(row.low))
                    data_dict["close"].append(float(row.close))
                    data_dict["volume"].append(float(row.volume))
                    data_dict["openinterest"].append(0)
                    data_dict["datetime"].append(row.timestamp.date())
                    data_dict["name"].append(stock_id)

                df = pd.DataFrame(data_dict)

                # 将日期列，设置成index
                df.index = pd.to_datetime(df.datetime, format="%Y%m%d")
                # 时间必须递增
                df = df.sort_index()

                self.data.append(
                    bt.feeds.PandasData(
                        name=df["name"][0],
                        dataname=df,
                        fromdate=dt_start_time,
                        todate=dt_end_time,
                        plot=self.isplot,
                    )
                )

                print(df)
                self.dfs.append(df)

            except Exception as err:
                print("下载{0}完毕失败！")
                print("失败原因 = " + str(err))

        return self.data, self.dfs

    def get_history_candlesticks(stock_id, period=Period.Day):
        """
        获取历史烛图数据
        :param stock_id: 股票代码
        :param period: 烛图周期
        :return: 历史烛图数据
        """
        return []

    def get_last_day_close(self, stock_id, day=None):
        """
        获取最后一个交易日的收盘价
        :param stock_id: 股票代码
        :return: 最后一个交易日的收盘价
        """
        if day is None or day < 1:
            return None

        return self.dfs[0]["close"][day - 1]


dataset = LongPortTest()
