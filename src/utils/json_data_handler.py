import atexit
import os
import json

from .logger import log_message

DATA_FILE_PATH = "temp.json"
COLLECTION = {}

def read_data():
    """从 JSON 文件中读取数据。"""
    global COLLECTION
    try:
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            COLLECTION = json.load(f)
    except FileNotFoundError:
        COLLECTION = {}
    except Exception as e:
        log_message(f"read_data Error: {e}", level="error")
    return COLLECTION

def write_data():
    """将数据写回 JSON 文件。"""
    if not COLLECTION:
        return
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(COLLECTION, f, ensure_ascii=False, indent=4)

atexit.register(write_data)

def set_data_file_path(path):
    """设置数据文件的路径。"""
    if not path:
        log_message("Error: Invalid file path. Please provide a JSON file path.", level="error")
        return
    if not path.endswith('.json'):
        log_message("Error: Invalid file format. Please provide a JSON file.", level="error")
        return
    
    write_data()
    global DATA_FILE_PATH
    DATA_FILE_PATH = path
    os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
    read_data()
    return

def get_from_dict(data_dict, map_list):
    """使用 map_list 从 data_dict 中获取值。如果路径不存在，则创建它。"""
    for k in map_list[:-1]:
        data_dict = data_dict.setdefault(k, {})
    return data_dict, map_list[-1]

def set_value(data, *args):
    """
    将数据写入 JSON 文件中的指定路径
    例如: `set_value(10, "user", "points")` 将在 `collection.json` 中创建以下结构：
    {
        "user": {
            "points": 10
        }
    }
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    data_dict[last_key] = data

def increment_value(data, *args):
    """
    将数据增加到 JSON 文件中的指定路径
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    data_dict[last_key] = data_dict.get(last_key, 0) + data

def decrement_value(data, *args):
    """
    将数据减少到 JSON 文件中的指定路径
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    data_dict[last_key] = data_dict.get(last_key, 0) - data

def multiply_value(data, *args):
    """
    将数据乘以 JSON 文件中的指定路径。
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    data_dict[last_key] = data_dict.get(last_key, 0) * data

def divide_value(data, *args):
    """
    将数据除以 JSON 文件中的指定路径。
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    try:
        data_dict[last_key] = data_dict.get(last_key, 0) / data
    except ZeroDivisionError:
        log_message("Error: Division by zero.", level="error")

def delete_key(*args):
    """
    从 JSON 文件中的指定路径删除键。
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    if last_key in data_dict:
        del data_dict[last_key]

def path_exists(*args):
    """
    检查 JSON 文件中是否存在指定路径。
    """
    data_dict, last_key = get_from_dict(COLLECTION, args)
    return last_key in data_dict
