import inspect
import queue
import logging
import threading

from datetime import datetime

from tencentcloud.common import credential,common_client

from amiyabot import Message

from ..cls import cls_pb2

class TencentClsHandler(logging.Handler):
    plugin_instance = None

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.log_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def emit(self, record):
        # 确定时间戳
        record.timestamp = datetime.now().timestamp()
        # 入队
        self.log_queue.put(record)
        # 检查工作线程状态，如有必要重启
        if not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._worker)
            self.worker_thread.daemon = True
            self.worker_thread.start()

    def _worker(self):
        while True:
            try:
                record = self.log_queue.get()
                if record is None:
                    break
                # 处理日志上传
                data = get_frame_data(record)
                upload_log(self, record, data)
            except Exception as e:
                # 处理可能的异常
                pass

    def close(self):
        self.log_queue.put(None)
        self.worker_thread.join()
        super(TencentClsHandler, self).close()

    def get_config(self, key):
        if self.plugin_instance:
            return self.plugin_instance.get_config(key)
        return None

def get_frame_data(record):
    try:
        extra = getattr(record, 'extra', {})

        channel_id = ""
        user_id = ""
        app_id = ""

        if extra.get("message_data", None) and isinstance(extra["message_data"], Message):
            message_data : Message = extra["message_data"]
            channel_id = message_data.channel_id
            user_id = message_data.user_id
            app_id = message_data.instance.appid
            debug_print('Channel 1')
        else:
            channel_id = extra.get("channel_id", "")
            user_id = extra.get("user_id", "")
            app_id = extra.get("app_id", "")
            if not channel_id and not user_id and not app_id:
                # inspect
                message_data = find_caller_with_message()
                if message_data:
                    channel_id = message_data.channel_id
                    user_id = message_data.user_id
                    app_id = message_data.instance.appid
                    debug_print('channel 4: channel_id: ' + channel_id + ' user_id: ' + user_id + ' app_id: ' + app_id)
                else:                    
                    debug_print('channel 3')
            else:
                debug_print('channel 2: channel_id: ' + channel_id + ' user_id: ' + user_id + ' app_id: ' + app_id)
    
        return channel_id, user_id, app_id
    except Exception as e:
        debug_print(f"Error while getting frame data: {e}")
        return None, None, None

def debug_print(str_message):
    # print(str_message)
    ...

def find_caller_with_message():
    frame = inspect.currentframe()

    while frame:
        # 获取当前帧的局部变量和参数
        debug_print("frame co_name " + frame.f_code.co_name + " frame f_back " + str(frame.f_back))
        local_vars = frame.f_locals
        args, _, _, local_vars = inspect.getargvalues(frame)

        # 在参数中查找Message实例
        for arg in args:
            if isinstance(local_vars[arg], Message):
                return local_vars[arg]

        frame = frame.f_back

    return None

def upload_log(handler,record,data):
    try:
        # debug_print("uploading log")
        # 提取 message 和 extra
        message = record.msg
        log_level = logging.getLevelName(record.levelno)
        
        region = handler.get_config("region")
        secret_id = handler.get_config("secret_id")
        secret_key = handler.get_config("secret_key")
        topic_id = handler.get_config("topic_id")

        # print(f"region: {region}, secret_id: {secret_id}, secret_key: {secret_key}, topic_id: {topic_id}")
        if not region or not secret_id or not secret_key or not topic_id:
            return

        channel_id, user_id, app_id = data

        log_items = [
            {
                "level": log_level,
                "channel_id": channel_id,
                "user_id": user_id,
                "app_id": app_id,
                "content": message
            }
        ]

        cred = credential.Credential(secret_id, secret_key) 
        client = common_client.CommonClient("cls", '2020-10-16', cred, region)

        headers = {
            "X-CLS-TopicId": topic_id
        }

        log = cls_pb2.Log()
        log.time = int(record.timestamp)

        for item in log_items:
            for key in item.keys():
                content = log.contents.add()
                content.key = key
                content.value = item[key]

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
        debug_print(resp)
    except Exception as e:
        print(f"Error while uploading log: {e}")
        return None