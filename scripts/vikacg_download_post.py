"""
保存 Vikacg 的文章到本地 Markdown 文件

需要设置环境变量:
- VIKACG_USERNAME: Vikacg 用户名
- VIKACG_PASSWORD: Vikacg 密码

相关库:
- html2text
- requests
"""

import json
import math
import os
import re
import time

from bs4 import BeautifulSoup
import html2text
import requests

VIKACG_BASE_URLS = [
    "www.vikacg.com",
]
VIKACG_BASE_URL = "www.vikacg.com"

VIKACG_AUTHOR_ID = 1
VIKACG_AUTHOR_POST_MAX_PAGE = 1

SAVING_PATH = "vikacg_posts"

VIKACG_SAVEING_ID = """
188226
191942
195786
"""

vikacg_headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": f"https://{VIKACG_BASE_URL}",
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
    global VIKACG_AUTHOR_ID
    
    username = os.environ.get("VIKACG_USERNAME")
    if not username:
        print("请设置环墶变量 VIKACG_USERNAME")
        return False
    password = os.environ.get("VIKACG_PASSWORD")
    if not password:
        print("请设置环墶变量 VIKACG_PASSWORD")
        return False

    url = f"https://{VIKACG_BASE_URL}/wp-json/jwt-auth/v1/token"
    data = {
        "username": username,
        "password": password,
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/login"

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
        print("\n------------------------------------\n")
        return False
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"getStreamList Request Error: {e}")
        print(f"vikacg Request Error")
        print("\n------------------------------------\n")
        return False
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")

    # 更新cookies
    cookies = response.cookies.get_dict()
    headers['Cookie'] = '; '.join([f"{key}={value}" for key, value in cookies.items()])
    
    try:
        response_json = response.json()
        print(f"vikacg 登录成功, 用户名: {response_json['name']}, 用户 ID: {response_json['id']}")
        VIKACG_AUTHOR_ID = response_json["id"]
        headers["Authorization"] = f"Bearer {response_json['token']}"
    except KeyError:
        print(f"vikacg 登录失败, 返回结果: {response.text}")
        print("\n------------------------------------\n")
        return False
        
    # reset Referer and save headers to global variable
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/wallet/mission"

    vikacg_headers = headers

    return True

# ------------------------------
# Utils
# ------------------------------
"""
html2text usage:
- UNICODE_SNOB for using unicode
- ESCAPE_SNOB for escaping every special character
- LINKS_EACH_PARAGRAPH for putting links after every paragraph
- BODY_WIDTH for wrapping long lines
- SKIP_INTERNAL_LINKS to skip #local-anchor things
- INLINE_LINKS for formatting images and links
- PROTECT_LINKS protect from line breaks
- GOOGLE_LIST_INDENT no of pixels to indent nested lists
- IGNORE_ANCHORS
- IGNORE_IMAGES
- IMAGES_AS_HTML always generate HTML tags for images; preserves `height`, `width`, `alt` if possible.
- IMAGES_TO_ALT
- IMAGES_WITH_SIZE
- IGNORE_EMPHASIS
- BYPASS_TABLES format tables in HTML rather than Markdown
- IGNORE_TABLES ignore table-related tags (table, th, td, tr) while keeping rows
- SINGLE_LINE_BREAK to use a single line break rather than two
- UNIFIABLE is a dictionary which maps unicode abbreviations to ASCII values
- RE_SPACE for finding space-only lines
- RE_ORDERED_LIST_MATCHER for matching ordered lists in MD
- RE_UNORDERED_LIST_MATCHER for matching unordered list matcher in MD
- RE_MD_CHARS_MATCHER for matching Md \,[,],( and )
- RE_MD_CHARS_MATCHER_ALL for matching `,*,_,{,},[,],(,),#,!
- RE_MD_DOT_MATCHER for matching lines starting with <space>1.<space>
- RE_MD_PLUS_MATCHER for matching lines starting with <space>+<space>
- RE_MD_DASH_MATCHER for matching lines starting with <space>(-)<space>
- RE_SLASH_CHARS a string of slash escapeable characters
- RE_MD_BACKSLASH_MATCHER to match \char
- USE_AUTOMATIC_LINKS to convert <a href='http://xyz'>http://xyz</a> to <http://xyz>
- MARK_CODE to wrap 'pre' blocks with [code]...[/code] tags
- WRAP_LINKS to decide if links have to be wrapped during text wrapping (implies INLINE_LINKS = False)
- WRAP_LIST_ITEMS to decide if list items have to be wrapped during text wrapping
- WRAP_TABLES to decide if tables have to be wrapped during text wrapping
- DECODE_ERRORS to handle decoding errors. 'strict', 'ignore', 'replace' are the acceptable values.
- DEFAULT_IMAGE_ALT takes a string as value and is used whenever an image tag is missing an `alt` value. 
                    The default for this is an empty string '' to avoid backward breakage
- OPEN_QUOTE is the character used to open a quote when replacing the `<q>` tag. It defaults to `"`.
- CLOSE_QUOTE is the character used to close a quote when replacing the `<q>` tag. It defaults to `"`.
"""
def html_to_markdown(html):
    # 创建 html2text 处理器的实例
    h = html2text.HTML2Text()
    # 忽略表格外围的外框线
    h.body_width = 0
    # 将图片转换为Markdown的图片语法
    h.ignore_images = False
    # 识别和转换表格
    h.ignore_tables = False
    # 忽略链接
    h.ignore_links = False
    # 不产生内联样式
    h.single_line_break = False
    
    # 转换HTML到Markdown
    markdown = h.handle(html)
    
    return markdown

