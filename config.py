from log import logger
from typing import Dict
import yaml


class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class Config(Borg):
    def __init__(self, config_path: str = "") -> None:
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print('"Config" instance already exists, returning existing instance.')
        else:
            # 如果没有实例存在，则初始化
            print("initiate the first instance with default state.")
            super().__init__()
            # 读取yaml配置文件
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            print("读取到的配置:", config)
            self.config = config


config = Config(config_path="./config.yaml").config
