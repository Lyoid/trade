import logging
import os

from typing import Dict
from logging.handlers import TimedRotatingFileHandler
from config import config


class LoggerUtil:
    @staticmethod
    def get_logger(name=None):
        log_dir = config["log_path"]

        """获取logger对象（带文件和控制台输出）"""
        logger = logging.getLogger(name if name else __name__)
        logger.setLevel(logging.DEBUG)

        # 避免重复添加处理器
        if not logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # 创建文件处理器（日志目录自动创建）
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                f"{log_dir}/{config['log_name']}.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)

            # 定义格式化器
            formatter = logging.Formatter(
                "%(asctime)s - %(pathname)s:%(lineno)d - %(funcName)s() - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            # 添加处理器
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        return logger


logger = LoggerUtil.get_logger()