# ------------------------------
# Vikacg API
# ------------------------------

def vikacg_get_stream_list(page=1, post_type="post"):
    """
    返回 Vikacg 作者的文章列表 ("data")
    """
    global VIKACG_AUTHOR_POST_MAX_PAGE
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/getStreamList"
    data = {
        "author": VIKACG_AUTHOR_ID,
        "paged": page,
        "pages": True,
        "post_types": [post_type],
        "post_status": ["publish", "draft", "pending", "private", "future"],
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/creator/list/post"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        VIKACG_AUTHOR_POST_MAX_PAGE = response.json().get("pages", 1)
        print(f"vikacg 总页数: {VIKACG_AUTHOR_POST_MAX_PAGE}")
        return response.json().get("data", [])
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
        print("\n------------------------------------\n")
        return False
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"getStreamList Request Error: {e}")
        print(f"vikacg Request Error")
        print("\n------------------------------------\n")
        return False
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return {}

def vikacg_user_get_write_post_info(post_id):
    """
    返回 Vikacg 文章的详细信息
    """
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/getWritePostInfo"
    data = {
        "post_id": post_id,
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/creator/write/post?id={post_id}"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.json()
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
        print("\n------------------------------------\n")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"getStreamList Request Error: {e}")
        print(f"vikacg Request Error")
        print("\n------------------------------------\n")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return {}

def vikacg_user_get_write_content(post_id):
    """
    返回 Vikacg 文章的内容
    """
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/getWriteCountent"
    data = {
        "post_id": post_id,
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/creator/write/post?id={post_id}"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.json()
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
        print("\n------------------------------------\n")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"getStreamList Request Error: {e}")
        print(f"vikacg Request Error")
        print("\n------------------------------------\n")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return {}

def vikacg_delete_user_draft_post(post_id):
    """
    删除 Vikacg 草稿文章
    
    :param post_id: 文章 ID

    :return: Boolean
    """
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/deleteDraftPost"
    data = {
        "post_id": post_id,
    }
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/creator/list/post"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.json()
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg getStreamList Request Error: {e}")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return False

def vikacg_get_post_html(post_id):
    """
    获取 Vikacg 文章的 HTML 内容
    """
    url = f"https://{VIKACG_BASE_URL}/p/{post_id}.html"
    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/post"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.text
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg vikacg_get_post_html Request Error: {e}")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return ""

def vikacg_delete_user_circle(topic_id):
    """
    删除 Vikacg 作者的圈子文章

    :param topic_id: 文章 ID
    """
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/deleteTopic"
    data = {
        "topic_id": topic_id,
    }

    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/c/{topic_id}.html"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.json()
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg HTTP 请求失败 ({response.status_code}): {e}")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg Request Error: {e}")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg Error: {e}")
    return False

