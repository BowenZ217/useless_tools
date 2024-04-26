import json
import os
import time

import requests

from .utils.logger import log_message
from .utils.file_operations import save_string_as_file

JMCOMIC_API_CONFIG_FILE_PATH = "./data/jmcomic_api_config.json"

DOMAIN_API_LIST = None
JMCOMIC_API_BASE_URL = None
APP_TOKEN_SECRET = None
APP_TOKEN_SECRET_2 = None
APP_DATA_SECRET = None
APP_VERSION = None
JMCOMIC_HEADERS = None

JMCOMIC_DAILY_ID = 43 # 默认值
JMCOMIC_USER_ID = None
JMCOMIC_USERNAME = None
JMCOMIC_PASSWORD = None
JMCOMIC_CURRENT_TS = None

TIME_OUT_TIME = 10  # seconds

class JmCryptoTool:
    """
    禁漫加解密相关逻辑

    Reference:  https://github.com/hect0x7/JMComic-Crawler-Python
    path:       src/jmcomic/jm_toolkit.py
    """
    @classmethod
    def token_and_tokenparam(cls,
                             ts,
                             ver=None,
                             secret=None,
                             ):
        """
        计算禁漫接口的请求headers的token和tokenparam

        :param ts: 时间戳
        :param ver: app版本
        :param secret: 密钥
        :return (token, tokenparam)
        """

        if ver is None:
            ver = '1.6.8'

        if secret is None:
            secret = APP_TOKEN_SECRET

        # tokenparam: 1700566805,1.6.3
        tokenparam = '{},{}'.format(ts, ver)

        # token: 81498a20feea7fbb7149c637e49702e3
        token = cls.md5hex(f'{ts}{secret}')

        return token, tokenparam

    @classmethod
    def decode_resp_data(cls,
                         data: str,
                         ts,
                         secret=None,
                         ) -> str:
        """
        解密接口返回值

        :param data: resp.json()['data']
        :param ts: 时间戳
        :param secret: 密钥
        :return: json格式的字符串
        """
        if secret is None:
            secret = APP_DATA_SECRET

        # 1. base64解码
        import base64
        data_b64 = base64.b64decode(data)

        # 2. AES-ECB解密
        key = cls.md5hex(f'{ts}{secret}').encode('utf-8')
        from Crypto.Cipher import AES
        data_aes = AES.new(key, AES.MODE_ECB).decrypt(data_b64)

        # 3. 移除末尾的padding
        data = data_aes[:-data_aes[-1]]

        # 4. 解码为字符串 (json)
        res = data.decode('utf-8')

        return res

    @classmethod
    def md5hex(cls, key: str):
        from hashlib import md5
        return md5(key.encode("utf-8")).hexdigest()

