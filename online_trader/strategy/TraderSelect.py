from online_trader.strategy.TraderStrategy import TraderStrategy
from online_trader.strategy.NetTrader import NetTrader
from online_trader.strategy.MACD import MACD
from online_trader.strategy.CallMacd import CallMacd
from typing import Dict, Protocol, Type


def SelectStrategy(trade_name: str):
    """Factory"""
    localizers: Dict[str, Type[TraderStrategy]] = {
        "NetTrader": NetTrader,
        "MACD": MACD,
        "CallMacd": CallMacd,
    }

    return localizers[trade_name]