def vikacg_delete_comment(id):
    """
    """
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/deleteComment"
    data = {
        "comment_id": id,
    }

    headers = vikacg_headers.copy()
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/post"
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(data)))

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        return response.json()
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg_delete_comment HTTP 请求失败 ({response.status_code}): {e}")
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg_delete_comment Request Error: {e}")
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg_delete_comment Error: {e}")

def vikacg_extract_comments(comment_list, user_id, user_comments):
    """
    递归地从评论列表中提取用户的评论ID。
    """
    for comment in comment_list:
        # 检查当前评论的作者是否为目标用户
        if str(comment["comment_author"]["id"]) == user_id:
            user_comments.append(comment["comment_ID"])
        # 如果存在子评论，递归地处理它们
        if "child_comments" in comment and "list" in comment["child_comments"]:
            vikacg_extract_comments(comment["child_comments"]["list"], user_id, user_comments)

def vikacg_get_user_topic_comment_list(topic_id, user_id):
    url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/getTopicCommentList"
    initial_data = {
        "topicId": topic_id,
        "paged": 1,
        "orderBy": "ASC"
    }
    
    headers = vikacg_headers.copy()
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(initial_data)))

    try:
        response = requests.post(url, headers=headers, json=initial_data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        pages = response.json().get("pages", 1)
        pages = int(pages)
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg_get_user_topic_comment_list HTTP 请求失败 ({response.status_code}): {e}")
        return []
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg_get_user_topic_comment_list Request Error: {e}")
        return []
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg_get_user_topic_comment_list Error: {e}")
        return []
    
    time.sleep(1)
    
    user_comments = []
    print(f"文章 {topic_id} 中的评论总页数: {pages}")

    for i in range(1, pages + 1):
        data = {
            "topicId": topic_id,
            "paged": i,
            "orderBy": "ASC"
        }
        headers["Content-Length"] = str(len(json.dumps(data)))

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
            comment_list = response.json().get("list", [])
            # for comment in comment_list:
            #     if str(comment["comment_author"]["id"]) == user_id:
            #         user_comments.append(comment["comment_ID"])
            vikacg_extract_comments(comment_list, user_id, user_comments)
        except requests.HTTPError as e:
            # Handle HTTP errors
            print(f"vikacg_get_user_topic_comment_list 2 HTTP 请求失败 ({response.status_code}): {e}")
            return []
        except requests.RequestException as e:
            # 处理HTTP错误
            print(f"vikacg_get_user_topic_comment_list 2 Request Error: {e}")
            return []
        except Exception as e:
            # Handle other errors, such as connection errors.
            print(f"vikacg_get_user_topic_comment_list 2 Error: {e}")
            return []
        time.sleep(1)
    print(f"用户 {user_id} 在文章 {topic_id} 中的评论: {user_comments}")
    return user_comments


def vikacg_get_author_comments_id(user_id):
    base_url = f"https://{VIKACG_BASE_URL}/wp-json/b2/v1/getAuthorComments"
    initial_data = {
        "user_id": user_id,
        "paged": 1,
        "number": 15,
        "post_paged": 1
    }
    
    headers = vikacg_headers.copy()
    headers["Content-Type"] = "application/json"
    headers["Content-Length"] = str(len(json.dumps(initial_data)))
    headers["Referer"] = f"https://{VIKACG_BASE_URL}/u/{user_id}/comments"

    try:
        response = requests.post(base_url, headers=headers, json=initial_data)
        response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
        total_comments = response.json().get("count", 0)
        max_paged = math.ceil(int(total_comments) / 15)
    except requests.HTTPError as e:
        # Handle HTTP errors
        print(f"vikacg_get_author_comments_id 1 HTTP 请求失败 ({response.status_code}): {e}")
        return []
    except requests.RequestException as e:
        # 处理HTTP错误
        print(f"vikacg_get_author_comments_id 1 Request Error: {e}")
        return []
    except Exception as e:
        # Handle other errors, such as connection errors.
        print(f"vikacg_get_author_comments_id 1 Error: {e}")
        return []
    
    time.sleep(1)
    
    id_set = set()
    for i in range(1, max_paged + 1):
        data = {
            "user_id": user_id,
            "paged": i,
            "number": 15,
            "post_paged": i
        }
        headers["Content-Length"] = str(len(json.dumps(data)))

        try:
            response = requests.post(base_url, headers=headers, json=data)
            response.raise_for_status()  # This will raise an HTTPError for bad requests (4XX or 5XX)
            html_content = response.json().get("data", "")

            # Extracting IDs from HTML content
            id_pattern = r"https://www.vikacg.com/[cp]/(\d+).html"
            id_set.update(re.findall(id_pattern, html_content))

        except requests.HTTPError as e:
            # Handle HTTP errors
            print(f"vikacg_get_author_comments_id 2 HTTP 请求失败 ({response.status_code}): {e}")
            return []
        except requests.RequestException as e:
            # 处理HTTP错误
            print(f"vikacg_get_author_comments_id 2 Request Error: {e}")
            return []
        except Exception as e:
            # Handle other errors, such as connection errors.
            print(f"vikacg_get_author_comments_id 2 Error: {e}")
            return []
        time.sleep(1)

    print(f"用户 {user_id} 的评论文章 ID: {id_set}")

    # Process each ID, extract and accumulate user comments
    all_user_comments = []

    for post_id in id_set:
        user_comments = vikacg_get_user_topic_comment_list(post_id, user_id)
        all_user_comments.extend(user_comments)
        time.sleep(1)

    # Removing duplicate comments and return
    return list(set(all_user_comments))


# ------------------------------
# Vikacg 相关操作
# ------------------------------

def vikacg_extract_body_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 定位到 class 为 entry-content 的 div
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        return str(content_div)
    return ""

def vikacg_extract_header_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.find('header', class_='entry-header')
    info = {}

    # 提取标题
    h1 = header.find('h1')
    if h1:
        info['title'] = h1.text.strip()

    # 提取作者及简介
    author_info = header.find('div', class_='post-user-name')
    if author_info:
        author_name = author_info.find('b')
        author_description = author_info.find('span', class_='user-title')
        if author_name and author_description:
            info['author'] = f"{author_name.text.strip()} ({author_description.text.strip()})"

    # 提取日期
    time_tag = header.find('time', class_='b2timeago')
    if time_tag:
        info['date'] = time_tag['datetime'].strip()

    # 提取标签
    tags = header.find_all('a', class_='post-list-cat-item')
    if tags:
        info['tags'] = [tag.text.strip() for tag in tags]

    # 提取封面图片
    top_div = soup.find('div', class_='post-style-4-top')
    if top_div:
        img_tag = top_div.find('img')
        if img_tag:
            info['cover'] = img_tag['src']

    return info

def vikacg_save_user_post(post_id, terms=None, desc=None, cover_image=None):
    """
    保存 Vikacg 文章到本地 Markdown 文件
    """
    post_info = vikacg_user_get_write_post_info(post_id)
    post_content = vikacg_user_get_write_content(post_id)
    post_content_md = html_to_markdown(post_content)

    # 处理文章信息
    post_title = post_info.get("edit_title", "")
    post_tags = post_info.get("edit_tags", [])

    # 保存到文件
    if not os.path.exists(SAVING_PATH):
        os.makedirs(SAVING_PATH)
    file_name = f"{post_id}.md"
    file_path = os.path.join(SAVING_PATH, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {post_title}\n\n")
        f.write(f"---\n\n")

        if cover_image:
            f.write(f"**Cover Image**:\n\n![Cover]({cover_image})\n\n")
        if desc:
            f.write(f"**Description**:\n\n{desc}\n\n")
        if terms:
            f.write(f"**Terms**:\n\n{', '.join([f'`{term}`' for term in terms])}\n\n")

        f.write(f"**Tags**:\n\n{', '.join([f'`{tag}`' for tag in post_tags])}\n\n")

        f.write(f"---\n\n")
        f.write(post_content_md)


def vikacg_save_all_user_post():
    """
    保存 Vikacg 作者的所有文章到本地 Markdown 文件
    """
    # 先获取第一页的文章列表, 刷新总页数
    res = vikacg_get_stream_list()

    for i in range(1, VIKACG_AUTHOR_POST_MAX_PAGE + 1):
        print(f"正在保存第 {i} 页的文章")
        res = vikacg_get_stream_list(i)
        for post in res:
            post_id = post.get("id")
            print(f"正在保存文章 {post_id}")
            desc = post.get("desc", "")
            cover_image = post.get("thumb", "")
            terms = post.get("data", {}).get("terms", {}).get("terms", [])
            terms = [term["name"] for term in terms]
            vikacg_save_user_post(post_id, terms=terms, desc=desc, cover_image=cover_image)
        print("\n\n------------------------------------\n\n")


def vikacg_delete_all_user_draft_post():
    """
    删除 Vikacg 作者的所有草稿文章
    """
    res = vikacg_get_stream_list()
    ids = []

    for i in range(1, VIKACG_AUTHOR_POST_MAX_PAGE + 1):
        print(f"正在获取第 {i} 页的文章")
        res = vikacg_get_stream_list(i)
        for post in res:
            post_id = post.get("id")
            ids.append(post_id)
    print("\n\n------------------------------------\n\n")
    
    for post_id in ids:
        print(f"正在删除文章 {post_id}")
        res = vikacg_delete_user_draft_post(post_id)
        print(f"结果: {res}\n")
        print()
        time.sleep(1)
    print("\n\n------------------------------------\n\n")

def vikacg_save_post(post_id):
    """
    保存 Vikacg 文章到本地 Markdown 文件
    """
    html = vikacg_get_post_html(post_id)
    if not html:
        print(f"获取文章 {post_id} 失败")
        return
    
    # 从 HTML 中提取特定 div 内容
    content_html = vikacg_extract_body_from_html(html)
    markdown = html_to_markdown(content_html)

    content_info = vikacg_extract_header_info(html)
    markdown_header = f"# {content_info['title']}\n\n"
    if 'cover' in content_info:
        markdown_header += f"![Cover]({content_info['cover']})\n\n"
    if 'author' in content_info:
        markdown_header += f"**作者**: {content_info['author']}\n\n"
    if 'date' in content_info:
        markdown_header += f"**日期**: {content_info['date']}\n\n"
    if 'tags' in content_info:
        markdown_header += f"**Tags**: {', '.join([f'`{tag}`' for tag in content_info['tags']])}\n\n"
        
    markdown_header += "---\n\n"

    markdown = markdown_header + markdown

    # 保存到文件
    if not os.path.exists(SAVING_PATH):
        os.makedirs(SAVING_PATH)
    file_name = f"{post_id}.md"
    file_path = os.path.join(SAVING_PATH, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return


def vikacg_save_all_post():
    """
    保存 `VIKACG_SAVEING_ID` 中的文章到本地 Markdown 文件
    VIKACG_SAVEING_ID 为字符串, 以换行分隔的文章 ID
    """
    post_ids = VIKACG_SAVEING_ID.strip().split("\n")
    for post_id in post_ids:
        print(f"正在保存文章 {post_id.strip()}")
        vikacg_save_post(post_id)
    return

def vikacg_delete_all_user_circle():
    """
    删除 Vikacg 作者的所有圈子文章
    """
    res = vikacg_get_stream_list(1, "circle")
    ids = []

    for i in range(1, VIKACG_AUTHOR_POST_MAX_PAGE + 1):
        print(f"正在获取第 {i} 页的文章")
        res = vikacg_get_stream_list(i, "circle")
        for post in res:
            post_id = post.get("id")
            ids.append(post_id)

    print("\n\n------------------------------------\n\n")

    for post_id in ids:
        print(f"正在删除文章 {post_id}")
        res = vikacg_delete_user_circle(post_id)
        print(f"结果: {res}\n")
        print()
        time.sleep(1)
    print("\n\n------------------------------------\n\n")

def vikacg_delete_all_user_comment():
    """
    删除 Vikacg 作者的所有评论
    """
    user_id = VIKACG_AUTHOR_ID
    user_comments = vikacg_get_author_comments_id(user_id)

    for comment_id in user_comments:
        print(f"正在删除评论 {comment_id}")
        res = vikacg_delete_comment(comment_id)
        print(f"结果: {res}\n")
        print()
        time.sleep(2)
    print("\n\n------------------------------------\n\n")


# ------------------------------
# Main
# ------------------------------
def main():
    if not set_header():
        return

    # vikacg_save_all_post()
    # vikacg_save_all_user_post()
    # vikacg_delete_all_user_draft_post()
    # vikacg_delete_all_user_circle()
    vikacg_delete_all_user_comment()

    # comment_id = "210968"
    # res = vikacg_delete_comment(comment_id)
    # print(f"删除评论 {comment_id} 结果: {res}")

if __name__ == "__main__":
    main()
