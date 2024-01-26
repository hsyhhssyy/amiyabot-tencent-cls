import os

from core import AmiyaBotPluginInstance

from .src.logger.handler import TencentClsHandler

from amiyabot import Message,log
from amiyabot.log.manager import LoggerManager

curr_dir = os.path.dirname(__file__)

class TencentClsLoggerPluginInstance(AmiyaBotPluginInstance):
    def install(self):
        pass
    def load(self):
        pass

bot = TencentClsLoggerPluginInstance(
    name='腾讯云Cls日志',
    version='1.0',
    plugin_id='amiyabot-tencent-cls',
    plugin_type='',
    description='TencentClsLogger',
    document=f'{curr_dir}/README.md',
    global_config_default=f'{curr_dir}/global_config_default.json',
    global_config_schema=f'{curr_dir}/global_config_schema.json',
)

TencentClsHandler.plugin_instance = bot

handler = TencentClsHandler()

LoggerManager.add_handler(handler)

print("LogHandler installed")