import json
from config import config

import lark_oapi as lark
from lark_oapi.api.im.v1 import *


# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.


class Borg:
    _shared_state = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class FeiShu(Borg):
    def __init__(self) -> None:
        if self._shared_state:
            # 如果已经有实例存在，则直接返回
            super().__init__()
            print('"FeiShu" instance already exists, returning existing instance.')
        else:
            # 如果没有实例存在，则初始化
            print("initiate the first instance with default state.")
            super().__init__()

            # 创建client
            self.client = (
                lark.Client.builder()
                .app_id(config["feishu"]["app_id"])
                .app_secret(config["feishu"]["app_secret"])
                .log_level(lark.LogLevel.DEBUG)
                .build()
            )

    def message(self, text: str):
        # 构造请求对象
        request: CreateMessageRequest = (
            CreateMessageRequest.builder()
            .receive_id_type("open_id")
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(config["feishu"]["open_id"])
                .msg_type("text")
                .content(f'{{"text":"{text}"}}')
                .build()
            )
            .build()
        )

        # 发起请求
        response: CreateMessageResponse = self.client.im.v1.message.create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))


feishu = FeiShu()
