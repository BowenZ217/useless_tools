import datetime
import os
import random
import re

import requests
from bs4 import BeautifulSoup


from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

CURRENT_MONTH = str(datetime.datetime.now().month)
ZODGAME_BASE_URL = "zodgame.xyz"
ZODGAME_FORMHASH = "417c75e4"

TIME_OUT_TIME = 10  # seconds

ZODGAME_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"https://{ZODGAME_BASE_URL}/index.php",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
}

ZODGAME_MOOD_ID_MATCH = {
	"kx": "￣︶￣",
	"ng": "╯０╰",
	"ym": "@﹏@",
	"wl": "￣.￣.zzZ",
	"nu": "╬￣皿￣",
	"ch": "￣.￣||",
	"fd": "＞д＜",
	"yl": "￣ω￣",
	"shuai": "〒▽〒"
}

def set_cookie():
    cookie_str = os.environ.get("ZODGAME_COOKIE")
    if not cookie_str:
        log_message("请设置环境变量 ZODGAME_COOKIE", level="error")
        return False
    
    global ZODGAME_HEADERS
    ZODGAME_HEADERS["Cookie"] = cookie_str
    return True

# --------------------

def zodgame_pick_random_mood_id():
    mood_id = random.choice(list(ZODGAME_MOOD_ID_MATCH.keys()))
    # log_message(f"随机选择的心情 ({mood_id}) 为 : {ZODGAME_MOOD_ID_MATCH[mood_id]}")
    return mood_id

def zodgame_update_formhash(html_str: str):
    """
    解析页面中的 formhash 并更新全局变量 ZODGAME_FORMHASH
    
    :param html: 页面的 HTML 内容
    """
    try:
        global ZODGAME_FORMHASH
        soup = BeautifulSoup(html_str, "html.parser")
        formhash_input = soup.find("input", {"name": "formhash"})
        if not formhash_input:
            log_message("页面中没有找到 formhash", level="error")
            return False
        formhash_temp = formhash_input.get("value", "")
        if not formhash_temp:
            log_message("找到的 formhash 为空", level="error")
            return False
        if formhash_temp != ZODGAME_FORMHASH:
            ZODGAME_FORMHASH = formhash_temp
            log_message(f"更新 ZODGAME_FORMHASH 为 {ZODGAME_FORMHASH}")
    except Exception as e:
        log_message(f"更新 ZODGAME_FORMHASH 时出现错误: {e}", level="error")
        return False
    return True

def zodgame_extract_sign_in_info(html_str: str):
    """
    从签到页面提取签到信息
    """
    # 用字典存储结果
    result = {}
    try:
        # 解析 HTML
        soup = BeautifulSoup(html_str, 'html.parser')

        # 提取上次签到时间
        last_check_in_time = soup.find(string=re.compile("您上次签到时间")).find_next('font').text
        result['last_check_in_time'] = last_check_in_time  # 上次签到时间

        # 提取总奖励
        total_rewards_text = soup.find(string=re.compile("您目前获得的总奖励为")).find_next('font').text
        total_rewards = int(total_rewards_text)
        result['total_rewards'] = total_rewards  # 总奖励

        # 提取上次获得的奖励
        last_reward_text = soup.find(string=re.compile("上次获得的奖励为")).find_next('font').text
        last_reward = int(last_reward_text)
        result['last_reward'] = last_reward  # 上次获得的奖励

        # 提取升级剩余天数
        remaining_days_text = soup.find(string=re.compile("您只需再签到")).find_next('font').text
        remaining_days = int(remaining_days_text)
        result['remaining_days'] = remaining_days  # 升级剩余天数
    except Exception as e:
        log_message(f"提取签到信息时出现错误: {e}", level="error")
        return {
            'last_check_in_time': '1970-01-01 00:00:00',
            'total_rewards': 0,
            'last_reward': 0,
            'remaining_days': 9999
        }

    return result

def zodgame_extract_sign_in(response_text: str) -> int:
    """
    从签到页面提取签到信息, 并返回酱油的数量
    如果没有找到数量, 则返回 0
    """
    try:
        # 首先检查响应中是否包含某些关键字, 并记录相关信息
        if "已被系统拒绝" in response_text:
            log_message('zodgame 的 cookie 已过期')
            return 0
        elif "恭喜" in response_text:
            log_message("zodgame 签到成功")
        elif '已经签到' in response_text:
            log_message('zodgame 已经签到了')
            return 0
        else:
            log_message(f'zodgame 签到失败: {response_text}')
            return 0
        
        num_pattern = r'酱油 (\d+) 瓶'
        
        # 提取酱油数量
        match = re.search(num_pattern, response_text)
        if match:
            num = int(match.group(1))
            log_message(f"领取酱油数量: {num} 瓶")
            return num
        else:
            log_message(f"没有找到酱油数量信息")
    except Exception as e:
        # 记录异常信息
        log_message(f'在提取签到信息时发生错误: {str(e)}')
    return 0

