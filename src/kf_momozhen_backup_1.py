import datetime
import json
import os
import random
import re
import time

from typing import Callable

import requests
from bs4 import BeautifulSoup

from . import utils
from .utils import log_message

kf_feiyue_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://bbs.kfpromax.com/kf_growup.php",
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

momozhen_headers = {
  "Accept": "*/*",
  "Accept-Encoding": "gzip, deflate, br",
  "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
  "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
  "Origin": "https://www.momozhen.com",
  "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
  "Sec-Ch-Ua-Mobile": "?0",
  "Sec-Ch-Ua-Platform": "\"Windows\"",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
  "X-Requested-With": "XMLHttpRequest"
}

def set_cookie():
    cookie_str = os.environ.get("KF_FEIYUE_COOKIE")
    if not cookie_str:
        log_message("请设置环墶变量 KF_FEIYUE_COOKIE", level="error")
        return False
    global kf_feiyue_headers
    kf_feiyue_headers["Cookie"] = cookie_str
    return True

def set_guguzhen_headers():
    global momozhen_headers
    # 步骤1: 访问基本URL, 处理重定向并更新cookies
    url = "https://bbs.kfpromax.com/fyg_sjcdwj.php?go=play&xl=2"
    response = requests.get(url, headers=kf_feiyue_headers, allow_redirects=False)
    if response.status_code == 302:
        new_url = response.headers.get('Location')

    # 步骤2: 访问新URL, 不带cookie的header
    headers = momozhen_headers.copy()
    response = requests.get(new_url, headers=headers, allow_redirects=False)
    if response.status_code == 302:
        # 更新momozhen_headers中的cookies
        cookies = response.cookies.get_dict()
        headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
    
    momozhen_headers = headers
    return

def kf_guguzhen_fyg_pk():
    base_url = "https://www.momozhen.com"
    path = "/fyg_pk.php"
    local_headers = momozhen_headers.copy()
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_index.php"

    response = requests.get(url, headers=local_headers)
    if response.status_code != 200:
        log_message(f"fyg_pk 访问失败, 状态码: {response.status_code}")
        
    path = "/fyg_read.php"
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_pk.php"
    data = b'f=12'
    local_headers["Content-Length"] = str(len(data))

    response = requests.post(url, headers=local_headers, data=data)
    if response.status_code != 200:
        log_message(f"fyg_read 访问失败, 状态码: {response.status_code}")
    
    data = b'f=25'
    local_headers["Content-Length"] = str(len(data))

    response = requests.post(url, headers=local_headers, data=data)
    if response.status_code != 200:
        log_message(f"fyg_read 访问失败, 状态码: {response.status_code}")
        
    return