def set_global():
    """设置全局变量"""
    global DOMAIN_API_LIST
    global APP_TOKEN_SECRET
    global APP_TOKEN_SECRET_2
    global APP_DATA_SECRET
    global APP_VERSION
    global JMCOMIC_HEADERS
    global JMCOMIC_USERNAME
    global JMCOMIC_PASSWORD
    global JMCOMIC_CURRENT_TS

    try:
        with open(JMCOMIC_API_CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        DOMAIN_API_LIST = config["DOMAIN_API_LIST"]
        APP_TOKEN_SECRET = config["APP_TOKEN_SECRET"]
        APP_TOKEN_SECRET_2 = config["APP_TOKEN_SECRET_2"]
        APP_DATA_SECRET = config["APP_DATA_SECRET"]
        APP_VERSION = config["APP_VERSION"]
        JMCOMIC_HEADERS = config["APP_HEADERS"]
    except Exception as e:
        log_message(f"读取 JMComic API 配置文件失败: {e}", level="error")
        return False
    
    try:
        JMCOMIC_USERNAME = os.environ.get("JMCOMIC_USERNAME")
        if not JMCOMIC_USERNAME:
            log_message("请设置环墶变量 JMCOMIC_USERNAME", level="error")
            return False
        JMCOMIC_PASSWORD = os.environ.get("JMCOMIC_PASSWORD")
        if not JMCOMIC_PASSWORD:
            log_message("请设置环境变量 JMCOMIC_PASSWORD", level="error")
            return False
    except Exception as e:
        log_message(f"读取 JMComic 用户信息失败: {e}", level="error")
        return False

    try:
        JMCOMIC_CURRENT_TS = int(time.time())
        token, tokenparam = JmCryptoTool.token_and_tokenparam(JMCOMIC_CURRENT_TS, APP_VERSION)
        JMCOMIC_HEADERS["token"] = token
        JMCOMIC_HEADERS["tokenparam"] = tokenparam
    except Exception as e:
        log_message(f"计算 token 和 tokenparam 失败: {e}", level="error")
        return False
    return True

def save_global():
    """保存全局变量"""
    try:
        config = None
        with open(JMCOMIC_API_CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["DOMAIN_API_LIST"] = DOMAIN_API_LIST
        config["APP_TOKEN_SECRET"] = APP_TOKEN_SECRET
        config["APP_TOKEN_SECRET_2"] = APP_TOKEN_SECRET_2
        config["APP_DATA_SECRET"] = APP_DATA_SECRET
        config["APP_VERSION"] = APP_VERSION
        
        with open(JMCOMIC_API_CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_message(f"保存 JMComic API 配置文件失败: {e}", level="error")
        return False
    return True


def set_cookie():
    """设置 Cookie"""
    global APP_VERSION
    global JMCOMIC_HEADERS
    global JMCOMIC_API_BASE_URL
    for domain in DOMAIN_API_LIST:
        url = f"https://{domain}/setting"
        JMCOMIC_HEADERS["Host"] = domain
        try:
            response = requests.post(url, headers=JMCOMIC_HEADERS, timeout=TIME_OUT_TIME)
            response.raise_for_status()
            cookies = response.cookies.get_dict()
            if cookies:
                JMCOMIC_HEADERS["Cookie"] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
                JMCOMIC_API_BASE_URL = f"https://{domain}"
            else:
                log_message(f"使用 {domain} 设置 Cookie 失败: 未获取到 Cookie", level="error")
                continue
            try:
                # app 格式: "1.6.8", 如果不对或为空，则跳过，如果大于当前版本，则更新
                resp_data = response.json()["data"]
                decoded_resp_data = JmCryptoTool.decode_resp_data(resp_data, JMCOMIC_CURRENT_TS)
                # decoded_resp_data: str -> dict
                data = json.loads(decoded_resp_data)
                version = data.get("version", None)
                if version and version > APP_VERSION:
                    log_message(f"检测到 {domain} 的 App 版本为 {version}，更新 {APP_VERSION} 为最新版本", level="info")
                    APP_VERSION = version
                    token, tokenparam = JmCryptoTool.token_and_tokenparam(JMCOMIC_CURRENT_TS, APP_VERSION)
                    JMCOMIC_HEADERS["token"] = token
                    JMCOMIC_HEADERS["tokenparam"] = tokenparam
            except Exception as e:
                log_message(f"解析 {domain} 的 App 版本失败: {e}", level="error")
                save_string_as_file(response.text, prefix="jmcomic_setting_error", folder="jmcomic")
            return True
        except Exception as e:
            log_message(f"使用 {domain} 设置 Cookie 失败: {e}", level="error")
            continue
    return False

def jmcomic_login():
    """JMComic 登录"""
    global JMCOMIC_USER_ID
    local_headers = JMCOMIC_HEADERS.copy()

    try:
        url = f"{JMCOMIC_API_BASE_URL}/login"
        data = f"username={JMCOMIC_USERNAME}&password={JMCOMIC_PASSWORD}&"
        local_headers["Content-Type"] = "application/x-www-form-urlencoded"
        local_headers["Content-Length"] = str(len(data))
        response = requests.post(url, headers=local_headers, data=data, timeout=TIME_OUT_TIME)
        response.raise_for_status()
        resp_data = response.json()["data"]
        decoded_resp_data = JmCryptoTool.decode_resp_data(resp_data, JMCOMIC_CURRENT_TS)
        data = json.loads(decoded_resp_data)
        JMCOMIC_USER_ID = data.get("uid", None)
        if not JMCOMIC_USER_ID:
            log_message(f"登录失败: 未获取到用户 ID", level="error")
            save_string_as_file(response.text, prefix="jmcomic_login_uid_error", folder="jmcomic")
            return False
        log_message(f"登录成功: lv. {data['level']} ({data['exp']} / {data['nextLevelExp']})", level="info")
        # log_message(f"登录信息: {data['message']}")
    except Exception as e:
        log_message(f"登录失败: {e}", level="error")
    return True

def jmcomic_get_daily_id():
    """获取 JMComic 签到的 `daily_id`"""
    global JMCOMIC_DAILY_ID
    try:
        url = f"{JMCOMIC_API_BASE_URL}/daily?user_id={JMCOMIC_USER_ID}"
        response = requests.get(url, headers=JMCOMIC_HEADERS, timeout=TIME_OUT_TIME)
        response.raise_for_status()
        resp_data = response.json()["data"]
        decoded_resp_data = JmCryptoTool.decode_resp_data(resp_data, JMCOMIC_CURRENT_TS)
        data = json.loads(decoded_resp_data)
        JMCOMIC_DAILY_ID = data.get("daily_id", 43)
    except Exception as e:
        log_message(f"获取 daily_id 失败: {e}", level="error")
    return

def jmcomic_check_in():
    """JMComic 签到"""
    local_headers = JMCOMIC_HEADERS.copy()
    # 签到
    try:
        url = f"{JMCOMIC_API_BASE_URL}/daily_chk"
        data = f"user_id={JMCOMIC_USER_ID}&daily_id={JMCOMIC_DAILY_ID}&"
        local_headers["Content-Type"] = "application/x-www-form-urlencoded"
        local_headers["Content-Length"] = str(len(data))
        response = requests.post(url, headers=local_headers, data=data, timeout=TIME_OUT_TIME)
        response.raise_for_status()
        resp_data = response.json()["data"]
        decoded_resp_data = JmCryptoTool.decode_resp_data(resp_data, JMCOMIC_CURRENT_TS)
        data = json.loads(decoded_resp_data)
        log_message(f"签到结果: {data['msg']}", level="info")
    except Exception as e:
        log_message(f"签到失败: {e}", level="error")

    return

def jmcomic_start():
    """开始执行 JMComic 签到"""
    if not set_global():
        return
    if not set_cookie():
        return
    if not jmcomic_login():
        return
    jmcomic_get_daily_id()

    jmcomic_check_in()

    save_global()
    return
