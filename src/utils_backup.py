import datetime
import math
import gzip
import logging
import os
import time
import zlib

from io import BytesIO

import brotli

logger = None

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
    global logger
    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    
    logger = logging.getLogger("qiandao")
    logger.setLevel(logging.INFO)

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
    logger.addHandler(handler)
    logger.addHandler(console)

    return logger

def log_message(*args, level="info"):
    """
    Logs a message using `logger` if logger is set, otherwise uses print.
    
    Accepts any number of positional arguments, which are converted to a single
    message string, mimicking the behavior of the built-in print function.
    """
    # Convert all arguments to strings (if they are not already) and join them with a space
    message = ' '.join(str(arg) for arg in args)
    
    if logger is not None:
        if level == "info":
            logger.info(message)
        elif level == "debug":
            logger.debug(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
    else:
        print(message)
    return

def save_string_as_file(input_str: str, prefix: str=None, folder: str=None, encoding="utf-8"):
    """
    将字符串保存到文件中
    
    :param input_str: 要保存的字符串
    :param prefix: 文件名前缀
    :param folder: 文件夹名称
    :param encoding: 文件编码
    """
    # 获取当前的日期和时间
    current_time = datetime.datetime.now()
    # 格式化日期时间格式为年-月-日-时.分.秒
    formatted_time = current_time.strftime("%y_%m_%d-%H-%M-%S")

    # 如果提供了前缀, 则在文件名中加入前缀并检查/创建对应的文件夹
    if prefix:
        # 更新文件名为包含文件夹路径的完整路径
        file_name = f"{prefix}_{formatted_time}.txt"
    else:
        file_name = f"{formatted_time}.txt"
        
    # 如果提供了文件夹名称, 则在文件名中加入文件夹名称并检查/创建对应的文件夹
    if folder:
        # 检查是否存在这个文件夹, 如果不存在, 则创建
        if not os.path.exists(folder):
            os.makedirs(folder)
        # 更新文件名为包含文件夹路径的完整路径
        file_name = os.path.join(folder, file_name)
    
    # 检查文件是否已存在，如果是，则在写入新内容之前添加分隔符
    separator = "\n\n------------------------------------\n\n"
    mode = "a" if os.path.exists(file_name) else "w"
    
    with open(file_name, mode, encoding=encoding) as file:
        if mode == "a":  # 文件已存在，追加模式下先写入分隔符
            file.write(separator)
        file.write(input_str)
    
    log_message(f"文件已保存为: {file_name}")

def contains_keywords(text: str, keywords: list[str]=None) -> bool:
    """
    Function to check if the given text contains any of the specified keywords.
    Returns True if any keyword is found, otherwise False.

    :param text: The text to search for keywords.
    :param keywords: A list of keywords (string) to search for in the text.
    """
    if keywords is None:
        keywords = []
    return any(keyword in text for keyword in keywords)

def compute_remaining_time(max_value: float, rate_per_minute: float):
    """计算到达最大值的时间

    参数:
    max_value (float): 需要达到的目标最大值。
    rate_per_minute (float): 每分钟增加的数值。

    返回:
    int: 达到最大值所需的总分钟数。如果rate_per_minute为0, 则返回 0。
    """
    if rate_per_minute <= 0:
        return 0
    
    remaining_time = max_value / rate_per_minute
    return math.ceil(remaining_time)

def compute_time_to_next_integer(begin_minutes: int, rate_per_minute: float):
    """计算达到下一个整数值所需的剩余时间

    参数:
    begin_minutes (int): 起始分钟数。
    rate_per_minute (float): 每分钟的增长率。

    返回:
    next_int_minutes (int): 达到下一个整数值所需的剩余时间（分钟数）。
    """
    if rate_per_minute <= 0 or begin_minutes < 0:
        # 如果每分钟增长率为0或负数 或 起始分钟数为负数，则无法达到下一个整数值
        return 0
    
    if begin_minutes == 0:
        return math.ceil(1 / rate_per_minute)
    
    # 计算当前值与下一个整数值之间的差值
    current_value = begin_minutes * rate_per_minute
    next_int_value = math.ceil(current_value)
    difference = next_int_value - current_value

    # 计算达到下一个整数值所需的剩余时间
    return math.ceil(difference / rate_per_minute)


def calculate_total_minutes(minutes: int, hours=0, days=0):
    """计算总时间"""
    return minutes + hours * 60 + days * 24 * 60

def format_remaining_time(total_minutes: int):
    """
    格式化剩余时间为字符串 "{days} 天 {hours} 小时 {minutes} 分钟"
    """
    if total_minutes <= 0:
        return "0 分钟"
    
    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60

    formatted_time = ""  # 初始化空字符串

    if days > 0:
        formatted_time += f"{days} 天 "
    if hours > 0 or days > 0:  # 如果有天数，即使小时数为0也显示
        formatted_time += f"{hours} 小时 "
    formatted_time += f"{minutes} 分钟"  # 分钟数总是显示

    return formatted_time.strip()  # 返回字符串，移除尾部可能的多余空格

def decompress_response(response_content: str):
    """
    尝试使用gzip, deflate, 或Brotli解压响应内容。
    返回解压缩的数据或原始数据（如果所有方法都失败）。
    """
    try:
        # 尝试使用gzip解压
        with gzip.GzipFile(fileobj=BytesIO(response_content),
                           mode='rb') as gzip_file:
            return gzip_file.read()
    except:
        try:
            # 尝试使用deflate解压
            return zlib.decompress(response_content, -zlib.MAX_WBITS)
        except:
            try:
                # 尝试使用Brotli解压
                return brotli.decompress(response_content)
            except:
                # log_message("无法解压响应内容")
                pass
                
    return response_content # 如果所有方法都失败, 返回原始数据

