import datetime
import os

from .logger import log_message

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