def kf_guguzhen_shatan_shuaxin():
    """开始 10 次沙滩刷新"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = b'c=12&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_beach.php"
    save_text = ""
    for i in range(10):
        response = requests.post(url, headers=local_headers, data=data)
        # 检查响应
        if response.status_code == 200:
            save_text += response.text
            save_text += "\n------------------------------------\n"
            if "今日强制刷新次数已达上限" in response.text:
                log_message(f"达到上限退出: {response.text}")
                return
            log_message(f"沙滩刷新成功: {response.text}")
        else:
            log_message(f"失败, 状态码: {response.status_code}")
        if i % 2 == 0:
            time.sleep(1)
    utils.save_string_as_file(save_text, prefix="guguzhen_shatan_shuaxin", folder="kf_guguzhen")
    return


def kf_guguzhen_print_zhuangbei(html_content: str):
    # Patterns for extracting information
    button_pattern = r'<button.*?data-content=".*?" title=".*?<br>.*?" data-placement=".*?" data-html="true" data-trigger="hover".*?</button>'
    name_pattern = r'title="Lv\.<span class=\'fyg_f18\'>\d+</span>.*?<br>(.*?)\"'
    level_pattern = r'title="Lv\.<span class=\'fyg_f18\'>(\d+)</span>'
    id_pattern = r'onclick="zbtip\(\'(\d+)\','
    attributes_pattern = r'data-content="(.*?)"'
    rarity_pattern = r'url\(ys/icon/z/z\d+_(\d)\.gif\);'
    
    # Finding all button elements
    buttons = re.findall(button_pattern, html_content, re.DOTALL)
    
    for button_html in buttons:
        # Extracting equipment name
        name_match = re.search(name_pattern, button_html, re.DOTALL)
        equipment_name = name_match.group(1) if name_match else "Unknown"
        
        # Extracting rarity
        rarity_match = re.search(rarity_pattern, button_html, re.DOTALL)
        rarity = rarity_match.group(1) if rarity_match else "Unknown"
        
        # Extracting level
        level_match = re.search(level_pattern, button_html, re.DOTALL)
        level = level_match.group(1) if level_match else "Unknown"
        
        # Extracting ID
        id_match = re.search(id_pattern, button_html, re.DOTALL)
        id_ = id_match.group(1) if id_match else "Unknown"
        
        # Extracting attributes
        attributes_html_match = re.search(attributes_pattern, button_html, re.DOTALL)
        attributes_html = attributes_html_match.group(1) if attributes_html_match else ""
        attributes = re.findall(r'>([^<]+)<span', attributes_html)
        
        # Compiling extracted information
        info = f"{equipment_name}({rarity})\nLv. {level}\nID = {id_}\n" + "\n".join(attributes) + "\n"
        
        # Printing the information for each equipment
        log_message(info)

def extract_equipment_ids(html_content: str):
    # Define the pattern to extract the necessary information
    pattern = r'background-image:url\(.*?_([3-9])\.gif\).*?title="Lv\.<span class=\'fyg_f18\'>(\d+)</span>.*?onclick="zbtip\(\'(\d+)\','
    matches = re.findall(pattern, html_content, re.DOTALL)
    
    # Define the minimum level requirement for each rarity
    rarity_level_requirements = {
        '3': 295,
        '4': 290,
        '5': 285,
        '6': 280,
        '7': 275,
        # Extend as needed for higher rarities
    }
    
    # Filter and collect the IDs based on rarity and level requirements
    valid_ids = []
    for rarity, level, equipment_id in matches:
        if int(level) >= rarity_level_requirements.get(rarity, 0):
            valid_ids.append(equipment_id)
    
    return valid_ids

def kf_guguzhen_pick_zhuangbei(id):
    """领取沙滩装备 {id}"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = f'c=1&id={id}&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_beach.php"
    response = requests.post(url, headers=local_headers, data=data)
    # 检查响应
    if response.status_code == 200:
        log_message(f"成功领取 {id} : {response.text}")
    else:
        log_message(f"领取 {id} 失败, 状态码: {response.status_code}")
    return

def kf_guguzhen_shatan_linqu():
    """领取沙滩装备"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_read.php"
    data = b'f=1'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_beach.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"沙滩装备: \n")
        kf_guguzhen_print_zhuangbei(response.text)
        utils.save_string_as_file(response.text, prefix="guguzhen_shatan_linqu", folder="kf_guguzhen")
        log_message(f"领取装备: \n")
        ids = extract_equipment_ids(response.text)
        for id in ids:
            kf_guguzhen_pick_zhuangbei(id)
    else:
        log_message(f"失败, 状态码: {response.status_code}\n")
    
    return



def kf_guguzhen_shatan_qinli():
    """清理沙滩"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = b'c=20&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_beach.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"清理沙滩成功: {response.text}")
    else:
        log_message(f"失败, 状态码: {response.status_code}")
    return

