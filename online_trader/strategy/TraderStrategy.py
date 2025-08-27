from typing import Dict, Protocol, Type
import yaml


class TraderStrategy(Protocol):
    """A base class for trader strategies."""

    config: Dict[str, str] = {}

    def __init__(self) -> None:
        pass

    def next(self) -> None:
        pass
