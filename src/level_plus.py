import datetime
import os
import re
import time

import requests
from bs4 import BeautifulSoup

from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file
from .utils.text_analysis import contains_keywords

CURRENT_MONTH = str(datetime.datetime.now().month)

NORTH_PLUS_BASE_URLS = [
    "www.south-plus.net",
    "www.north-plus.net",
    "www.level-plus.net"
] # 不过每个 cookie 只能在对应的站点使用, 并且登录需要 验证码
NORTH_PLUS_BASE_URL = "www.level-plus.net"

level_plus_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
}

def set_cookie():
    cookie_str = os.environ.get("LEVEL_PLUS_COOKIE")
    if not cookie_str:
        log_message("请设置环墶变量 LEVEL_PLUS_COOKIE", level="error")
        return False
    global level_plus_headers
    level_plus_headers["Cookie"] = cookie_str
    return True

def level_plus_tasks_page():
    """
    请求 level-plus 任务页面, 并返回 HTML 内容。
    """
    # 请求的基本 URL
    base_url = f"https://{NORTH_PLUS_BASE_URL}/plugin.php?H_name-tasks.html"
    local_headers = level_plus_headers.copy()
    local_headers["Referer"] = f"https://{NORTH_PLUS_BASE_URL}"

    # 发送 GET 请求
    try:
        response = requests.get(base_url, headers=local_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        log_message(f"level-plus 任务页面请求失败, HTTP Error ({response.status_code}): {e}", level="error")
        return ""
    except requests.RequestException as e:
        log_message(f"level-plus 任务页面请求失败, Request Error: {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"level-plus 任务页面请求失败, Error: {e}", level="error")
        return ""
    
    return response.text

def level_plus_find_verifyhash(html_content: str=None) -> str:
    """
    找到 level-plus 页面中的 verifyhash, 用于领取任务和奖励。

    :param html_content: 表示需要分析的HTML内容。
    :return: 找到的 verifyhash。
    """
    if not html_content:
        html_content = level_plus_tasks_page()

    verifyhash = "a9b1e270" # 默认值 (日期: 2024-03)
    
    # 使用正则表达式查找verifyhash
    match = re.search(r"var\s+verifyhash\s*=\s*'([^']+)'", html_content)
    if match:
        # 如果找到匹配项, 提取verifyhash
        verifyhash = match.group(1)
        log_message(f"找到的 verifyhash 是: {verifyhash}")
    else:
        log_message("verifyhash 页面请求成功, 但未找到 verifyhash", level="error")
        save_string_as_file(html_content, prefix="level_plus_verifyhash_unfind", folder="level_plus")

    return verifyhash

def level_plus_find_task_ids(html_content: str=None, id_range=100):
    """
    用于解析网页 HTML 内容中的特定任务标识符 (id), 以识别和提取任务ID。
    这些标识符是通过特定的JavaScript函数`startjob('id')`调用来引用的。
    
    :param html_content: 表示需要分析的HTML内容。
    :param id_range: 指定搜索ID的范围上限, 默认为30。函数将仅返回在1到id_range (包含) 之间的有效ID。
    :return: 一个`int`列表, 包含在指定范围内找到的所有有效任务ID。
    """
    if not html_content:
        html_content = level_plus_tasks_page()

    # 定义用于匹配 startjob('id'); 的正则表达式
    pattern = re.compile(r"startjob\('(\d+)'\);")
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    startjob_ids = []

    for onclick in soup.find_all('a', onclick=True):
        # if 'startjob' in onclick['onclick']:
        #     # Extract the numeric ID from the onclick attribute
        #     start_id = onclick['onclick'].split("'")[1]  # Split by single quote and get the second item
        #     if start_id.isdigit() and 1 <= int(start_id) <= id_range:
        #         startjob_ids.append(int(start_id))
        
        match = pattern.search(onclick['onclick'])
        if match:
            start_id = match.group(1)  # 提取匹配到的ID
            if start_id.isdigit() and 1 <= int(start_id) <= id_range:
                startjob_ids.append(int(start_id))
            else:
                log_message(f"找到无效的任务 ID: {start_id}", level="warning")

    return startjob_ids

def level_plus_single_task(cid, verifyhash: str, task_name: str=None):
    """
    根据 `cid` 领取并完成 level-plus 的单个任务

    :param cid: 一个整数, 表示任务的标识符
    :param verifyhash: 表示用于验证的哈希
    :param task_name: 表示任务的名称, 用于日志记录

    已知接口参数:

    cid = 1 :   [头像任务]
    cid = 2 :   [会员任务]
    cid = 3 :   [主题帖任务(I)]
    cid = 4 :   [新春快乐~]
    cid = 5 :   [帖子收藏任务]
    cid = 6 :   [好图分享任务]
    cid = 7 :   [帖子签名]
    cid = 8 :   [帖子推荐任务]
    cid = 9 :   [银行任务]
    cid = 10 :  [朋友圈任务]
    cid = 11 :  [论坛宣传推荐任务]
    cid = 12 :  [主题帖任务(II)]
    cid = 13 :  [主题帖任务(III)]
    cid = 14 :  [周常]
    cid = 15 :  [日常]
    cid = 16 :  [免费运气卡]
    cid = 17 :  [魂之绅士升级道具]
    cid = 18 :  [LP归零卡]
    cid = 19 :  [新年红包~]
    cid = 20 :  [⑨卡]
    cid = 21 :  [圣诞快乐~]
    """
    if not task_name:
        task_name = f"cid = {cid}"
        
    keywords = ["是不开放", "还没超过"]

    # 请求的基本 URL
    base_url = f"https://{NORTH_PLUS_BASE_URL}/plugin.php"

    log_message(f"开始 {task_name} 任务")

    # 获取当前时间的时间戳, 用于 nowtime 参数
    nowtime = int(datetime.datetime.now().timestamp() * 1000)

    # 请求参数
    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job",
        "cid": cid,
        "nowtime": nowtime,
        "verify": verifyhash
    }

    local_headers = level_plus_headers.copy()
    local_headers["Referer"] = f"https://{NORTH_PLUS_BASE_URL}/plugin.php?H_name-tasks.html"

    # 发送 GET 请求
    try:
        response = requests.get(base_url, headers=local_headers, params=params)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        log_message(f"领取 {task_name} 任务 失败, HTTP Error ({response.status_code}): {e}")
        return
    except requests.RequestException as e:
        log_message(f"领取 {task_name} 任务 失败, Request Error: {e}")
        return
    except Exception as e:
        log_message(f"领取 {task_name} 任务 失败: {e}")
        return
    
    cleaned_text = response.text.replace(
        '<?xml version="1.0" encoding="utf-8"?><ajax><![CDATA[',
        '').replace(']]></ajax>', '')
    log_message(f"领取 {task_name} 任务 成功: {cleaned_text}")
    if contains_keywords(cleaned_text, keywords):
        log_message(f"{task_name} 任务 已完成或不开放, 跳过\n")
        return

    # 获取当前时间的时间戳, 用于 nowtime 参数
    nowtime = int(datetime.datetime.now().timestamp() * 1000)
    # 请求参数
    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job2",
        "cid": cid,
        "nowtime": nowtime,
        "verify": verifyhash
    }
    local_headers["Referer"] = f"https://{NORTH_PLUS_BASE_URL}/plugin.php?H_name-tasks-actions-newtasks.html.html"
    # 发送 GET 请求
    try:
        response = requests.get(base_url, headers=local_headers, params=params)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        log_message(f"领取 {task_name} 奖励 失败, HTTP Error ({response.status_code}): {e}")
        return
    except requests.RequestException as e:
        log_message(f"领取 {task_name} 奖励 失败, Request Error: {e}")
        return
    except Exception as e:
        log_message(f"领取 {task_name} 奖励 失败: {e}")
        return
    
    cleaned_text = response.text.replace(
        '<?xml version="1.0" encoding="utf-8"?><ajax><![CDATA[',
        '').replace(']]></ajax>', '')
    log_message(f"领取 {task_name} 奖励 成功: {cleaned_text}")
    
    log_message(f"{task_name} 完成\n")
    json_data_handler.increment_value(1, CURRENT_MONTH, "level_plus", "tasks_completed", task_name)
    return

