import pandas as pd
from decimal import Decimal
import time
from log import logger
from config import config
from typing import Dict
from datetime import datetime, timedelta
import pytz

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

        # Get current UTC time as a naive datetime
        naive_utc_time = datetime.utcnow()

        # Localize the naive UTC datetime to UTC
        utc_time = pytz.utc.localize(naive_utc_time)
        logger.info(f"UTC Time: {utc_time}")

        # Convert to U.S. Eastern Time
        eastern_tz = pytz.timezone("US/Eastern")
        eastern_time = utc_time.astimezone(eastern_tz)
        logger.info(f"U.S. Eastern Time: {eastern_time}")

        # # Convert to U.S. Pacific Time
        # pacific_tz = pytz.timezone("US/Pacific")
        # pacific_time = utc_time.astimezone(pacific_tz)
        # print("U.S. Pacific Time:", pacific_time)

        return eastern_time

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


timecheck = TimeCheck()
