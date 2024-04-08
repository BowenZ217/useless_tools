import datetime
import json
import os

import requests

from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

CURRENT_MONTH = str(datetime.datetime.now().month)

galcg_headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Length": "0",
    "Origin": "https://www.galcg.org",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
}

def set_header():
    global galcg_headers
    
    username = os.environ.get("GALCG_USERNAME")
    if not username:
        log_message("请设置环墶变量 GALCG_USERNAME", level="error")
        log_message("\n------------------------------------\n")
        return False
    password = os.environ.get("GALCG_PASSWORD")
    if not password:
        log_message("请设置环墶变量 GALCG_PASSWORD", level="error")
        log_message("\n------------------------------------\n")
        return False

    url = "https://www.galcg.org/wp-json/jwt-auth/v1/token"
    data = {
        "username": username,
        "password": password,
    }
    
    headers = galcg_headers.copy()
    headers["Referer"] = "https://www.galcg.org/"
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

    except requests.exceptions.HTTPError as e:
        log_message(f"登录请求失败: {e}", level="error")
        log_message("\n------------------------------------\n")
        return False
    except requests.RequestException as e:
        log_message(f"登录请求失败: {e}", level="error")
        log_message("\n------------------------------------\n")
        return False
    except Exception as e:
        log_message(f"登录请求失败: {e}", level="error")
        log_message("\n------------------------------------\n")
        return False
    
    # 更新cookies
    cookies = response.cookies.get_dict()
    headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in cookies.items()])

    try:
        response_json = response.json()
        headers["Authorization"] = f"Bearer {response_json['token']}"
        # log_message(f"galcg 登录成功, 用户名: {response_json['name']}, 用户 ID: {response_json['id']}")
    except KeyError:
        log_message(f"galcg 登录失败, 返回结果: {response.text}")
        log_message("\n------------------------------------\n")
        return False
        
    # reset Referer and save headers to global variable
    headers["Referer"] = "https://www.galcg.org/mission/today"

    galcg_headers = headers
    return True

def galcg():
    """签到"""
    log_message("\n------------------------------------\n")
    log_message("开始执行 galcg 函数")
    log_message("\n------------------------------------\n")

    # 请求签到页面相关信息, 否则无法直接请求签到接口
    url = "https://www.galcg.org/wp-json/b2/v1/getUserInfo"
    try:
        response = requests.post(url, headers=galcg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"getUserInfo HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "galcg_fail", "galcg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getUserInfo Request Error: {e}", level="error")
    except Exception as e:
        log_message(f"getUserInfo 解析失败: {e}", level="error")

    url = "https://www.galcg.org/wp-json/b2/v1/getLatestAnnouncement"
    data = b'count=3'
    galcg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=galcg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        del galcg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        log_message(f"getLatestAnnouncement HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "galcg_fail", "galcg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getLatestAnnouncement Request Error: {e}", level="error")
    except Exception as e:
        log_message(f"getLatestAnnouncement 解析失败: {e}", level="error")

    url = "https://www.galcg.org/wp-json/b2/v1/getUserMission"
    data = b'count=10&paged=1'
    galcg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=galcg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        del galcg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        log_message(f"getUserMission HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "galcg_fail", "galcg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getUserMission Request Error: {e}", level="error")
    except Exception as e:
        log_message(f"getUserMission 解析失败: {e}", level="error")
        

    url = "https://www.galcg.org/wp-json/b2/v1/getMissionList"
    data = b'count=20&paged=1&type=today&post_paged=1'
    galcg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=galcg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        del galcg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        log_message(f"getMissionList HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "galcg_fail", "galcg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getMissionList Request Error: {e}", level="error")
    except Exception as e:
        log_message(f"getMissionList 解析失败: {e}", level="error")


    # ----------------------------------------------
    # 请求签到
    # ----------------------------------------------
        
    url = "https://www.galcg.org/wp-json/b2/v1/userMission"
    
    try:
        response = requests.post(url, headers=galcg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        # save_string_as_file(response.text, "galcg_checkin", "galcg", response.encoding)

        response_json = response.json()
        log_message(
            f"签到日期: {response_json['date']}\n"
            f"签到积分: {response_json['credit']}\n"
        )
        json_data_handler.increment_value(response_json['credit'], CURRENT_MONTH, "galcg", "credit_added")
    except json.JSONDecodeError as e:
        log_message(f"解析 JSON 失败: {e}", level="error")
        log_message(f"签到失败, 返回结果: {response.text}", level="error")
        log_message("\n------------------------------------\n")
        return False
    except requests.HTTPError as e:
        log_message(f"签到请求失败 HTTP Error ({response.status_code}): {e}", level="error")
        log_message("\n------------------------------------\n")
        save_string_as_file(str(response.json()), "galcg_fail", "galcg", response.encoding)
        return False
    except requests.RequestException as e:
        log_message(f"签到请求失败 Request Error: {e}", level="error")
        log_message("\n------------------------------------\n")
        return False
    # json 格式不存在签到结果, 因此不再解析
    except Exception as e:
        log_message(f"userMission 解析失败: {e}", level="error")
        log_message(f"签到失败, 可能今天已经签到过了, 返回结果: {response.text}")
        log_message("\n------------------------------------\n")
        return False
    
    log_message("\n------------------------------------\n")
    
    return True


def galcg_start():
    """开始执行 galcg 签到"""
    if not set_header():
        return
    
    current_year = datetime.datetime.now().year
    json_path = f"./data/others_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)

    # 签到
    galcg()

    json_data_handler.write_data()

    return
