from datetime import datetime
from longport.openapi import OrderStatus
import time
from dataloader.LongPortOnline import LongPortOnline
from log import logger
from orderbook.OrderBook import OrderBook
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


class RiskManager:
    """A base class for risk management strategies."""

    def __init__(self, config) -> None:
        self.config = config
        self.data = LongPortOnline(config)
        logger.info(f"RiskManager initialized")

    def Run(self) -> None:
        """Run the risk management strategy."""
        raise NotImplementedError("Subclasses should implement this method.")