def kf_guguzhen_xuyuanchi():
    """许愿池"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = b'c=18&id=10&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_wish.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"许愿池: {response.text}")
        utils.save_string_as_file(response.text, prefix="guguzhen_xuyuanchi", folder="kf_guguzhen")
    else:
        log_message(f"失败, 状态码: {response.status_code}")
    return


def kf_guguzhen_baoshigongfang_parse_activity_time(activity_text: str):
    """从活动文本中解析当前值、增速和计算剩余时间"""
    numbers = re.findall(r'\d+\.?\d*', activity_text)
    current_value = float(numbers[0])
    rate_per_minute = float(numbers[-1])
    return current_value, rate_per_minute

def kf_guguzhen_baoshigongfang_parse_activity_sand(activity_text: str):
    """从星沙活动文本中特殊解析当前值、增速"""
    # 先找到括号内的数字作为当前值
    current_value_match = re.search(r'\((\d+\.\d+)\)', activity_text)
    current_value = float(current_value_match.group(1)) if current_value_match else 0
    # 解析每分钟增速
    rate_per_minute_match = re.search(r'每分钟 \+(\d+\.?\d*)星沙', activity_text)
    rate_per_minute = float(rate_per_minute_match.group(1)) if rate_per_minute_match else 0
    return current_value, rate_per_minute
    
def kf_guguzhen_baoshigongfang_shell(text: str, begin_minutes=0):
    """
    将 "已拾取1640贝壳Lv.656 伊 (赶海中...)红石25每分钟 +205贝壳"
    转换为 "已拾取 1640 贝壳 (每分钟 + 205 贝壳) 剩余 81 小时 11 分"
    """
    shell_max = 1000000  # 单次贝壳产出上限
    current_value, rate_per_minute = kf_guguzhen_baoshigongfang_parse_activity_time(text)
    minutes = utils.compute_remaining_time(shell_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    log_message(f"已拾取 {current_value} 贝壳 (每分钟 +{rate_per_minute}贝壳) 剩余 {utils.format_remaining_time(remaining_time)}")

def kf_guguzhen_baoshigongfang_sand(text: str, begin_minutes=0):
    """
    将 "已开采0星沙(0.0104)Lv.656 霞 (挖矿中...)虚石0每分钟 +0.0013星沙"
    转换为 "已开采 0星沙(0.0104) (每分钟 + 0.0013 星沙) 剩余 128 小时 5 分, 距下一整数 12 小时 42 分"
    """
    sand_max = 10  # 单次星沙产出上限
    current_value, rate_per_minute = kf_guguzhen_baoshigongfang_parse_activity_sand(text)
    minutes = utils.compute_remaining_time(sand_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    next_int_minutes = utils.compute_time_to_next_integer(begin_minutes, rate_per_minute)
    log_message(f"已开采 {current_value} 星沙 (每分钟 +{rate_per_minute}星沙) 剩余 {utils.format_remaining_time(remaining_time)}, 距下一整数 {utils.format_remaining_time(next_int_minutes)}")

def kf_guguzhen_baoshigongfang_experience(text: str, begin_minutes=0):
    """
    将 "已获得0幻影经验Lv.656 希 (闭关中...)幻石0每分钟 +0.038幻影经验"
    转换为 "已获得 0 幻影经验 (每分钟 +0.038 幻影经验) 剩余 87 小时 36 分, 每点需要 0 小时 19 分"
    """
    experience_max = 200  # 单次幻影经验产出上限
    current_value, rate_per_minute = kf_guguzhen_baoshigongfang_parse_activity_time(text)
    minutes = utils.compute_remaining_time(experience_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    next_int_minutes = utils.compute_time_to_next_integer(begin_minutes, rate_per_minute)
    log_message(f"已获得 {current_value} 幻影经验 (每分钟 +{rate_per_minute}幻影经验) 剩余 {utils.format_remaining_time(remaining_time)}, 距下一整数 {utils.format_remaining_time(next_int_minutes)}")

def kf_guguzhen_baoshigongfang_percent_items(text: str, begin_minutes=0):
    """
    将 "0.416%概率出产{item_name}Lv.656 琳 (组装中...)银石20每分钟 +0.052%概率"
    转换为 "0.416% 概率出产 {item_name} (每分钟 +0.052% 概率) 剩余 31 小时 56 分"
    """
    item_name = re.search(r"概率出产 (.+?) Lv", text).group(1)
    percent_max = 100  # 假设概率满值为100%
    current_value, rate_per_minute = kf_guguzhen_baoshigongfang_parse_activity_time(text)
    minutes = utils.compute_remaining_time(percent_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    log_message(f"{current_value}% 概率出产 {item_name} (每分钟 +{rate_per_minute}%概率) 剩余 {utils.format_remaining_time(remaining_time)}")
    
def kf_guguzhen_baoshigongfang_print_items(html_content: str, begin_minutes=0):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取相关信息
    activities = soup.find_all("div", class_="alert alert-info fyg_f14 fyg_lh30")
    
    for activity in activities:
        text = activity.get_text(separator=" ", strip=True)
        if "贝壳" in text:
            kf_guguzhen_baoshigongfang_shell(text, begin_minutes)
        elif "星沙" in text:
            kf_guguzhen_baoshigongfang_sand(text, begin_minutes)
        elif "幻影经验" in text:
            kf_guguzhen_baoshigongfang_experience(text, begin_minutes)
        elif "概率出产" in text:
            kf_guguzhen_baoshigongfang_percent_items(text, begin_minutes)
        else:
            log_message(text)

def kf_guguzhen_baoshigongfang_find_work_hours() -> int:
    """
    尝试找到已开工 {int} 小时
    If no such information is found, returns 0.
    """
    base_url = "https://www.momozhen.com"
    path = "/fyg_read.php"
    url = base_url + path
    data = b'f=21'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    local_headers["Referer"] = "https://www.momozhen.com/fyg_gem.php"
    response = requests.post(url, headers=local_headers, data=data)
    
    # 检查响应
    if response.status_code != 200:
        log_message(f"失败, 状态码: {response.status_code}")
        return 0
    
    soup = BeautifulSoup(response.text, 'html.parser')
    buttons = soup.find_all('button')
    for button in buttons:
        if "已开工" in button.text:
            pattern = r"(\d+)小时(\d+)分钟"
            match = re.search(pattern, button.text)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                total_minutes = utils.calculate_total_minutes(minutes, hours=hours)
                log_message(f"宝石工坊已开工 {hours} 小时 {minutes} 分钟")
                kf_guguzhen_baoshigongfang_print_items(response.text, total_minutes)
                return hours
            
    log_message(f"宝石工坊读取失败")
    kf_guguzhen_baoshigongfang_print_items(response.text)
    utils.save_string_as_file(response.text, prefix="guguzhen_baoshigongfang", folder="kf_guguzhen")

    return 0

def kf_guguzhen_baoshigongfang():
    """宝石工坊 开工 / 收工"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = b'c=30&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_gem.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"宝石工坊 开工 / 收工: {response.text}")
        utils.save_string_as_file(response.text, prefix="guguzhen_baoshigongfang", folder="kf_guguzhen")
    else:
        log_message(f"失败, 状态码: {response.status_code}")
    return

