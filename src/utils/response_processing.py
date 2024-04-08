import gzip
import zlib

from io import BytesIO

import brotli

# from .logger import log_message

def decompress_response(response_content: str):
    """
    尝试使用gzip, deflate, 或Brotli解压响应内容。
    返回解压缩的数据或原始数据（如果所有方法都失败）。
    """
    try:
        # 尝试使用gzip解压
        with gzip.GzipFile(fileobj=BytesIO(response_content),
                           mode='rb') as gzip_file:
            return gzip_file.read()
    except:
        try:
            # 尝试使用deflate解压
            return zlib.decompress(response_content, -zlib.MAX_WBITS)
        except:
            try:
                # 尝试使用Brotli解压
                return brotli.decompress(response_content)
            except:
                # log_message("无法解压响应内容")
                pass
                
    return response_content # 如果所有方法都失败, 返回原始数据
