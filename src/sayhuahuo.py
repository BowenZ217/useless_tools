
import json
import os
import re
import time

from html.parser import HTMLParser
from xml.etree import ElementTree as ET

import requests

from .utils.logger import log_message
from .utils.response_processing import decompress_response
from .utils.file_operations import save_string_as_file

# Global variables
sayhuahuo_headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
}

def set_cookie():
    cookie_str = os.environ.get("SAYHUAHUO_COOKIE")
    if not cookie_str:
        log_message("请设置环墶变量 SAYHUAHUO_COOKIE", level="error")
        return False
    global sayhuahuo_headers
    sayhuahuo_headers["Cookie"] = cookie_str
    return True

class DivTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.is_target_div = False  # 是否是目标div
        self.result = ""

    def handle_starttag(self, tag, attrs):
        if tag == "div" and ("class", "c") in attrs:
            self.is_target_div = True

    def handle_data(self, data):
        if self.is_target_div:
            self.result += data

    def handle_endtag(self, tag):
        if tag == "div" and self.is_target_div:
            self.is_target_div = False

def extract_text_from_sayhuahuo(xml_data: str):
    """
    从HTML内容中提取<div class="c">内的文本。

    :param html_content: 要解析的HTML内容字符串
    :return: 提取的文本字符串
    """
    # 去除XML字符串前面的空白字符后再次尝试解析
    xml_data_cleaned = xml_data.strip()

    # 重新解析XML
    root = ET.fromstring(xml_data_cleaned)
    cdata_content = root.text
    parser = DivTextExtractor()
    parser.feed(cdata_content)
    return parser.result.strip()


def make_requests(action: str, times: int, base_url: str=None):
    """执行请求 action 次数 times 次。"""
    if not base_url:
        base_url = "https://www.sayhuahuo.xyz/hanabigame-api.html"
    log_message(f"正在执行 {action} 请求 {times} 次...")

    url = f"{base_url}?action={action}"
    for i in range(times):
        response = None  # Initialize response variable
        try:
            response = requests.get(url, headers=sayhuahuo_headers)
            # 这里打印出每个请求的响应状态码和内容, 您也可以根据需要处理这些响应
            if response:
                decompressed_content = decompress_response(response.content)
                try:
                    # 尝试将解压缩的内容解析为JSON
                    response_json = json.loads(decompressed_content)
                    if response_json.get('code') == 406:
                        log_message("请求已达到上限。")
                        break  # 如果code为406, 退出循环
                except json.JSONDecodeError:
                    log_message("解析响应JSON失败")

                log_message(f"Status Code: {response.status_code}")
                log_message(f"Response: {decompressed_content}\n")
            else:
                log_message("请求失败.")
            if i % 2 == 0:
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            log_message(f"请求失败: {e}")

    log_message(f"Action: {action}, 请求完成\n")

def huahuolianjie():
    log_message("\n------------------------------------\n")
    log_message("开始执行 花火链接 函数")
    log_message("\n------------------------------------\n")

    # 执行请求
    make_requests("getexp", 3)  # 请求 getexp 3 次
    make_requests("getcredit", 20)  # 请求 getcredit 20 次
    #make_requests("getcoin", 1)    # 请求 getcoin 1 次

    log_message("\n------------------------------------\n")
    return

def huahuoxueyuan():
    log_message("\n------------------------------------\n")
    log_message("开始执行 花火学院签到 函数")
    log_message("\n------------------------------------\n")
    
    # 获取 formhash
    base_url = "https://www.sayhuahuo.xyz/dsu_paulsign-sign.html"
    
    # 尝试获取 formhash
    formhash = "a64e7183"
    try:
        response = requests.post(base_url, headers=sayhuahuo_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        # 'name=\"formhash\" value=\"(.+?)\"', // formhash 正则
        match = re.search(r'name=\"formhash\" value=\"(.+?)\"', response.text)
        if match:
            # 如果找到匹配项, 提取formhash
            formhash = match.group(1)
            log_message(f"找到的formhash是: {formhash}")
        else:
            save_string_as_file(response.text, "sayhuahuo_formhash_fail", "sayhuahuo", response.encoding)

    except requests.HTTPError as e:
        log_message(f"formhash 请求失败 HTTP Error ({response.status_code}): {e}", level="error")
    except requests.RequestException as e:
        log_message(f"formhash 请求失败 Request Error: {e}", level="error")
    except Exception as e:
        log_message(f"formhash 请求失败: {e}", level="error")
    

    # ------------------------------------------------
    # 构建签到请求
    # ------------------------------------------------
        
    base_url = "https://www.sayhuahuo.xyz/plugin.php"

    params = {
        "id": "dsu_paulsign:sign",
        "operation": "qiandao",
        "infloat": "1",
        "inajax": "1",
    }
    data = {
        "formhash": formhash,  # 通常需要一个 formhash, 你需要从页面中获取这个值
        "qdxq": "wl",    # 这是选择的心情表情
        "qdmode": 1,
        "todaysay": " 签到",  # 这是用户想说的话
        "fastreply": 0,
    }
    
    # 发送POST请求
    try:
        response = requests.post(base_url, headers=sayhuahuo_headers, params=params, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        log_message(extract_text_from_sayhuahuo(response.text))
        
    except requests.HTTPError as e:
        log_message(f"签到请求失败 HTTP Error ({response.status_code}): {e}", level="error")
        return
    except requests.RequestException as e:
        log_message(f"签到请求失败 Request Error: {e}", level="error")
        return
    except Exception as e:
        if 'response' in locals():
            log_message(f"签到解析失败: {e}", level="error")
        else:
            log_message(f"签到请求失败，无法获取响应: {e}", level="error")
        return
    
    log_message("\n------------------------------------\n")
    return


def sayhuahuo_start():
    """开始执行花火签到"""
    if not set_cookie():
        return
    
    # 签到
    huahuolianjie()
    time.sleep(1)
    huahuoxueyuan()

    return
