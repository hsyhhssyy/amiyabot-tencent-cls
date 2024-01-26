import threading
import logging
from typing import Optional

from datetime import datetime

from tencentcloud.common import credential,common_client

import cls_pb2

def upload_log(self,log_level, message, channel_id, user_id):
        endpoint = self.endpoint or TencentClsLogger.endpoint
        secret_id = self.secret_id or TencentClsLogger.secret_id
        secret_key = self.secret_key or TencentClsLogger.secret_key
        topic_id = self.topic_id or TencentClsLogger.topic_id

        if not endpoint or not secret_id or not secret_key or not topic_id:
            return

        log_items = [
            {
                "level": log_level,
                "channel_id": channel_id,
                "user_id": user_id,
                "content": message
            }
        ]

        thread = threading.Thread(target=__upload_log_to_tencent_cls, args=(endpoint, secret_id, secret_key, topic_id, log_items))
        thread.daemon = True
        thread.start()

def __upload_log_to_tencent_cls(endpoint, secret_id, secret_key, topic_id, log_items):
    """
    上传日志到腾讯云日志服务（CLS）。

    :param endpoint: CLS API的终端地址。
    :param secret_id: 腾讯云账户的SecretId。
    :param secret_key: 腾讯云账户的SecretKey。
    :param topic_id: 日志主题的ID。
    :param log_items: 要上传的日志列表，每个日志作为一个字典。
    """
    try:
        cred = credential.Credential(secret_id, secret_key) 
        client = common_client.CommonClient("cls", '2020-10-16', cred, endpoint)

        headers = {
            "X-CLS-TopicId": topic_id
        }

        log = cls_pb2.Log()
        log.time = int(datetime.now().timestamp())

        for item in log_items:
            content = log.contents.add()
            content.key = "level"
            content.value = item["level"]

            content = log.contents.add()
            content.key = "channel_id"
            content.value = str(item["channel_id"])

            content = log.contents.add()
            content.key = "user_id"
            content.value = str(item["user_id"])

            content = log.contents.add()
            content.key = "content"
            content.value = item["content"]

        # 创建LogGroup
        log_group = cls_pb2.LogGroup()
        log_group.logs.extend([log])
        log_group.filename = "running.log"
        log_group.source = "amiya-bot"

        # 创建LogGroupList
        log_group_list = cls_pb2.LogGroupList()
        log_group_list.logGroupList.extend([log_group])

        # 序列化LogGroupList
        serialized_data = log_group_list.SerializeToString()

        resp = client.call_octet_stream("UploadLog", headers, serialized_data)
        print(resp)
    except Exception as e:
        print(f"Error while uploading log: {e}")
        return None
    
# main

if __name__ == "__main__":
    test_logger = TencentClsLogger()

    TencentClsLogger.endpoint = "ap-guangzhou"
    TencentClsLogger.secret_id= "[YourSecretId]"
    TencentClsLogger.secret_key = "[YourSecretKey]"
    TencentClsLogger.topic_id = "8b632c76-4612-452d-8ff0-6df81e2ee4d8"

    test_logger.info("test message", 123, 456)