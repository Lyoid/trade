from online_trader.strategy.TraderStrategy import TraderStrategy
from online_trader.strategy.NetTrader import NetTrader
from online_trader.strategy.MACD import MACD
from typing import Dict, Protocol, Type


def SelectStrategy(trade_name: str):
    """Factory"""
    localizers: Dict[str, Type[TraderStrategy]] = {
        "NetTrader": NetTrader,
        "MACD": MACD,
    }

    return localizers[trade_name]
