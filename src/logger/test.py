import inspect

class Message:
    def __init__(self):
        self.channel_id = ""
        self.user_id = ""

def find_caller_with_message():
    frame = inspect.currentframe()

    while frame:
        # 获取当前帧的局部变量和参数
        local_vars = frame.f_locals
        args, _, _, local_vars = inspect.getargvalues(frame)

        # 在参数中查找Message实例
        for arg in args:
            if isinstance(local_vars[arg], Message):
                return local_vars[arg]

        frame = frame.f_back

    return None

def func(data):
    call_in()

def call_in():
    print(find_caller_with_message().channel_id)

if __name__ == "__main__":
    msg = Message()
    msg.channel_id = "123"
    msg.user_id = "456"
    func(data=msg)