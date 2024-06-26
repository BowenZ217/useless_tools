import datetime
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup


from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

CURRENT_MONTH = str(datetime.datetime.now().month)
ZODGAME_BASE_URL = "zodgame.xyz"
ZODGAME_FORMHASH = "417c75e4"

TIME_OUT_TIME = 30  # seconds

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

def zodgame_extract_earn_points_info(html_str: str):
    """
    从赚积分页面提取任务信息
    """
    # Updated dictionary to hold task details
    tasks_dict = {}

    try:
        # 解析 HTML
        soup = BeautifulSoup(html_str, 'html.parser')
        
        # Find all <script> elements that define the opening of new windows using the corrected method
        scripts = soup.find_all("script", string=re.compile(r"function openNewWindow\d+\(\)"))
        for script in scripts:
            function_content = script.string.strip()
            task_id_search = re.search(r"function openNewWindow(\d+)", function_content)
            if task_id_search:
                task_id = task_id_search.group(1)
                url_search = re.search(r"window.open\(\"(.*?)\",", function_content)
                if url_search:
                    ad_url = url_search.group(1)
                    tasks_dict[task_id] = {"ad_url": ad_url}

        # Find all rows in the table that have task details
        task_rows = soup.find_all("tr")
        for row in task_rows:
            cells = row.find_all("td")
            if len(cells) < 6:  # Ensure it's a row with enough columns
                continue

            id_cell = cells[0].text.strip()
            if id_cell.isdigit() and id_cell in tasks_dict:  # Check if it matches a task id
                # Extract additional data from the row
                title = cells[1].text.strip()
                reward = cells[2].text.strip()
                time_seconds_match = re.search(r'(\d+) 秒', cells[3].text.strip())
                if not time_seconds_match:
                    continue
                time_seconds = int(time_seconds_match.group(1))
                status = cells[4].text.strip()
                operation = cells[5].text.strip()
                
                # Regex to find check URL
                check_link_search = re.search(r"showWindow\('check', '(.*?)'\)", cells[5].a['onclick'])
                if not check_link_search:
                    continue  # Skip this task if no check URL is found
                check_url = check_link_search.group(1)
                tasks_dict[id_cell].update({
                    "title": title,
                    "reward": reward,
                    "check_time": time_seconds,
                    "status": status,
                    "operation": operation,
                    "check_url": check_url
                })

    except Exception as e:
        log_message(f"提取赚积分信息时出现错误: {e}", level="error")

    return tasks_dict

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

def zodgame_extract_earn_point_task_page(html_str: str, task: str) -> str:
    """
    从赚积分任务页面提取任务当前状态
    """
    try:
        # 解析 HTML
        soup = BeautifulSoup(html_str, 'html.parser')

        if "click" in task or "update" in task:
            # 提取 <div class="jnbux_hd"> 中的文本
            task_info = soup.find("div", class_="jnbux_hd")
            if task_info:
                return task_info.text
        elif "final" in task:
            task_info = soup.find("div", id="messagetext")
            if task_info:
                task_text = task_info.text
                task_text = re.sub(r"如果您的浏览器没有自动跳转，请点击此链接", "", task_text)
                return task_text.strip()
        else:
            return soup.get_text()
    except Exception as e:
        print(f"提取任务 ({task}) 信息时出现错误: {e}")
    return ""

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

def zodgame_process_earn_points_task(task_id: str, task_info: dict):
    """
    处理赚积分任务

    :param task_id: 任务 ID
    :param task_info: 任务信息

    :return: 处理结果
    """
    # 访问广告页面
    ad_url = task_info.get("ad_url", "")
    if not ad_url:
        log_message(f"任务 ({task_id}) 的广告链接为空", level="error")
        return False
    try:
        url = f"https://{ZODGAME_BASE_URL}/{ad_url}"
        response = requests.get(url, headers=ZODGAME_HEADERS, timeout=TIME_OUT_TIME)
        result = zodgame_extract_earn_point_task_page(response.text, "click")
        log_message(f"任务 ({task_id}) 的广告初始点击页面: {result}")
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求广告页面 ({url}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return False
    except requests.RequestException as e:
        log_message(f"请求广告页面 ({url}) (Request Error): {e}", level="error")
        return False
    except Exception as e:
        log_message(f"请求广告页面 ({url}) 失败: {e}", level="error")
        return False

    # 等待一段时间
    time.sleep(task_info['check_time'] + 2) # 多两秒容错

    # 访问更新页面
    try:
        update_url = url.replace("do=click", "do=update")
        response = requests.get(update_url, headers=ZODGAME_HEADERS, timeout=TIME_OUT_TIME)
        result = zodgame_extract_earn_point_task_page(response.text, "update")
        log_message(f"任务 ({task_id}) 的更广告新页面: {result}")
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求更新页面 ({update_url}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return False
    except requests.RequestException as e:
        log_message(f"请求更新页面 ({update_url}) (Request Error): {e}", level="error")
        return False
    except Exception as e:
        log_message(f"请求更新页面 ({update_url}) 失败: {e}", level="error")
        return False

    # 等待一段时间
    time.sleep(1)

    # 访问检查页面
    check_url = task_info.get("check_url", "")
    if not check_url:
        log_message(f"任务 ({task_id}) 的检查链接为空", level="error")
        return False
    try:
        url = f"https://{ZODGAME_BASE_URL}/{check_url}"
        response = requests.get(url, headers=ZODGAME_HEADERS, timeout=TIME_OUT_TIME)
        result = zodgame_extract_earn_point_task_page(response.text, "final")
        log_message(f"任务 ({task_id}) 的检查页面: {result}")
        if "成功" in result:
            # e.x. task_info['reward'] = "2 点币"
            # 从中提取数字 和 单位
            reward_match = re.match(r"(\d+)(.+)", task_info['reward'])
            if reward_match:
                reward_num = int(reward_match.group(1))
                reward_unit = reward_match.group(2).strip()
                json_data_handler.increment_value(reward_num, CURRENT_MONTH, "zodgame", reward_unit)
                json_data_handler.increment_value(1, CURRENT_MONTH, "zodgame", "任务", task_id)
        response.raise_for_status()
    except requests.HTTPError as e:
        log_message(f"请求检查页面 ({url}) 失败 HTTP Error ({response.status_code}): {e}", level="error")
        return False
    except requests.RequestException as e:
        log_message(f"请求检查页面 ({url}) (Request Error): {e}", level="error")
        return False
    except Exception as e:
        log_message(f"请求检查页面 ({url}) 失败: {e}", level="error")
        return False
    
    return True

def zodgame_process_earn_points():
    response_text = zodgame_earn_points_page()

    tasks_dict = zodgame_extract_earn_points_info(response_text)
    if not tasks_dict:
        log_message("没有找到任务信息")
        return
    
    for task_id, task_info in tasks_dict.items():
        log_message(f"任务 ({task_id}) : {task_info['title']}\n奖励: {task_info['reward']}\n所需时间: {task_info['check_time']} 秒")

        # 处理任务
        zodgame_process_earn_points_task(task_id, task_info)

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