def kf_guguzhen_tiliyaoshui():
    """使用体力药水"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    data = b'c=13&id=2&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_index.php"
    response = requests.post(url, headers=local_headers, data=data)

    keywords = ["无法使用"]
    # 检查响应
    if response.status_code == 200:
        log_message(f"使用体力药水: {response.text}")
        if utils.contains_keywords(response.text, keywords):
            log_message("无法使用体力药水, 结束")
            return False
    else:
        log_message(f"失败, 状态码: {response.status_code}")
        return False
    return True

def kf_guguzhen_fanpai_find_SVIP() -> str:
    """
    尝试找到 SVIP透视 在 class "text-muted" 里.
    If no such text is found, returns an empty string.
    """
    base_url = "https://www.momozhen.com"
    path = "/fyg_read.php"
    url = base_url + path
    data = b'f=10'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    local_headers["Referer"] = "https://www.momozhen.com/fyg_index.php"
    response = requests.post(url, headers=local_headers, data=data)
    
    # 检查响应
    if response.status_code != 200:
        log_message(f"失败, 状态码: {response.status_code}")
        return ""
    soup = BeautifulSoup(response.text, 'html.parser')
    text_muted = soup.find(class_="text-muted")
    svip_str = text_muted.get_text(strip=True) if text_muted else ""
    
    log_message(f"尝试获取SVIP透视: {svip_str}")
    return svip_str

def kf_guguzhen_fanpai():
    """12张牌里有蓝、绿、黄、红各三张。每次翻一张牌。当任意颜色的三张牌被翻出时, 则获得该三张牌对应品质的奖励。"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_click.php"
    url = base_url + path
    local_headers = momozhen_headers.copy()
    local_headers["Referer"] = "https://www.momozhen.com/fyg_index.php"
    safeid = "5cda2b"  # 假设safeid是一个固定值, 如果它是变动的, 你需要动态获取它
    ids = list(range(1, 13))  # 创建一个从1到12的列表, 代表12张牌的id

    save_text = ""
    svip_str = kf_guguzhen_fanpai_find_SVIP()

    if utils.contains_keywords(svip_str, keywords=["稀有", "幸运"]):
        ids.remove(1)
        log_message("根据 SVIP 透视不翻第一张牌")

    for _ in range(len(ids)):
        # 随机选择一个id, 然后从列表中移除这个id, 以确保下次不会重复选择
        card_id = random.choice(ids)
        ids.remove(card_id)

        # 构建POST请求的数据
        data = f"c=8&id={card_id}&safeid={safeid}".encode('ascii')
        local_headers["Content-Length"] = str(len(data))

        # 发送POST请求
        response = requests.post(url, headers=local_headers, data=data)

        # 检查响应
        if response.status_code == 200:
            save_text += response.text
            save_text += "\n------------------------------------\n"
            if "今日已获取奖励" in response.text:
                log_message(f"达到上限退出: {response.text}")
                utils.save_string_as_file(save_text, prefix="guguzhen_fanpai", folder="kf_guguzhen")
                return False
            if "请刷新后重试" in response.text:
                log_message(f"需刷新: {response.text}")
                utils.save_string_as_file(save_text, prefix="guguzhen_fanpai", folder="kf_guguzhen")
                return True
            log_message(f"成功翻开牌: {response.text}")
        else:
            log_message(f"请求失败, 状态码: {response.status_code}")
    utils.save_string_as_file(save_text, prefix="guguzhen_fanpai", folder="kf_guguzhen")
    return False