# ------------------------------
# zodgame 的一些请求接口
# ------------------------------

# 签到接口
def zodgame_sign_in(mood_id: str):
    """
    zodgame 签到

    :param mood_id: 心情 ID

    :return: 签到结果

    """
    url = f"https://{ZODGAME_BASE_URL}/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1"
    data = {
        "formhash": ZODGAME_FORMHASH,
        "qdxq": mood_id
    }
    try:
        response = requests.post(url, headers=ZODGAME_HEADERS, data=data, timeout=TIME_OUT_TIME)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 zodgame_sign_in({mood_id}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return ""
    except requests.RequestException as e:
        log_message(f"请求 zodgame_sign_in({mood_id}) (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 zodgame_sign_in({mood_id}) 失败: {e}", level="error")
        return ""
    return response.text

# ------------------------------
# zodgame 的一些页面请求
# ------------------------------

def zodgame_earn_points_page():
    """
    请求赚积分页面

    BUX 广告点击赚积分

    说明
    1. 每天只能点击广告1次
    2. 看完广告之后才会奖励积分, 中途关闭则今日广告不再显示, 必须等到下一天
    """
    url = f"https://{ZODGAME_BASE_URL}/plugin.php?id=jnbux"
    try:
        response = requests.get(url, headers=ZODGAME_HEADERS, timeout=TIME_OUT_TIME)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 zodgame_earn_points_page 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return ""
    except requests.RequestException as e:
        log_message(f"请求 zodgame_earn_points_page (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 zodgame_earn_points_page 失败: {e}", level="error")
        return ""
    return response.text

def zodgame_sign_in_page():
    """
    请求签到页面
    
    """
    url = f"https://{ZODGAME_BASE_URL}/plugin.php?id=dsu_paulsign:sign"
    try:
        response = requests.get(url, headers=ZODGAME_HEADERS,timeout=TIME_OUT_TIME)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求 zodgame_sign_in_page 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return ""
    except requests.RequestException as e:
        log_message(f"请求 zodgame_sign_in_page (Request Error): {e}", level="error")
        return ""
    except Exception as e:
        log_message(f"请求 zodgame_sign_in_page 失败: {e}", level="error")
        return ""
    return response.text




# ------------------------------
# zodgame 的一些操作
# ------------------------------

def zodgame_process_earn_points():
    response_text = zodgame_earn_points_page()
    # 保存页面内容, 以备分析
    save_string_as_file(response_text, "zodgame_earn_points_page", "zodgame")
    return

def zodgame_process_sign_in():
    # 准备签到
    response_text = zodgame_sign_in_page()
    zodgame_update_formhash(response_text)
    sign_in_info = zodgame_extract_sign_in_info(response_text)

    mood_id = zodgame_pick_random_mood_id()
    response_text = zodgame_sign_in(mood_id)
    if "已被系统拒绝" in response_text:
        log_message('zodgame 的 cookie 已过期')
    elif "恭喜" in response_text:
        log_message("zodgame 签到成功")
    elif '已经签到' in response_text:
        log_message('zodgame 已经签到了')
    else:
        log_message(f'zodgame 签到失败')
        save_string_as_file(response_text, "zodgame_sign_in_fail", "zodgame")

    response_text = zodgame_sign_in_page()
    sign_in_info_new = zodgame_extract_sign_in_info(response_text)

    # 检查是否签到成功
    if sign_in_info_new['total_rewards'] == sign_in_info['total_rewards']:
        log_message("签到失败", level="error")
    else:
        log_message(f"本次签到时间: {sign_in_info_new['last_check_in_time']}\n"
                    f"本次获得的奖励: {sign_in_info['last_reward']}\n"
                    f"距离升级还需签到: {sign_in_info_new['remaining_days']} 天\n"
        )
        json_data_handler.increment_value(sign_in_info_new['last_reward'], CURRENT_MONTH, "zodgame", "酱油")
    return

def zodgame():
    log_message("\n------------------------------------\n")
    log_message("开始执行 zodgame 函数")
    log_message("\n------------------------------------\n")
    
    zodgame_process_earn_points()

    zodgame_process_sign_in()

    
    log_message("\n------------------------------------\n")
    


# ------------------------------
# 入口
# ------------------------------

def zodgame_start():
    """开始执行 zodgame 签到"""
    if not set_cookie():
        return
    
    current_year = datetime.datetime.now().year
    json_path = f"./data/others_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)

    # 签到
    zodgame()

    json_data_handler.write_data()

    return