def level_plus_ids(id_list=[], verifyhash: str=None):
    """
    根据 `id_list` 领取并完成 level-plus 的多个任务

    :param id_list: 一个整数列表, 表示任务的标识符。
    :param verifyhash: 一个字符串, 表示用于验证的哈希。
    """
    # if verifyhash is none or empty string, find it
    if not verifyhash:
        verifyhash = level_plus_find_verifyhash()
    
    for cid in id_list:
        level_plus_single_task(cid, verifyhash)
        time.sleep(1)

def level_plus():
    """
    根据 level-plus 页面中的任务列表领取并完成任务。
    """
    log_message("\n------------------------------------\n")
    log_message("开始执行 level-plus 函数")
    log_message("\n------------------------------------\n")

    html_content = level_plus_tasks_page()

    id_list = level_plus_find_task_ids(html_content)
    log_message(f"页面中的任务 id : {id_list}")
    id_list = [id for id in id_list if id not in [14, 15]] # 移除每日签到和每周签到

    verifyhash = level_plus_find_verifyhash(html_content)

    # 先尝试页面中存在的任务
    level_plus_ids(id_list, verifyhash)
    
    # 每日签到
    level_plus_single_task(15, verifyhash, "每日签到")

    time.sleep(1)

    # 每周签到
    level_plus_single_task(14, verifyhash, "每周签到")

    log_message("\n------------------------------------\n")

    return


def level_plus_all(max_id=22):
    """
    领取并完成 level-plus 的所有任务, 从 1 到 `max_id`。
    """
    log_message("\n------------------------------------\n")
    log_message(f"开始执行 level-plus 全部函数, 尝试 1 到 {max_id} 的所有任务")
    log_message("\n------------------------------------\n")
    verifyhash = level_plus_find_verifyhash()

    for cid in range(1, max_id+1):
        level_plus_single_task(cid, verifyhash)
        time.sleep(1)

    return

def level_plus_start(all=False):
    """开始执行 level plus (south-plus) 签到"""
    if not set_cookie():
        return
    
    current_year = datetime.datetime.now().year
    json_path = f"./data/others_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)
    
    # 签到
    if all:
        level_plus_all()
    else:
        level_plus()

    json_data_handler.write_data()

    return