def extract_battle_info(html_str: str):
    """解析 html_str 中的战斗信息, 并打印输出"""
    if "达到上限" in html_str and len(html_str) <= 50:
        log_message(html_str)
        return -3

    # try except, 如果失败设为空字符""
    try:
        soup = BeautifulSoup(html_str, 'html.parser')
        # Find the names and stats of the participants
        participants = soup.find_all(class_='fyg_f18')
        stats = soup.find_all('span', class_='label-outline')
    
        # Extracting names and stats
        name_1 = participants[0].get_text().strip()
        stats_1 = ' / '.join([stat.get_text().strip() for stat in stats[:2]])
        name_2 = participants[1].get_text().strip()
        stats_2 = ' / '.join([stat.get_text().strip() for stat in stats[3:5]])
    except:
        name_1 = "Unknown"
        stats_1 = "Unknown"
        name_2 = "Unknown"
        stats_2 = "Unknown"
        #utils.save_string_as_file(html_str, prefix="gugu_zhandou", folder="kf_guguzhen")
    
    # Determine the winner
    try:
        winner_text = soup.find(
            'div',
            class_='alert alert-danger with-icon fyg_tc').get_text().strip()
        output = f"{name_1} ({stats_1}) v.s. {name_2} ({stats_2})\n{winner_text} "
        log_message(f"{output}")
        return 1
    except:
        winner_text = "No winner"
    try:
        winner_text = soup.find(
            'div',
            class_='alert alert-info with-icon fyg_tc').get_text().strip()
        output = f"{name_1} ({stats_1}) v.s. {name_2} ({stats_2})\n{winner_text} "
        log_message(f"{output}")
        return -1
    except:
        winner_text = "No winner"
    try:
        winner_text = soup.find(
            'div', class_='alert with-icon fyg_tc').get_text().strip()
        output = f"{name_1} ({stats_1}) v.s. {name_2} ({stats_2})\n{winner_text} "
        log_message(f"{output}")
        return 0
    except:
        winner_text = "No winner"

    # Format and log_message the output
    output = f"{name_1} ({stats_1}) v.s. {name_2} ({stats_2})\n{winner_text} "
    #output = f"{winner_text} "
    log_message(output)
    return -2


def kf_guguzhen_jingong():
    """开始 20 次争夺（打人）, 遇到平局时增加额外的循环"""
    kf_guguzhen_fyg_pk()
    
    base_url = "https://www.momozhen.com"
    path = "/fyg_v_intel.php"
    data = b'id=2&safeid=5cda2b'
    local_headers = momozhen_headers.copy()
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_pk.php"

    # 初始化胜负平统计
    win_count, lose_count, draw_count, error_count = 0, 0, 0, 0
    attempts = 0  # 已尝试次数

    save_text = ""

    while attempts < 20:
        response = requests.post(url, headers=local_headers, data=data)
        # 检查响应
        if response.status_code == 200:
            save_text += response.text
            save_text += "\n------------------------------------\n"
            if "今日已主动出击20次" in response.text:
                log_message(f"达到上限退出: {response.text}")
                break
            if "刷新页面" in response.text:
                log_message(f"需刷新: {response.text}")
                utils.save_string_as_file(save_text, prefix="guguzhen_jingong", folder="kf_guguzhen")
                return True
            log_message("成功: ")
            result = extract_battle_info(response.text)
            if result == 1:
                win_count += 1
                attempts += 1
            elif result == -1:
                lose_count += 1
                attempts += 1
            elif result == 0:
                draw_count += 1
                log_message("平局, 将重新尝试")
                # 注：平局时不增加 attempts 计数, 以确保进行20次胜负判定
            elif result == -2:
                error_count += 1
                attempts += 1
                log_message("出错了")
        else:
            log_message(f"失败, 状态码: {response.status_code}")
            error_count += 1
            attempts += 1
    
    # 打印统计结果
    log_message(f"统计结果: 胜:{win_count} 负:{lose_count} 平:{draw_count} 错误:{error_count}")
    utils.save_string_as_file(save_text, prefix="guguzhen_jingong", folder="kf_guguzhen")
    return False

