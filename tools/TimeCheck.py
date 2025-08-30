import pandas as pd
from decimal import Decimal
import time
from log import logger
from config import config
from typing import Dict
from datetime import datetime, timedelta
import pytz
import holidays

last_time = datetime.now()

class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class TimeCheck(Borg):
    def __init__(self) -> None:
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print('"TimeCheck" instance already exists, returning existing instance.')
        else:
            # 如果没有实例存在，则初始化
            print("initiate the first instance with default state.")
            super().__init__()


    # 美股盘前开始/港股盘中结束16：00
    @staticmethod
    def check_next_day() -> bool:
        global last_time
        ''' 如果隔天了'''
        now = datetime.now()
        if now.date() != last_time.date():
            last_time = now
            return True
        """如果当前北京时间大于16点，返回True"""
        now = datetime.utcnow()
        beijing_tz = pytz.timezone("Asia/Shanghai")
        if now.tzinfo is None:
            now = pytz.utc.localize(now).astimezone(beijing_tz)
        else:
            now = now.astimezone(beijing_tz)
        return now.hour >= 16

    @staticmethod
    def get_us_time() -> datetime:
        """获取当前的美国时间"""

       # 获取当前UTC时间
        utc_now = datetime.now(pytz.utc)
        # 转换为美国东部时间（考虑夏令时）
        eastern = pytz.timezone('US/Eastern')
        eastern_now = utc_now.astimezone(eastern)
        logger.info(f"U.S. Eastern Time: {eastern_now}")

        # # Convert to U.S. Pacific Time
        # pacific_tz = pytz.timezone("US/Pacific")
        # pacific_time = utc_time.astimezone(pacific_tz)
        # print("U.S. Pacific Time:", pacific_time)

        return eastern_now

    @staticmethod
    def get_beijing_time() -> datetime:
        """获取当前的北京时间"""

        # Create a naive datetime (no timezone)
        naive_time = datetime.utcnow()

        # Localize the naive datetime to UTC
        utc_time = pytz.utc.localize(naive_time)
        # logger.info(f"UTC Time: {utc_time}")

        # Convert to Beijing Time
        beijing_tz = pytz.timezone("Asia/Shanghai")
        beijing_time = utc_time.astimezone(beijing_tz)
        # logger.info(f"Beijing Time: {beijing_time}")

        return beijing_time

    @staticmethod
    def is_us_holiday():
        """判断当前美国东部时间是否为法定节假日"""
        # 获取当前UTC时间
        utc_now = datetime.now(pytz.utc)
        # 转换为美国东部时间（考虑夏令时）
        eastern = pytz.timezone('US/Eastern')
        eastern_now = utc_now.astimezone(eastern)
        # 获取美国联邦节假日（2025年）
        us_holidays = holidays.US(years=eastern_now.year)
        # 判断是否为节假日（包含观察日期，如元旦若在周末则顺延至周一）
        return eastern_now.date() in us_holidays

    @staticmethod
    def is_hong_kong_holiday():
        """判断当前香港时间是否为公众假期或法定假日"""
        # 获取当前UTC时间
        utc_now = datetime.now(pytz.utc)
        # 转换为香港时间
        hong_kong = pytz.timezone('Asia/Hong_Kong')
        hong_kong_now = utc_now.astimezone(hong_kong)
        # 获取香港公众假期（2025年，包含法定假日）
        hk_holidays = holidays.HongKong(years=hong_kong_now.year)
        # 判断是否为公众假期（包含法定假日）
        return hong_kong_now.date() in hk_holidays


    @staticmethod
    def is_us_eastern_workday():
        """判断当前美国东部时间是否为工作日（排除周末及法定节假日）"""
        # 获取当前UTC时间
        utc_now = datetime.now(pytz.utc)
        # 转换为美国东部时间（自动处理夏令时）
        eastern = pytz.timezone('US/Eastern')
        eastern_now = utc_now.astimezone(eastern)
        # 获取美国联邦法定节假日（2025年）
        us_holidays = holidays.US(years=eastern_now.year)
        # 判断是否为周末（5=周六，6=周日）或法定节假日
        return eastern_now.weekday() < 5 and eastern_now.date() not in us_holidays

    @staticmethod
    def is_hong_kong_workday():
        """判断当前香港时间是否为工作日（排除周末及法定假日）"""
        # 获取当前UTC时间
        utc_now = datetime.now(pytz.utc)
        # 转换为香港时间
        hong_kong = pytz.timezone('Asia/Hong_Kong')
        hong_kong_now = utc_now.astimezone(hong_kong)
        # 获取香港公众假期（含法定假日，2025年）
        hk_holidays = holidays.HongKong(years=hong_kong_now.year)
        # 判断是否为周末（5=周六，6=周日）或法定假日
        return hong_kong_now.weekday() < 5 and hong_kong_now.date() not in hk_holidays


timecheck = TimeCheck()
