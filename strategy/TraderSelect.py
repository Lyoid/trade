from strategy.StrategySelfBase import StrategySelfBase
from strategy.MACD import MACD
from typing import Dict, Protocol, Type


def SelectStrategy(trade_name: str):
    """Factory"""
    localizers: Dict[str, Type[StrategySelfBase]] = {
        "MACD": MACD,
    }

    return localizers[trade_name]