def kf_guguzhen_shangdian():
    """商店购买 体力药水, 免费商品"""
    base_url = "https://www.momozhen.com"
    path = "/fyg_shop_click.php"
    local_headers = momozhen_headers.copy()

    # [日限]BVIP打卡包
    data = b'c=5&safeid=5cda2b'
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_shop.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"购买成功: {response.text}")
    else:
        log_message(f"购买失败, 状态码: {response.status_code}")

    # [日限]SVIP打卡包
    data = b'c=12&safeid=5cda2b'
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_shop.php"
    response = requests.post(url, headers=local_headers, data=data)

    # 检查响应
    if response.status_code == 200:
        log_message(f"购买成功: {response.text}")
    else:
        log_message(f"购买失败, 状态码: {response.status_code}")

    # 体能刺激药水 x 4
    data = b'c=7&safeid=5cda2b'
    local_headers["Content-Length"] = str(len(data))
    url = base_url + path
    local_headers["Referer"] = "https://www.momozhen.com/fyg_shop.php"
    for _ in range(4):
        response = requests.post(url, headers=local_headers, data=data)

        # 检查响应
        if response.status_code == 200:
            log_message(f"购买成功: {response.text}")
        else:
            log_message(f"购买失败, 状态码: {response.status_code}")

    return


def kf_guguzhen_try_operation(operation: Callable[[], bool], operation_name: str):
    """
    尝试执行某操作, 最多重试10次。
    如果操作成功, 则返回True；如果尝试了10次仍未成功, 则返回False。
    """
    for i in range(10):
        if operation():
            set_guguzhen_headers()  # 刷新headers
            # Current time in the specified format
            formatted_time = datetime.datetime.now().strftime("%y-%m-%d-%H.%M.%S")
            # Path to save the JSON file
            file_path = f"kf_guguzhen/headers_{formatted_time}.json"
            
            # Writing the JSON data to the specified file
            with open(file_path, "w") as json_file:
                json.dump(momozhen_headers, json_file)
                
            time.sleep(1)
        else:
            log_message(f"{operation_name}成功, 尝试次数：{i+1}")
            return True
        log_message(f"{operation_name}尝试重试第{i+1}次")
    log_message(f"{operation_name}尝试了10次, 但都失败了")
    return False

def kf_guguzhen():
    """咕咕镇"""
    log_message("\n------------------------------------\n")
    log_message("开始执行 咕咕镇 函数")
    log_message("\n------------------------------------\n")

    # 步骤3: 调用 kf_guguzhen 相关函数
    kf_guguzhen_shangdian() # 商店

    time.sleep(1)

    baoshigongfang_hour = kf_guguzhen_baoshigongfang_find_work_hours()
    if baoshigongfang_hour < 1:
        kf_guguzhen_baoshigongfang() # 开始宝石工坊
    elif baoshigongfang_hour >= 32: # 可改, 目前32小时正好 1 项满
        kf_guguzhen_baoshigongfang() # 领取宝石工坊
        kf_guguzhen_baoshigongfang() # 开始宝石工坊
    else:
        log_message("宝石工坊未满 32 小时")

    time.sleep(1)

    # kf_guguzhen_shatan_shuaxin() # 刷新沙滩
    # time.sleep(1)
    kf_guguzhen_shatan_linqu() # 沙滩领取装备
    time.sleep(1)
    kf_guguzhen_shatan_qinli() # 沙滩装备分解
    time.sleep(1)


    # 尝试进攻3次（包含使用两次药水的机会）
    for attack_round in range(3):
        # 进攻成功前尝试10次进攻
        if not kf_guguzhen_try_operation(kf_guguzhen_jingong, "进攻"):
            break  # 如果10次进攻都失败, 直接结束循环
            
        time.sleep(1)

        # 翻牌, 如果10次都失败, 则不继续后续操作
        if not kf_guguzhen_try_operation(kf_guguzhen_fanpai, "翻牌"):
            break
        time.sleep(1)

        # 前两轮进攻后尝试使用体力药水
        if attack_round < 2:
            if not kf_guguzhen_tiliyaoshui():
                break
        time.sleep(1)

    kf_guguzhen_xuyuanchi()

    log_message("\n------------------------------------\n")

    return

def kf_momozhen_start():
    """开始执行 kf 咕咕镇 签到"""
    if not set_cookie():
        return
    set_guguzhen_headers()
    
    # 签到
    kf_guguzhen()

    return
