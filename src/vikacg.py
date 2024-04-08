import datetime
import json
import os

import requests

from .utils import json_data_handler
from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

CURRENT_MONTH = str(datetime.datetime.now().month)

vikacg_headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.vikacg.com",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}

def set_header():
    global vikacg_headers
    
    username = os.environ.get("VIKACG_USERNAME")
    if not username:
        log_message("请设置环墶变量 VIKACG_USERNAME", level="error")
        return False
    password = os.environ.get("VIKACG_PASSWORD")
    if not password:
        log_message("请设置环墶变量 VIKACG_PASSWORD", level="error")
        return False

    url = "https://www.vikacg.com/wp-json/jwt-auth/v1/token"
    data = {
        "username": username,
        "password": password,
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = "https://www.vikacg.com/login"

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        # Handle HTTP errors
        log_message(f"vikacg HTTP 请求失败 ({response.status_code}): {e}", level="error")
        log_message("\n------------------------------------\n")
        return False
    except requests.RequestException as e:
        # 处理HTTP错误
        log_message(f"getStreamList Request Error: {e}", level="error")
        log_message(f"vikacg Request Error", level="error")
        log_message("\n------------------------------------\n")
        return False
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"vikacg Error: {e}", level="error")

    # 更新cookies
    cookies = response.cookies.get_dict()
    headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
    
    try:
        response_json = response.json()
        # log_message(f"vikacg 登录成功, 用户名: {response_json['name']}, 用户 ID: {response_json['id']}")
        headers["Authorization"] = f"Bearer {response_json['token']}"
    except KeyError:
        log_message(f"vikacg 登录失败, 返回结果: {response.text}")
        log_message("\n------------------------------------\n")
        return False
        
    # reset Referer and save headers to global variable
    headers["Referer"] = "https://www.vikacg.com/wallet/mission"

    vikacg_headers = headers

    return True

def vikacg():
    """签到"""
    log_message("\n------------------------------------\n")
    log_message("开始执行 vikacg 函数")
    log_message("\n------------------------------------\n")

    
    # 请求签到页面相关信息, 否则无法直接请求签到接口
    url = "https://www.vikacg.com/networkTest.json"
    try:
        response = requests.get(url, headers=vikacg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        log_message(f"vikacg 网络测试: {response.text}")
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"网络测试 HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        log_message(f"网络测试 Request Error: {e}", "error")
    except Exception as e:
        log_message(f"网络测试失败: {e}", "error")
    
    url = "https://www.vikacg.com/wp-json/b2/v1/app/collectionIndex"
    data = b'count=20&paged=1'
    vikacg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=vikacg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        del vikacg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"collectionIndex HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        log_message(f"collectionIndex Request Error: {e}", level="error")
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"collectionIndex Error: {e}", level="error")
    
    url = "https://www.vikacg.com/wp-json/b2/v1/getLatestAnnouncement"
    data = b'count=5'
    vikacg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=vikacg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        del vikacg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"getLatestAnnouncement HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getLatestAnnouncement Request Error: {e}", level="error")
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"getLatestAnnouncement Error: {e}", level="error")
    
    url = "https://www.vikacg.com/wp-json/vikacg/v1/getIndex"
    vikacg_headers["Content-Length"] = "0"
    try:
        response = requests.post(url, headers=vikacg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        del vikacg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"getIndex HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getIndex Request Error: {e}", level="error")
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"getIndex Error: {e}", level="error")
    

    url = "https://www.vikacg.com/wp-json/b2/v1/getUserInfo"
    vikacg_headers["Content-Length"] = "0"
    user_id = "1"
    try:
        response = requests.post(url, headers=vikacg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        
        response_json = response.json()
        user_id = response_json["user_data"]["id"]

        del vikacg_headers["Content-Length"]
    except requests.HTTPError as e:
        # 处理HTTP错误
        log_message(f"getUserInfo HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        log_message(f"getUserInfo Request Error: {e}", level="error")
    except KeyError:
        pass
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"getUserInfo Error: {e}", level="error")

    url = "https://www.vikacg.com/wp-json/b2/v1/getStreamList"
    payload = {
        "author": user_id,
        "paged": 1,
        "pages": True,
        "post_types": ["publish"],
        "post_status": ["post", "document", "newsflashes", "circle"]
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=vikacg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        # Handle HTTP errors
        log_message(f"getStreamList HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        # 处理HTTP错误
        log_message(f"getStreamList Request Error: {e}", level="error")
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"getStreamList Error: {e}", level="error")


    # ----------------------------------------------
    # 可能只需要请求这个接口即可
    # ----------------------------------------------
        
    url = "https://www.vikacg.com/wp-json/b2/v1/getUserMission"
    data = b'count=20&paged=1'
    vikacg_headers["Content-Length"] = str(len(data))
    try:
        response = requests.post(url, headers=vikacg_headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)

        del vikacg_headers["Content-Length"]
    except KeyError:
        pass
    except requests.HTTPError as e:
        # Handle HTTP errors
        log_message(f"getUserMission HTTP Error ({response.status_code}): {e}", level="error")
        save_string_as_file(str(response.json()), "vikacg_fail", "vikacg", response.encoding)
    except requests.RequestException as e:
        # 处理HTTP错误
        log_message(f"getUserMission Request Error: {e}", level="error")
    except Exception as e:
        # Handle other errors, such as connection errors.
        log_message(f"getUserMission Error: {e}", level="error")

    # ----------------------------------------------
    # 请求签到
    # ----------------------------------------------
        
    url = "https://www.vikacg.com/wp-json/b2/v1/userMission"
    try:
        response = requests.post(url, headers=vikacg_headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        
        response_json = response.json()
        log_message(
            f"签到日期: {response_json['date']}\n"
            f"签到积分: {response_json['credit']}\n"
        )
        json_data_handler.increment_value(response_json['credit'], CURRENT_MONTH, "vikacg", "credit_added")
    except json.JSONDecodeError as e:
        log_message(f"解析 JSON 失败: {e}", level="error")
        log_message(f"签到失败, 返回结果: {response.text}", level="error")
        log_message("\n------------------------------------\n")
        return False
    except requests.HTTPError as e:
        # Handle HTTP errors
        log_message(f"userMission HTTP Error ({response.status_code}): {e}", level="error")
        log_message("\n------------------------------------\n")
        save_string_as_file(response.text, "vikacg_fail", "vikacg", response.encoding)
        return False
    except requests.RequestException as e:
        # 处理HTTP错误
        log_message(f"userMission Request Error: {e}", level="error")
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

def vikacg_start():
    """开始执行 vikacg 签到"""
    if not set_header():
        return
    
    current_year = datetime.datetime.now().year
    json_path = f"./data/others_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)
    
    # 签到
    vikacg()

    json_data_handler.write_data()

    return
