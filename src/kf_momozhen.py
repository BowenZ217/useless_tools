import datetime
import os
import random
import re
import time

from typing import Callable

import requests
from bs4 import BeautifulSoup

from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file
from .utils.text_analysis import contains_keywords, convert_number_to_range
from .utils.time_utils import compute_remaining_time, compute_time_to_next_integer, calculate_total_minutes, format_remaining_time


MOMOZHEN_ENTRY_URL = "https://bbs.kfpromax.com/fyg_sjcdwj.php?go=play&xl=2"
MOMOZHEN_BASE_URL = "https://www.momozhen.com"
MOMOZHEN_SAFEID = "5cda2b"
CURRENT_MONTH = str(datetime.datetime.now().month)

kf_feiyue_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
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

kf_momozhen_headers = {
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
    """
    设置 momozhen 的 cookie
    """
    global kf_momozhen_headers

    cookie_str = os.environ.get("KF_FEIYUE_COOKIE")
    if not cookie_str:
        log_message("请设置环墶变量 KF_FEIYUE_COOKIE", level="error")
        return False
    global kf_feiyue_headers
    kf_feiyue_headers["Cookie"] = cookie_str
    
    try:
        # 步骤1: 访问基本URL, 显式处理重定向
        response = requests.get(MOMOZHEN_ENTRY_URL, headers=kf_feiyue_headers, allow_redirects=False)
        if response.status_code == 302:
            # 从响应中获取新的URL
            new_url = response.headers.get('Location')
        else:
            # 如果没有重定向，直接返回，可能需要记录日志或抛出异常
            log_message("咕咕镇登录失败, 没有重定向到新的URL ({response.status_code})")
            return False

        # 步骤2: 访问新URL, 不带cookie的header
        response = requests.get(new_url, headers=kf_momozhen_headers, allow_redirects=False)
        if response.status_code == 302 or response.status_code == 200:
            # 如果是重定向，获取并更新cookies
            cookies = response.cookies.get_dict()
            if cookies:  # 确保cookies不是空的
                kf_momozhen_headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
            else:
                log_message("咕咕镇登录失败, 没有获取到cookies")
                return False
        else:
            # 如果得到的响应不是302也不是200，可能需要记录日志或抛出异常
            log_message(f"咕咕镇 Unexpected status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        # 处理请求过程中可能出现的异常
        log_message(f"咕咕镇 error: {e}")
        return False
    
    return True

# ------------------------------
# 咕咕镇的一些请求接口
# ------------------------------

def kf_momozhen_fyg_read(f: str, id: str=None, zid: str=None, ca: str=None, Referer: str=None):
    """
    处理 `fyg_read` 接口的请求。

    :param f: 请求参数 1
    :param id: 请求参数 2
    :param ca: 请求参数 3
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数 (未给出的参数默认为 None):

    f=1: 沙滩装备信息
    f=2: 仓库装备信息
    f=3: `cding()` 函数 (宝石工坊 页面)
    f=5: 天赋信息
    f=6: `eqmy()` 函数 (未启用)
    f=7: 我的仓库
    f=8: 所有角色卡片简易信息
    f=9: 当前出战人物 具体信息
    f=10: 翻牌信息
    f=12: 当前 出击 具体信息
    f=16: 骰子战争等级 + {星晶/星沙/贝壳} 数量
    f=17: 商店 对账信息
    f=18: 角色卡片的详细信息
        zid = 卡片ID, 详细请看 `kf_momozhen_fyg_read(8)` 页面内容, 例如 `xxcard(3000)`
    f=19: 许愿池 当前信息
        return: num_0#num_1#...#num_15#num_16
        num_0 和 num_1 为 无用信息, 可能为功能更新日期
        其他请见 `fyg_wish.php` 页面内容的 `#xyx_{num}` 部分
    f=20: 物品信息
        id = 装备ID
            ca = 3: 仓库装备
            ca = 4: 沙滩装备
        id = 护符ID
            ca = 1: 已装备护符 (我的饰品)
            ca = 2: 仓库护符
    f=21: 宝石工坊 进度信息
    f=22: 当前出战人物，光环，争夺狗牌数量
    f=23: 争夺等级 和 争夺 强化属性
    f=24: 装备强化 (未启用)
        id = None: 主页面
        id = 1: 当前武器装备
        id = 2: 当前手臂装备
        id = 3: 当前身体装备
        id = 4: 当前头部装备
    f=25: 当前 出击 历史信息

    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer
    path = "/fyg_read.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    data = f"f={f}"
    if id:
        data += f"&id={id}"
    if zid:
        data += f"&zid={zid}"
    if ca:
        data += f"&ca={ca}"
    local_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_read({f}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_read_{f}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_read({f}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_read({f}) 失败: {e}", level="error")
        return ""
    return response.text

def kf_momozhen_fyg_menu(m: str, id: str=None, Referer: str=None):
    """
    处理 `fyg_menu` 接口的请求。

    :param c: 请求参数 1
    :param id: 请求参数 2
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数 (未给出的参数默认为 None):

    m=1: 锻造装备 目录
    m=2: 提升卡片 目录
    m=4: 恢复体力 (体力药水) 目录
        id = undefined: 体力药水
        id = 3003, 3004, ...: 物品介绍?
    m=5: 等级转换 目录
        id = 卡片ID, 详细请看 `kf_momozhen_fyg_read(8)` 页面内容, 例如 `xxcard(3000)`
    m=6: 提升宝石(宝石工坊) 目录
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer

    path = "/fyg_menu.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"m={m}"
    if id:
        data += f"&id={id}"
    else:
        data += "&id=undefined"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_menu({m}, {id}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_menu_{m}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_menu({m}, {id}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_menu({m}, {id}) 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_click(c: str, id: str=None, id2: str=None, id99: str=None, yz: str=None, Referer: str=None):
    """
    处理 `fyg_click` 接口的请求。

    :param c: 请求参数 1
    :param id: 请求参数 2
    :param id2: 请求参数 3
    :param id3: 请求参数 4
    :param yz: 请求参数 5
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数 (未给出的参数默认为 None):

    c=1: 领取沙滩装备
        id = 装备ID
    c=2: 保存加点
        id = 卡片ID
        add01 - add06 (00, 01, 03, 04, 05, 06): 加点信息 (力量, 敏捷, 智力, 体魄, 精神, 意志)
    c=3: 穿上装备
        id = 装备ID, 详细请看 `kf_momozhen_fyg_read(7)` 页面内容
    c=4: 更改天赋
        arr: 天赋ID (as an array), 详细请看 `kf_momozhen_fyg_read(5)` 页面内容
    c=5: 装备卡片 (需重新分配天赋光环)
        id = 卡片ID, 详细请看 `kf_momozhen_fyg_read(8)` 页面内容, 例如 `xxcard(3000)`
    c=6: 名称更改 (未启用)
        name: 新名称
    c=7: 丢弃装备 (到沙滩)
        id = 装备ID, 详细请看 `kf_momozhen_fyg_read(7)` 页面内容
    c=8: 翻牌
        id = 翻牌ID (1 - 12)
        return: 翻牌结果 (空字符为无奖励)
    c=9: 熔炼装备
        id = 装备ID (变成护符)
            yz = 熔炼装备的验证参数, 需要通过 `kf_momozhen_fyg_read(20)` 里面的 `pirlyz` 获取
            return: 护符ID
        id = 护符ID
            yz = 熔炼护符的验证参数 (默认 "124")
    c=10: `cmaxup(id)` 函数 (未启用) ?
        id = 卡片ID
    c=11: 等级转换
        id = 当前卡片ID
        id2 = 目标卡片ID
        id99 = 可能为转换卡片的验证参数, 需要通过 `kf_momozhen_fyg_menu(5, id)` 获取 (默认 "2")
        `gx_jydj(id)` 函数 (未启用), 需消耗 20 星沙
    c=12: 刷新沙滩, 立刻获得下一批随机装备
    c=13: 使用体力药水
        id = 1: 获取额外一次翻牌经验和贝壳奖励 (不含物品奖励)
        id = 2: 重置狗牌, 重新打狗牌重新翻牌获得完整的翻牌奖励
    c=14: 重置加点
        id = 卡片ID, 详细请看 `kf_momozhen_fyg_read(8)` 页面内容, 例如 `xxcard(3000)`
    c=17: 商店购买星晶 (rmb)
        xingjing = 购买星晶数量
    c=18: 许愿池 许愿
        id = 许愿次数 (1 - 10)
    c=20: 清理沙滩所有装备为 强化锻造石
    c=21: 放入仓库
        id = 护符 ID, 详细请看 `kf_momozhen_fyg_read(7)` 页面内容
    c=22: 装备 护身符
        id = 护符 ID, 详细请看 `kf_momozhen_fyg_read(7)` 页面内容
    c=23: 强化 护身符
        id = 护符 ID, 详细请看 `kf_momozhen_fyg_read(7)` 页面内容
    c=24: `expcard(id)` 函数
        id = 卡片ID ?
    c=25: 锻造装备, 消耗 (锻造材料箱 x2) 获取高级装备
        id = 装备ID, 详细请看 `kf_momozhen_fyg_menu(1)`
    c=26: 提升卡片等级 (和品质)
        id = 卡片ID, 详细请看 `kf_momozhen_fyg_menu(2)`
    c=27: 提升宝石数量, 数量越大的成功率越低
        id = 宝石ID, 详细请看 `kf_momozhen_fyg_menu(6)`
    c=28: `taitem(id)` 函数
        id = 卡片ID ?
    c=29:
        id = 29: 使用光环天赋 (石提升天赋光环)
    c=30: 宝石工坊 开工 / 收工
    c=33: `ocuz(id)` 函数
        id = ?
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer

    path = "/fyg_click.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"c={c}"
    if id:
        data += f"&id={id}"
    if id2:
        data += f"&id2={id2}"
    # if id99:
    #     data += f"&id3={id99}"
    if yz:
        data += f"&yz={yz}"
    data += f"&safeid={MOMOZHEN_SAFEID}"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_click({c}, {id}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_click_{c}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_click({c}, {id}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_click({c}, {id}) 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_v_intel(id: str="2", Referer: str=None):
    """
    处理 `fyg_v_intel` 接口的请求。

    :param id: 请求参数 1
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数:
    
    id=1: 进攻野怪
    id=2: 进攻玩家
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer
    else:
        local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_pk.php"

    path = "/fyg_v_intel.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"id={id}&safeid={MOMOZHEN_SAFEID}"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_v_intel({id}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_v_intel_{id}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_v_intel({id}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_v_intel({id}) 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_shop_click(c: str, Referer: str=None):
    """
    处理 `fyg_shop_click` 接口的请求。

    :param c: 请求参数 1
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数:

    c=2: SVIP (30天)
        价格: 10星晶
    c=4: 100W贝壳
        价格: 50星沙
    c=5: [日限]10W贝壳
        价格: 1星沙
    c=6: [日限]120W贝壳
        价格: 1星晶
    c=7: 体能刺激药水
        价格: 20星沙
    c=11: [日限]BVIP打卡包
        价格: 免费
    c=12: [日限]SVIP打卡包
        价格: 免费
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer
    else:
        local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_shop.php"

    path = "/fyg_shop_click.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"c={c}&safeid={MOMOZHEN_SAFEID}"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_shop_click({c}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_shop_click_{c}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_shop_click({c}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_shop_click({c}) 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_s_int(Referer: str=None):
    """
    处理 `fyg_s_int` 接口的请求。

    骰子战争 开始 1 次战斗
        价格: 1星晶

    :param Referer: 请求来源
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer
    else:
        local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_shop.php"

    path = "/fyg_s_int.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"safeid={MOMOZHEN_SAFEID}"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_v_intel({id}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_v_intel_{id}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_v_intel({id}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_v_intel({id}) 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_llpw_c(iu: str, Referer: str=None):
    """
    处理 `fyg_llpw_c` 接口的请求。

    注1: 不想每7天告诉别人一次新密钥的话, 请点击密钥延期, 保持旧密钥可登录
    注2: 不想现有密钥再被使用, 直接点击生成新密钥即可, 旧密钥即时失效
    注3: 密钥登录无法购买星晶
    注4: 密钥登录无法将红色装备丢弃到沙滩
    注5: 密钥登录无法熔炼/销毁红色装备

    :param iu: 请求参数 1
    :param Referer: 请求来源

    :return: 请求的结果文本

    已知接口参数:

    iu=1: 生成新的密钥
    iu=2: 当前密钥延期7天
    iu=3: 允许 进入商店
    iu=4: 禁止 进入商店
    """
    local_headers = kf_momozhen_headers.copy()
    if Referer:
        local_headers["Referer"] = Referer
    else:
        local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_llpw.php"

    path = "/fyg_llpw_c.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"

    data = f"iu={iu}"
    local_headers["Content-Length"] = str(len(data))

    try:
        response = requests.post(url, headers=local_headers, data=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_llpw_c({iu}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, f"fyg_llpw_c_{iu}_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_llpw_c({iu}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_llpw_c({iu}) 失败: {e}", level="error")
        return ""
    
    return response.text

# ------------------------------
# 咕咕镇的一些页面请求
# ------------------------------

def kf_momozhen_fyg_index():
    """
    模仿点击 `fyg_index` 页面
    """
    path = "/fyg_index.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    try:
        response = requests.get(url, headers=kf_momozhen_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_index 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_index_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_index (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_index 失败: {e}", level="error")
        return ""
    
    # 页面的额外信息
    kf_momozhen_fyg_read("22", url) # 当前出战人物，光环，争夺狗牌数量
    kf_momozhen_fyg_read("10", url) # 翻牌信息
    return response.text

def kf_momozhen_fyg_stat():
    """
    模仿点击 `fyg_stat` 页面

    全站战绩统计
    """
    path = "/fyg_stat.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_stat 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_stat_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_stat (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_stat 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_ulog():
    """
    模仿点击 `fyg_ulog` 页面

    更新日志
    """
    path = "/fyg_ulog.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_ulog 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_ulog_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_ulog (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_ulog 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_llpw():
    """
    模仿点击 `fyg_llpw` 页面

    生成临时登录信息 (密钥, 授权他人登录)
    """
    path = "/fyg_llpw.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_llpw 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_llpw_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_llpw (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_llpw 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_beach():
    """
    模仿点击 `fyg_beach` 页面
    """
    path = "/fyg_beach.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_beach 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_beach_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_beach (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_beach 失败: {e}", level="error")
        return ""
    
    # 页面的额外信息
    kf_momozhen_fyg_read("1", url) # 沙滩装备信息
    kf_momozhen_fyg_read("2", url) # 仓库装备信息
    kf_momozhen_fyg_read("9", url) # 当前出战人物 具体信息
    return response.text

def kf_momozhen_fyg_pk():
    """
    模仿点击 `fyg_pk` 页面
    """
    path = "/fyg_pk.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_pk 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_pk_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_pk (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_pk 失败: {e}", level="error")
        return ""
    
    # 页面的额外信息
    kf_momozhen_fyg_read("12", url) # 当前 出击 具体信息
    kf_momozhen_fyg_read("25", url) # 当前 出击 历史信息

    return response.text

def kf_momozhen_fyg_wish():
    """
    模仿点击 `fyg_wish` 页面
    """
    path = "/fyg_wish.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_wish 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_wish_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_wish (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_wish 失败: {e}", level="error")
        return ""
    
    return response.text

def kf_momozhen_fyg_gem():
    """
    模仿点击 `fyg_gem` 页面
    """
    path = "/fyg_gem.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_gem 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_gem_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_gem (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_gem 失败: {e}", level="error")
        return ""
    
    # 页面的额外信息
    kf_momozhen_fyg_read("21", url) # 宝石工坊 进度信息
    
    return response.text

def kf_momozhen_fyg_shop():
    """
    模仿点击 `fyg_shop` 页面
    """
    path = "/fyg_shop.php"
    url = f"{MOMOZHEN_BASE_URL}{path}"
    local_headers = kf_momozhen_headers.copy()
    local_headers["Referer"] = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    try:
        response = requests.get(url, headers=local_headers)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 fyg_shop 失败 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(response.text, "fyg_shop_fail", "kf_momozhen", response.encoding)
        return ""
    except requests.RequestException as e:
        log_message(f"请求 fyg_shop (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 fyg_shop 失败: {e}", level="error")
        return ""
    
    # 页面的额外信息
    kf_momozhen_fyg_read("16", url) # 骰子战争等级 + {星晶/星沙/贝壳} 数量
    kf_momozhen_fyg_read("17", url) # 商店 对账信息
    return response.text


# ------------------------------
# 咕咕镇的一些操作
# ------------------------------

def kf_momozhen_beach_refresh(times: int=10):
    """
    刷新沙滩

    :param times: 刷新次数
    """
    beach_url = f"{MOMOZHEN_BASE_URL}/fyg_beach.php"

    # 刷新沙滩
    for _ in range(times):
        response_text = kf_momozhen_fyg_click("12", Referer=beach_url)
        if "今日强制刷新次数已达上限" in response_text:
            log_message(f"达到上限退出: {response_text}")
            break
        log_message(f"沙滩刷新成功: {response_text}")
        kf_momozhen_fyg_beach()
        time.sleep(1)
    return

def kf_momozhen_beach_extract_data_content(data_content: str):
    """
    从 装备 的 `data-content` 中提取装备属性信息
    """
    try:
        # 将 data-content 字符串转化为 BeautifulSoup 对象以解析 HTML
        soup = BeautifulSoup(data_content, 'html.parser')

        # 初始化一个列表来保存每个 p 标签处理后的文本
        formatted_texts = []

        # 查找所有的 p 标签
        p_tags = soup.find_all('p')

        for p in p_tags:
            # 对于每个 <p> 标签内的 <span> 标签，提取文本，去除 &nbsp;，加入括号
            for span in p.find_all('span'):
                span_text = span.text.replace(u'\xa0', ' ').strip()
                # 替换原 <span> 标签为格式化后的文本
                span.replace_with(f"({span_text})")

            formatted_texts.append(p.get_text(separator=" ", strip=True))

        # 将所有处理后的文本用换行符连接起来
        return "\n".join(formatted_texts)
    except Exception as e:
        log_message(f"解析装备属性失败: {e}", level="error")
        attributes_text = ""

    return attributes_text

def kf_momozhen_beach_print_equipment(html_content: str):
    """
    打印沙滩装备
    """
    try:
        level_pattern = r'Lv\.<span class=\'fyg_f18\'>(\d+)</span>'
        name_pattern = r'</span>.*?<br>\s*(.*?)$'
        id_pattern = r"zbtip\('(\d+)',"
        rarity_pattern = r'url\(ys/icon/z/z\d+_(\d)\.gif\);'

        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找所有的 button 元素
        buttons = soup.find_all('button')

        for idx, button in enumerate(buttons):
            # 提取等级和名称
            title = button.get('title')
            level_match = re.search(level_pattern, title)
            level = level_match.group(1) if level_match else 'Unknown'

            name_match = re.search(name_pattern, title)
            equipment_name = name_match.group(1) if name_match else 'Unknown'

            # 提取 ID
            onclick_attr = button.get('onclick')
            id_match = re.search(id_pattern, onclick_attr)
            id = id_match.group(1) if id_match else 'Unknown'

            # 提取装备稀有度
            style_attr = button.get('style')
            rarity_match = re.search(rarity_pattern, style_attr)
            rarity = rarity_match.group(1) if rarity_match else 'Unknown'

            # 使用 BeautifulSoup 提取 data-content 属性，并用正则表达式作为辅助解析属性值
            data_content = button.get('data-content')
            attributes = kf_momozhen_beach_extract_data_content(data_content)

            # Compiling extracted information
            info = f"{idx}. {equipment_name}({rarity})\nLv. {level}\nID = {id}\n" + attributes + "\n"
            
            # Printing the information for each equipment
            log_message(info)
            level_range = convert_number_to_range(level, 20)
            json_data_handler.increment_value(1, CURRENT_MONTH, "沙滩装备", equipment_name, rarity, level_range)
    except Exception as e:
        log_message(f"打印沙滩装备失败: {e}", level="error")
        save_string_as_file(html_content, "kf_momozhen_beach_print_fail", "kf_momozhen")

    return

def kf_momozhen_beach_extract_equipment_ids(html_content: str):
    """
    提取沙滩符合条件的 装备 (ID)

    :param html_content: 沙滩页面的 HTML 内容
    """
    # Define the pattern to extract the necessary information
    pattern = r'background-image:url\(.*?_(\d+)\.gif\).*?title="Lv\.<span class=\'fyg_f18\'>(\d+)</span>.*?onclick="zbtip\(\'(\d+)\','
    # pattern = r'background-image:url\(.*?_([3-9])\.gif\).*?title="Lv\.<span class=\'fyg_f18\'>(\d+)</span>.*?onclick="zbtip\(\'(\d+)\','
    matches = re.findall(pattern, html_content, re.DOTALL)
    
    # Define the minimum level requirement for each rarity
    rarity_level_requirements = {
        '3': 295,
        '4': 280,
        '5': 260,
        '6': 250,
        '7': 250,
        '8': 0,
        '9': 0,
        # Extend as needed for higher rarities
    }
    min_melt_rarity = 3
    
    # Filter and collect the IDs based on rarity and level requirements
    pick_ids = []
    melt_ids = []
    for rarity, level, equipment_id in matches:
        if int(level) >= rarity_level_requirements.get(rarity, 999):
            pick_ids.append(equipment_id)
            json_data_handler.increment_value(1, CURRENT_MONTH, "沙滩", "pick_count", rarity)
        elif int(rarity) >= min_melt_rarity:
            melt_ids.append(equipment_id)
            json_data_handler.increment_value(1, CURRENT_MONTH, "沙滩", "melt_count", rarity)
        else:
            json_data_handler.increment_value(1, CURRENT_MONTH, "沙滩", "clean_count", rarity)
    
    return pick_ids, melt_ids

def kf_momozhen_beach_pick_equipment_with_id(equipment_ids: list):
    """
    领取沙滩装备 {id}
    """
    beach_url = f"{MOMOZHEN_BASE_URL}/fyg_beach.php"
    keyword = "仓库已满"

    log_message(f"领取装备: {equipment_ids}")

    for idx, equipment_id in enumerate(equipment_ids):
        response_text = kf_momozhen_fyg_click("1", id=equipment_id, Referer=beach_url)
        if response_text: # 如果不为空字符串, 则说明领取成功
            log_message(f"领取沙滩装备 {equipment_id} 成功: {response_text}")
        if keyword in response_text:
            log_message(f"仓库已满: {response_text}")
            break
        if idx % 7 == 0:
            time.sleep(1)
    return

def kf_momozhen_beach_get_equipment_pirlyz(html_content: str):
    """
    找到熔炼装备的验证参数
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 使用 BeautifulSoup 查找 id 为 'pirlyz' 的 <input> 元素
        pirlyz_input = soup.find('input', id='pirlyz')

        if pirlyz_input:
            return pirlyz_input.get('value')
        
        # 如果失败，使用正则表达式匹配 'pirlyz' 的值
        match = re.search(r'id="pirlyz" value="(\d+)"', html_content)
        if match:
            return match.group(1)
    except Exception as e:
        log_message(f"获取熔炼装备的验证参数失败: {e}", level="error")

    return ""

def kf_momozhen_beach_get_amulet_info(html_content: str):
    """
    获取护符信息

    :param html_content: 沙滩页面的 HTML 内容

    :return: (名称, 效果项, 数字, 单位)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # 使用正则表达式匹配 class 名称中包含任意两位数数字的标签
        name_tag_regex = re.compile(r'fyg_colpz\d{2}bg')
        effect_tag_regex = re.compile('bg-special')

        # 查找护符名称，考虑到可能有多种不同的数字结尾
        name_tag = soup.find('p', class_=name_tag_regex)
        if name_tag:
            name = name_tag.get_text(strip=True)
        else:
            name = "未找到名称"
            save_string_as_file(html_content, "fyg_amulet_fail", "kf_momozhen")

        # 查找效果项、数字和单位
        effect_tag = soup.find('p', class_=effect_tag_regex)
        if effect_tag:
            effect_text = effect_tag.get_text(strip=True)
            # 使用正则表达式从效果文本中提取信息
            effect_match = re.search(r'(.+?)(\d+)(\s*[%点])', effect_text)
            if effect_match:
                effect = effect_match.group(1).strip()
                number = effect_match.group(2).strip()
                unit = effect_match.group(3).strip()
            else:
                effect, number, unit = "未找到效果", "9999", "未找到单位" # 确保未知情况下不会销毁护符
                save_string_as_file(html_content, "fyg_amulet_fail", "kf_momozhen")
        else:
            effect, number, unit = "未找到效果", "9999", "未找到单位"
            save_string_as_file(html_content, "fyg_amulet_fail", "kf_momozhen")

    except Exception as e:
        log_message(f"获取护符信息失败: {e}", level="error")
        save_string_as_file(html_content, "fyg_amulet_fail", "kf_momozhen")
        name, effect, number, unit = "未找到名称", "未找到效果", "9999", "未找到单位"

    return name, effect, number, unit

def kf_momozhen_beach_melt_equipment_with_id(equipment_ids: list):
    """
    熔炼沙滩装备 {id} 为 护符
    """
    beach_url = f"{MOMOZHEN_BASE_URL}/fyg_beach.php"

    # 简称: 苹果,葡萄,樱桃
    amulet_min_effect = {
        "苹果": 5, # 星铜苹果护身符
        "葡萄": 2, # 蓝银葡萄护身符
        "樱桃": 1, # 紫晶樱桃护身符
    }
    amulet_yz = "124"

    log_message(f"熔炼装备: {equipment_ids}")

    for idx, equipment_id in enumerate(equipment_ids):
        # ca = "3" 为 仓库装备
        # ca = "4" 为 沙滩装备
        response_text = kf_momozhen_fyg_read("20", id=equipment_id, ca="4", Referer=beach_url)
        if not response_text:
            continue
        pirlyz = kf_momozhen_beach_get_equipment_pirlyz(response_text)

        amulet_id = kf_momozhen_fyg_click("9", id=equipment_id, yz=pirlyz, Referer=beach_url)
        if not amulet_id:
            continue
        # ca = "2" 为护符
        response_text = kf_momozhen_fyg_read("20", id=amulet_id, ca="2", Referer=beach_url)

        if not response_text:
            continue

        name, effect, number, unit = kf_momozhen_beach_get_amulet_info(response_text)

        log_message(f"熔炼装备 {equipment_id} 为 {name} : {effect} {number} {unit}")
        json_data_handler.increment_value(1, CURRENT_MONTH, "护符信息", name, number)

        # 如果不满足则销毁
        # if name in amulet_min_effect and int(number) < amulet_min_effect[name]:
        #     log_message(f"销毁护符 {name}: {effect} {number} {unit}")
        #     kf_momozhen_fyg_click("9", id=amulet_id, yz=amulet_yz, Referer=beach_url)
        for amulet_name, min_effect in amulet_min_effect.items():
            if amulet_name in name and int(number) >= min_effect:
                log_message(f"保留护符 {name}: {effect} {number} {unit}")
                break
            if amulet_name in name:
                log_message(f"销毁护符 {name}: {effect} {number} {unit}")
                kf_momozhen_fyg_click("9", id=amulet_id, yz=amulet_yz, Referer=beach_url)
                break
        if idx % 7 == 0:
            time.sleep(1)
    return

def kf_momozhen_beach_pick_equipment():
    """
    领取沙滩装备
    """
    beach_url = f"{MOMOZHEN_BASE_URL}/fyg_beach.php"
    response_text = kf_momozhen_fyg_read("1", beach_url)
    time.sleep(1)
    if response_text:
        log_message(f"沙滩装备: \n")
        kf_momozhen_beach_print_equipment(response_text)
        save_string_as_file(response_text, "fyg_beach_equipment", "kf_momozhen")

        log_message(f"领取装备: \n")
        pick_ids, melt_ids = kf_momozhen_beach_extract_equipment_ids(response_text)
        kf_momozhen_beach_pick_equipment_with_id(pick_ids)

        log_message(f"熔炼装备: \n")
        kf_momozhen_beach_melt_equipment_with_id(melt_ids)
    else:
        log_message("沙滩无装备")
    return

def kf_momozhen_beach_clear():
    """
    清理沙滩
    """
    beach_url = f"{MOMOZHEN_BASE_URL}/fyg_beach.php"
    response_text = kf_momozhen_fyg_click("20", Referer=beach_url)
    if response_text:
        log_message(f"清理沙滩成功: {response_text}")
    return

def kf_momozhen_wish_get_result(html_content: str):
    """
    解析许愿池结果
    """
    try:
        # 使用 BeautifulSoup 解析 HTML 内容
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找所有的 <p> 标签
        paragraphs = soup.find_all('p')
        if not paragraphs:
            # 如果没有 <p> 标签，直接返回原文本
            return html_content

        # 提取每个 <p> 标签中的文本，并用换行符连接
        extracted_texts = [p.get_text() for p in paragraphs]
        for text in extracted_texts:
            json_data_handler.increment_value(1, CURRENT_MONTH, "许愿池", "词条次数", text)
        return '\n'.join(extracted_texts)
    except Exception as e:
        log_message(f"解析许愿池结果失败: {e}", level="error")
        save_string_as_file(html_content, "fyg_wish_result_fail", "kf_momozhen")
        return html_content

def kf_momozhen_wish(max_attempts=100):
    """
    许愿池

    TODO: 未来在某一项满时添加检查 (关键词), 自动重试, 直到许愿成功 (待检查)
    """
    kf_momozhen_fyg_wish()

    wish_url = f"{MOMOZHEN_BASE_URL}/fyg_wish.php"
    attempt = 0
    keyword = "重新许愿" # "许愿到已满的词条，提升失败，贝壳退还，请重新许愿。"

    response_text = kf_momozhen_fyg_click("18", id="10", Referer=wish_url)

    while keyword in response_text and attempt < max_attempts:
        log_message(f"许愿到已满的词条, 重试中... ({attempt})")
        response_text = kf_momozhen_fyg_click("18", id="10", Referer=wish_url)
        # save_string_as_file(response_text, "fyg_wish", "kf_momozhen")
        attempt += 1
        if attempt % 5 == 0:
            time.sleep(1) # 每5次休息1秒

    if response_text:
        result = kf_momozhen_wish_get_result(response_text)
        log_message(f"许愿池请求成功: {result}")
        save_string_as_file(response_text, "fyg_wish", "kf_momozhen")
    
    return

def kf_momozhen_gem_parse_activity_time(activity_text: str):
    """从活动文本中解析当前值、增速和计算剩余时间"""
    numbers = re.findall(r'\d+\.?\d*', activity_text)
    current_value = float(numbers[0])
    rate_per_minute = float(numbers[-1])
    return current_value, rate_per_minute

def kf_momozhen_gem_parse_activity_sand(activity_text: str):
    """从星沙活动文本中特殊解析当前值、增速"""
    # 先找到括号内的数字作为当前值
    current_value_match = re.search(r'\((\d+\.\d+)\)', activity_text)
    current_value = float(current_value_match.group(1)) if current_value_match else 0
    # 解析每分钟增速
    rate_per_minute_match = re.search(r'每分钟 \+(\d+\.?\d*)星沙', activity_text)
    rate_per_minute = float(rate_per_minute_match.group(1)) if rate_per_minute_match else 0
    return current_value, rate_per_minute

def kf_momozhen_gem_shell(text: str, begin_minutes=0):
    """
    将 "已拾取1640贝壳Lv.656 伊 (赶海中...)红石25每分钟 +205贝壳"
    转换为 "已拾取 1640 贝壳 (每分钟 + 205 贝壳) 剩余 81 小时 11 分"
    """
    shell_max = 1000000  # 单次贝壳产出上限
    current_value, rate_per_minute = kf_momozhen_gem_parse_activity_time(text)
    minutes = compute_remaining_time(shell_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    log_message(f"已拾取 {current_value} 贝壳 (每分钟 +{rate_per_minute}贝壳) 剩余 {format_remaining_time(remaining_time)}")

def kf_momozhen_gem_sand(text: str, begin_minutes=0):
    """
    将 "已开采0星沙(0.0104)Lv.656 霞 (挖矿中...)虚石0每分钟 +0.0013星沙"
    转换为 "已开采 0星沙(0.0104) (每分钟 + 0.0013 星沙) 剩余 128 小时 5 分, 距下一整数 12 小时 42 分"
    """
    sand_max = 10  # 单次星沙产出上限
    current_value, rate_per_minute = kf_momozhen_gem_parse_activity_sand(text)
    minutes = compute_remaining_time(sand_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    next_int_minutes = compute_time_to_next_integer(begin_minutes, rate_per_minute)

    remaining_time_str = format_remaining_time(remaining_time)
    next_int_minutes_str = format_remaining_time(next_int_minutes)
    log_message(f"已开采 {current_value} 星沙 (每分钟 +{rate_per_minute}星沙) 剩余 {remaining_time_str}, 距下一整数 {next_int_minutes_str}")

def kf_momozhen_gem_experience(text: str, begin_minutes=0):
    """
    将 "已获得0幻影经验Lv.656 希 (闭关中...)幻石0每分钟 +0.038幻影经验"
    转换为 "已获得 0 幻影经验 (每分钟 +0.038 幻影经验) 剩余 87 小时 36 分, 每点需要 0 小时 19 分"
    """
    experience_max = 200  # 单次幻影经验产出上限
    current_value, rate_per_minute = kf_momozhen_gem_parse_activity_time(text)
    minutes = compute_remaining_time(experience_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    next_int_minutes = compute_time_to_next_integer(begin_minutes, rate_per_minute)

    remaining_time_str = format_remaining_time(remaining_time)
    next_int_minutes_str = format_remaining_time(next_int_minutes)
    log_message(f"已获得 {current_value} 幻影经验 (每分钟 +{rate_per_minute}幻影经验) 剩余 {remaining_time_str}, 距下一整数 {next_int_minutes_str}")

def kf_momozhen_gem_percent_items(text: str, begin_minutes=0):
    """
    将 "0.416%概率出产{item_name}Lv.656 琳 (组装中...)银石20每分钟 +0.052%概率"
    转换为 "0.416% 概率出产 {item_name} (每分钟 +0.052% 概率) 剩余 31 小时 56 分"
    """
    item_name = re.search(r"概率出产 (.+?) Lv", text).group(1)
    percent_max = 100  # 假设概率满值为100%
    current_value, rate_per_minute = kf_momozhen_gem_parse_activity_time(text)
    minutes = compute_remaining_time(percent_max, rate_per_minute)
    remaining_time = minutes - begin_minutes
    remaining_time = max(remaining_time, 0) # 确保 remaining_time 大于等于0
    log_message(f"{current_value}% 概率出产 {item_name} (每分钟 +{rate_per_minute}%概率) 剩余 {format_remaining_time(remaining_time)}")

def kf_momozhen_gem_print_items(html_content: str, begin_minutes=0):
    """
    打印宝石工坊的相关信息
    """
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取相关信息
    activities = soup.find_all("div", class_="alert alert-info fyg_f14 fyg_lh30")
    
    for activity in activities:
        text = activity.get_text(separator=" ", strip=True)
        if "贝壳" in text:
            kf_momozhen_gem_shell(text, begin_minutes)
        elif "星沙" in text:
            kf_momozhen_gem_sand(text, begin_minutes)
        elif "幻影经验" in text:
            kf_momozhen_gem_experience(text, begin_minutes)
        elif "概率出产" in text:
            kf_momozhen_gem_percent_items(text, begin_minutes)
        else:
            log_message(text)
    return

def kf_momozhen_gem_find_work_hours() -> int:
    """
    尝试找到已开工 {int} 小时
    If no such information is found, returns 0.
    """
    gen_url = f"{MOMOZHEN_BASE_URL}/fyg_gem.php"
    response_text = kf_momozhen_fyg_read("21", gen_url)

    if not response_text:
        return 0
    
    soup = BeautifulSoup(response_text, 'html.parser')
    buttons = soup.find_all('button')
    for button in buttons:
        if "已开工" in button.text:
            pattern = r"(\d+)小时(\d+)分钟"
            match = re.search(pattern, button.text)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                total_minutes = calculate_total_minutes(minutes, hours=hours)
                log_message(f"宝石工坊已开工 {hours} 小时 {minutes} 分钟")
                kf_momozhen_gem_print_items(response_text, total_minutes)
                return hours
            
    log_message(f"宝石工坊读取失败")
    kf_momozhen_gem_print_items(response_text)
    return 0

def kf_momozhen_gem_get_result(html_content: str):
    """
    从宝石工坊的领取结果中提取结果
    """
    try:
        # 使用 BeautifulSoup 解析 HTML 内容
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找所有的 <p> 标签
        paragraphs = soup.find_all('p')
        if not paragraphs:
            # 如果没有 <p> 标签，直接返回原文本
            return html_content

        # 提取每个 <p> 标签中的文本，并用换行符连接
        extracted_texts = [p.get_text() for p in paragraphs]
        return '\n'.join(extracted_texts)
    except Exception as e:
        log_message(f"解析宝石工坊领取结果时出错: {e}", level="error")
        save_string_as_file(html_content, "fyg_gem_result_fail", "kf_momozhen")
        return html_content

def kf_momozhen_gem_data_collection(text: str):
    """
    统计宝石工坊的数据
    """
    patterns = {
        "贝壳": r"收获(\d+)枚贝壳",
        "星沙": r"收获(\d+)粒星沙",
        "幻影等级经验": r"感悟(\d+)幻影等级经验",
        "随机装备箱": r"随机装备箱x(\d+)",
        "灵魂药水": r"灵魂药水x(\d+)",
        "宝石原石": r"宝石原石x(\d+)"
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        # 没有则为0
        value = sum([int(match) for match in matches]) if matches else 0
        json_data_handler.increment_value(value, CURRENT_MONTH, "宝石工坊", "奖励", key)

def kf_momozhen_gem():
    """
    宝石工坊 开工 / 收工
    """
    kf_momozhen_fyg_gem()

    gem_url = f"{MOMOZHEN_BASE_URL}/fyg_gem.php"
    response_text = kf_momozhen_fyg_click("30", Referer=gem_url)

    if response_text:
        result = kf_momozhen_gem_get_result(response_text)
        log_message(f"宝石工坊 开工 / 收工: {result}")
        if "收工统计" in result:
            kf_momozhen_gem_data_collection(result)
    return

def kf_momozhen_use_energy():
    """
    使用体力药水
    """
    index_url = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    response_text = kf_momozhen_fyg_click("13", id="2", Referer=index_url) # 'c=13&id=2&safeid=5cda2b'

    keywords = ["无法使用"]
    
    log_message(f"使用体力药水: {response_text}")
    if contains_keywords(response_text, keywords):
        log_message("无法使用体力药水, 结束")
        return False
    json_data_handler.increment_value(1, CURRENT_MONTH, "使用体力药水", "次数")

    return True

def kf_momozhen_find_SVIP() -> str:
    """
    尝试找到 SVIP透视 在 class "text-muted" 里.
    If no such text is found, returns an empty string.
    """
    index_url = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    response_text = kf_momozhen_fyg_read("10", index_url)

    if not response_text:
        return ""
    
    soup = BeautifulSoup(response_text, 'html.parser')
    text_muted = soup.find(class_="text-muted")
    svip_str = text_muted.get_text(strip=True) if text_muted else ""
    
    log_message(f"尝试获取SVIP透视: {svip_str}")
    return svip_str

def kf_momozhen_card_value():
    """
    蓝色: 幸运 "btn-info"
    绿色: 稀有 "btn-success"
    黄色: 史诗 "btn-warning"
    红色: 传说 "btn-danger"
    
    :return: blue_value, green_value, yellow_value, red_value
    """
    # 
    index_url = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    response_text = kf_momozhen_fyg_read("10", index_url) # 翻牌信息

    blue, green, yellow, red = 0, 0, 0, 0

    # 分割整个HTML文本为多个部分，每个部分代表一个卡牌
    parts = response_text.split('<div class="col-sm-1">')
    
    # 遍历每个部分
    for part in parts:
        # 检查卡牌的类型并更新相应的计数器
        if 'btn-info' in part:  # 蓝色
            blue += 1
        elif 'btn-success' in part:  # 绿色
            green += 1
        elif 'btn-warning' in part:  # 黄色
            yellow += 1
        elif 'btn-danger' in part:  # 红色
            red += 1
    return blue, green, yellow, red
    
def kf_momozhen_fanpai_prin_result(html_content: str):
    try:
        # 使用BeautifulSoup解析给定的HTML内容
        soup = BeautifulSoup(html_content, 'html.parser')

        # 找到所有的<p>标签
        p_tags = soup.find_all('p')

        # 提取每个<p>标签的文本内容
        for p in p_tags:
            log_message(p.get_text().strip())
    except Exception as e:
        log_message(f"解析翻牌结果时出错: {e}", level="error")
        save_string_as_file(html_content, "fyg_fanpai_fail", "kf_momozhen")
    return

def kf_momozhen_fanpai_data_collection(text: str):
    """
    统计翻牌数据
    """
    patterns = {
        "贝壳": r"获得(\d+)贝壳",
        "争夺经验": r"(\d+)争夺经验",
        "随机装备箱": r"随机装备箱 x (\d+)",
        "灵魂药水": r"灵魂药水 x (\d+)",
        "锻造材料箱": r"锻造材料箱 x (\d+)",
        "光环天赋石": r"光环天赋石 x (\d+)",
        "体能刺激药水": r"体能刺激药水 x (\d+)"
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)
        # 没有则为0
        value = sum([int(match) for match in matches]) if matches else 0
        json_data_handler.increment_value(value, CURRENT_MONTH, "翻牌", "奖励", key)

def kf_momozhen_fanpai():
    """
    12张牌里有蓝、绿、黄、红各三张。每次翻一张牌。当任意颜色的三张牌被翻出时, 则获得该三张牌对应品质的奖励。
    """
    kf_momozhen_fyg_index()
    index_url = f"{MOMOZHEN_BASE_URL}/fyg_index.php"
    
    ids = list(range(2, 13))  # 创建一个从2到12的列表, 代表12张牌的id
    svip_str = kf_momozhen_find_SVIP()

    first_card_decision = True  # 第一张牌的决策，默认等待

    # 根据透视结果处理第一张牌
    if not svip_str:
        # 如果 svip_str 寻找失败, 则把第一张卡牌加入到 ids 列表中
        ids.insert(0, 1)
        first_card_decision = False
        log_message("未找到 SVIP 透视")
    elif "传说" in svip_str:
        # 如果第一张是红色，直接翻开
        kf_momozhen_fyg_click("8", id=str(1), Referer=index_url)
        first_card_decision = False
        log_message("根据 SVIP 透视翻开第一张牌")
    elif "幸运" in svip_str:
        first_card_decision = False
        log_message("根据 SVIP 透视跳过第一张牌")

    for _ in range(len(ids)):
        response_text = ""
        blue, green, yellow, red = kf_momozhen_card_value()
        log_message(f"蓝色: {blue}, 绿色: {green}, 黄色: {yellow}, 红色: {red}")
        card_id = None

        # 决定是否翻开第一张牌
        if first_card_decision:
            # 首先尝试追求 3 张红色, 然后判断是否要保底

            # 如果有两张蓝色或两张绿色, 保底黄色
            if yellow == 2 and "史诗" in svip_str and (blue == 2 or green == 2):
                log_message("根据透视翻开保底 史诗")
                first_card_decision = False
                card_id = 1

                # response_text = kf_momozhen_fyg_click("8", id=str(1), Referer=index_url)

            # 如果有两张蓝色和两张绿色, 保底绿色
            elif green == 2 and "稀有" in svip_str and blue == 2: 
                log_message("根据透视翻开保底 稀有")
                first_card_decision = False
                card_id = 1

                # response_text = kf_momozhen_fyg_click("8", id=str(1), Referer=index_url)

        if card_id is None:
            # 随机选择一个id, 然后从列表中移除这个id, 以确保下次不会重复选择
            card_id = random.choice(ids)
            ids.remove(card_id)

        response_text = kf_momozhen_fyg_click("8", id=str(card_id), Referer=index_url)
        log_message(f"成功翻开牌 ({card_id})")

        if "今日已获取奖励" in response_text:
            log_message(f"今日已达到上限退出: {response_text}")
            return False
        if "请刷新后重试" in response_text:
            log_message(f"需刷新: {response_text}")
            return True
        
        if response_text.strip():
            blue, green, yellow, red = kf_momozhen_card_value()
            kf_momozhen_fanpai_prin_result(response_text)
            kf_momozhen_fanpai_data_collection(response_text)
            if blue == 3:
                json_data_handler.increment_value(1, CURRENT_MONTH, "翻牌", "次数统计", "幸运")
                break
            if green == 3:
                json_data_handler.increment_value(1, CURRENT_MONTH, "翻牌", "次数统计", "稀有")
                break
            if yellow == 3:
                json_data_handler.increment_value(1, CURRENT_MONTH, "翻牌", "次数统计", "史诗")
                break
            if red == 3:
                json_data_handler.increment_value(1, CURRENT_MONTH, "翻牌", "次数统计", "传说")
                break

    return False

def kf_momozhen_extract_battle_info(html_content: str):
    """解析 html_str 中的战斗信息, 并打印输出"""
    if "达到上限" in html_content and len(html_content) <= 50:
        log_message(html_content)
        return -3

    # try except, 如果失败设为空字符""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the names and stats of the participants
        participants = soup.find_all(class_='fyg_f18')
        stats = soup.find_all('span', class_='label-outline')
    
        # Extracting names and stats
        # name_1 = participants[0].get_text().strip()
        name_1 = "User"
        stats_1 = ' / '.join([stat.get_text().strip() for stat in stats[:2]])
        name_2 = participants[1].get_text().strip()
        stats_2 = ' / '.join([stat.get_text().strip() for stat in stats[3:5]])
    except:
        name_1 = "Unknown"
        stats_1 = "Unknown"
        name_2 = "Unknown"
        stats_2 = "Unknown"
        save_string_as_file(html_content, "battle_info_fail", "kf_momozhen", "utf-8")
    
    # Determine the winner
    try:
        winner_text = soup.find(
            'div',
            class_='alert alert-danger with-icon fyg_tc').get_text().strip()
        winner_text = "User"
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
    log_message(output)
    return -2

def kf_momozhen_battle(num_battles: int=20):
    """
    开始 {num_battles} 次争夺（打人）, 遇到平局时增加额外的循环

    :param num_battles: 争夺次数 (默认 20)
    """
    kf_momozhen_fyg_pk()
    pk_url = f"{MOMOZHEN_BASE_URL}/fyg_pk.php"
    
    # 初始化胜负平统计
    win_count, lose_count, draw_count, error_count = 0, 0, 0, 0
    attempts = 0  # 已尝试次数

    for _ in range(num_battles * 2):
        if attempts >= num_battles:
            break

        response_text = kf_momozhen_fyg_v_intel("2", Referer=pk_url)

        if not response_text:
            error_count += 1
            continue

        if "今日已主动出击20次" in response_text:
            log_message(f"达到上限退出: {response_text}")
            break
        if "刷新页面" in response_text:
            log_message(f"需刷新: {response_text}")
            return True
        
        log_message("成功: ")
        result = kf_momozhen_extract_battle_info(response_text)
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
        else:
            error_count += 1
            log_message("出错了")

    # 打印统计结果
    log_message(f"统计结果: 胜:{win_count} 负:{lose_count} 平:{draw_count} 错误:{error_count}")
    json_data_handler.increment_value(win_count, CURRENT_MONTH, "battle", "win_count")
    json_data_handler.increment_value(lose_count, CURRENT_MONTH, "battle", "lose_count")
    json_data_handler.increment_value(draw_count, CURRENT_MONTH, "battle", "draw_count")
    json_data_handler.increment_value(error_count, CURRENT_MONTH, "battle", "error_count")
    return False

def kf_momozhen_try_operation(operation: Callable[[], bool], operation_name: str):
    """
    尝试执行某操作, 最多重试10次。
    如果操作成功, 则返回True, 如果尝试了10次仍未成功, 则返回False。
    """
    for i in range(10):
        if operation():
            set_cookie()  # 刷新headers

            time.sleep(1)
        else:
            log_message(f"{operation_name} 成功, 尝试次数：{i+1}")
            return True
        log_message(f"{operation_name} 尝试重试第 {i+1} 次")
    log_message(f"{operation_name} 尝试了 10 次, 但都失败了")
    return False




# ------------------------------
# 相关步骤
# ------------------------------

def kf_momozhen_process_shop():
    """
    商店购买 体力药水, 免费商品
    """
    kf_momozhen_fyg_shop()

    shop_url = f"{MOMOZHEN_BASE_URL}/fyg_shop.php"

    # [日限]BVIP打卡包
    response_text = kf_momozhen_fyg_shop_click("11", Referer=shop_url)
    if response_text:
        log_message(f"购买 BVIP打卡包: {response_text}")
    
    # [日限]SVIP打卡包
    response_text = kf_momozhen_fyg_shop_click("12", Referer=shop_url)
    if response_text:
        log_message(f"购买 SVIP打卡包: {response_text}")

    # 体能刺激药水 x 4
    keywords = ["已获得"]
    for _ in range(4):
        response_text = kf_momozhen_fyg_shop_click("7", Referer=shop_url)
        if response_text:
            log_message(f"购买 体能刺激药水: {response_text}")
            if not contains_keywords(response_text, keywords):
                break

    return

def kf_momozhen_process_beach():
    """
    刷新 10 次沙滩, 并 处理/领取 沙滩装备
    """
    kf_momozhen_fyg_beach()
    
    # 刷新沙滩
    kf_momozhen_beach_refresh()
    time.sleep(1)

    # 领取沙滩装备
    kf_momozhen_beach_pick_equipment()
    time.sleep(1)

    # 清理沙滩
    kf_momozhen_beach_clear()

    return

def kf_momozhen_process_gem():
    """
    检查宝石工坊, 并处理宝石工坊的活动
    """
    kf_momozhen_fyg_gem()

    gem_hour = kf_momozhen_gem_find_work_hours()
    if gem_hour < 1:
        kf_momozhen_gem() # 开始宝石工坊
    elif gem_hour >= 23: # 可改, 目前32小时正好 1 项满
        kf_momozhen_gem() # 领取宝石工坊
        kf_momozhen_gem() # 开始宝石工坊
    else:
        log_message("宝石工坊未满 32 小时")

    return

def kf_momozhen_process_battle():
    """
    尝试进攻 3 次 (包含使用两次药水的机会)
    """
    for attack_round in range(3):
        # 进攻成功前尝试10次进攻
        kf_momozhen_fyg_pk()
        if not kf_momozhen_try_operation(kf_momozhen_battle, "进攻"):
            break
        time.sleep(1)

        # 翻牌, 如果10次都失败, 则不继续后续操作
        kf_momozhen_fyg_index()
        if not kf_momozhen_try_operation(kf_momozhen_fanpai, "翻牌"):
            break
        time.sleep(1)

        # 前两轮进攻后尝试使用体力药水
        if attack_round < 2:
            if not kf_momozhen_use_energy():
                break
        time.sleep(1)
    return

def kf_momozhen_process_wish():
    """
    许愿池
    """
    kf_momozhen_fyg_wish()
    kf_momozhen_wish()
    return


def kf_momo_test():
    kf_momozhen_fanpai()



# ------------------------------
# 主函数
# ------------------------------

def kf_momozhen():
    """咕咕镇"""
    log_message("\n------------------------------------\n")
    log_message("开始执行 咕咕镇 函数")
    log_message("\n------------------------------------\n")

    current_year = datetime.datetime.now().year
    json_path = f"./data/kf_momozhen_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)

    # 开始执行咕咕镇签到
    kf_momozhen_process_shop()
    time.sleep(1)

    # 开始执行咕咕镇沙滩
    kf_momozhen_process_beach()
    time.sleep(1)

    # 开始执行咕咕镇宝石工坊
    kf_momozhen_process_gem()
    time.sleep(1)

    # 开始执行咕咕镇争夺
    kf_momozhen_process_battle()
    time.sleep(1)

    # 开始执行许愿池
    kf_momozhen_process_wish()

    json_data_handler.write_data()
    
    log_message("\n------------------------------------\n")


def kf_momozhen_start():
    """开始执行 kf 咕咕镇 签到"""
    if not set_cookie():
        return
    # 签到
    kf_momozhen()
    # kf_momo_test()
    
