import logging
import os
import time

LOGGER = None

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)
        self.last_log_time = None
        self.last_name = ""
        self.last_levelname = ""
        self.original_fmt = fmt
        self.simple_fmt = "%(message)s"

    def format(self, record):
        current_log_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(record.created))
        if (current_log_time == self.last_log_time and
            record.levelname == self.last_levelname and
            record.name == self.last_name):
            self._style._fmt = self.simple_fmt
        else:
            self._style._fmt = self.original_fmt
            self.last_log_time = current_log_time
            self.last_name = record.name
            self.last_levelname = record.levelname
        return super().format(record)

def setup_logging():
    """
    设置日志记录器
    
    后续可以使用 `log_message` 函数记录日志
    """
    global LOGGER
    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    
    LOGGER = logging.getLogger("qiandao")
    LOGGER.setLevel(logging.INFO)

    # 创建一个handler, 用于写入日志文件, 注意文件路径的修改
    handler = logging.FileHandler(os.path.join(logs_directory, "qiandao.log"), encoding="utf-8")
    
    # 创建一个handler, 用于将日志输出到控制台
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    # 设置日志格式
    full_format = '%(asctime)s - %(name)s - %(levelname)s:\n%(message)s'
    date_format = "%Y-%m-%d %H:%M:%S"
    custom_formatter = CustomFormatter(full_format, date_format)
    handler.setFormatter(custom_formatter)
    console.setFormatter(custom_formatter)

    # 添加handler到logger
    LOGGER.addHandler(handler)
    LOGGER.addHandler(console)

    return LOGGER

def log_message(*args, level="info"):
    """
    Logs a message using `logger` if logger is set, otherwise uses print.
    
    Accepts any number of positional arguments, which are converted to a single
    message string, mimicking the behavior of the built-in print function.
    """
    # Convert all arguments to strings (if they are not already) and join them with a space
    message = ' '.join(str(arg) for arg in args)
    
    if LOGGER is not None:
        if level == "info":
            LOGGER.info(message)
        elif level == "debug":
            LOGGER.debug(message)
        elif level == "warning":
            LOGGER.warning(message)
        elif level == "error":
            LOGGER.error(message)
    else:
        print(message)
    return
