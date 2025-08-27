import logging
import os

from typing import Dict
from logging.handlers import TimedRotatingFileHandler


class logger:
    def __init__(self, name: str = "default", log_path: str = "./LOG") -> None:
        global logger
        logger = logging.getLogger(name)
        # 初始化log
        logger.setLevel(logging.INFO)

        # 创建一个handler，用于写入日志文件，每天一个文件，保留30天
        log_path = os.path.join(log_path, name + ".log")
        handler = TimedRotatingFileHandler(
            log_path, when="D", interval=1, backupCount=30
        )
        handler.setLevel(logging.INFO)

        # 创建一个输出格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # 添加handler到logger
        logger.addHandler(handler)

    @staticmethod
    def info(msg: str) -> None:
        """Log an info message."""
        logger.info(msg)

    @staticmethod
    def error(msg: str) -> None:
        """Log an info message."""
        logger.error(msg)
