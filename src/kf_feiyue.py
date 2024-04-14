
import os
import re
import time

import requests
from bs4 import BeautifulSoup

from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

KF_FEIYUE_BASE_URL = "bbs.kfpromax.com"

kf_feiyue_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"https://{KF_FEIYUE_BASE_URL}/kf_growup.php",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
}

def set_cookie():
    cookie_str = os.environ.get("KF_FEIYUE_COOKIE")
    if not cookie_str:
        log_message("请设置环墶变量 KF_FEIYUE_COOKIE", level="error")
        return False
    global kf_feiyue_headers
    kf_feiyue_headers["Cookie"] = cookie_str
    return True

def kf_feiyue_extract_sucess_page(html_str: str):
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_str, 'html.parser')

    # 找到<body>部分
    body_content = soup.find('body')

    # 移除所有<a>标签内的文本，但保留其他内容
    for a_tag in body_content.find_all('a'):
        if '自动跳转' in a_tag.text:
            a_tag.decompose()

    # 返回去除了<a>标签内自动跳转文本后的剩余文字
    return body_content.get_text(separator="\n", strip=True)

def kf_feiyue_request_kf_growup() -> str:
    # 请求的基本 URL
    base_url = f"https://{KF_FEIYUE_BASE_URL}/kf_growup.php"

    # 发送 GET 请求
    try:
        response = requests.get(base_url, headers=kf_feiyue_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        log_message(f"签到请求失败 HTTP Error ({response.status_code}): {e}", level="error")
        log_message("\n------------------------------------\n")
        return "签到请求失败"
    except requests.RequestException as e:
        log_message(f"签到请求失败 Request Error: {e}", level="error")
        log_message("\n------------------------------------\n")
        return "签到请求失败"
    except Exception as e:
        log_message(f"签到请求失败: {e}", level="error")
        return "签到请求失败"
    
    return response.text

def kf_feiyue_request_checkin(url: str):
    """请求签到"""
    try:
        log_message(f"请求签到: {url}")
        response = requests.get(url, headers=kf_feiyue_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        log_message(kf_feiyue_extract_sucess_page(response.text))
    except requests.HTTPError as e:
        log_message(f"签到请求失败 HTTP Error ({response.status_code}): {e}", level="error")
        return False
    except requests.RequestException as e:
        log_message(f"签到请求失败 Request Error: {e}", level="error")
        return False
    except Exception as e:
        log_message(f"页面解析失败: {e}", level="error")
        return False
    return True

def kf_feiyue():
    log_message("\n------------------------------------\n")
    log_message("开始执行 kf 绯月 函数")
    log_message("\n------------------------------------\n")

    # 请求 kf_growup 页面
    response_text = kf_feiyue_request_kf_growup()

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response_text, 'html.parser')

    # 使用正则表达式匹配URL模式
    pattern = re.compile(r'kf_growup\.php\?ok=3&safeid=\w+')

    # 找到所有匹配特定模式的<a>标签
    a_tags = soup.find_all('a', href=pattern)

    # 如果 a_tags 为空, 则 log 没有找到链接
    if not a_tags:
        save_string_as_file(response_text, prefix="kf_feiyue", folder="kf_feiyue")
        log_message("没有找到链接")

    # 对于找到的每个匹配项, 提取并打印href属性
    for a_tag in a_tags:
        url = f"https://{KF_FEIYUE_BASE_URL}/" + a_tag['href']
        
        kf_feiyue_request_checkin(url)

        time.sleep(1)

    log_message("\n------------------------------------\n")
    
    return


def kf_feiyue_start():
    """开始执行 kf 绯月 签到"""
    if not set_cookie():
        return
    
    # 签到
    kf_feiyue()

    return


