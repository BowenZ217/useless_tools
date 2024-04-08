import math

def compute_remaining_time(max_value: float, rate_per_minute: float):
    """计算到达最大值的时间

    参数:
    max_value (float): 需要达到的目标最大值。
    rate_per_minute (float): 每分钟增加的数值。

    返回:
    int: 达到最大值所需的总分钟数。如果rate_per_minute为0, 则返回 0。
    """
    if rate_per_minute <= 0:
        return 0
    
    remaining_time = max_value / rate_per_minute
    return math.ceil(remaining_time)

def compute_time_to_next_integer(begin_minutes: int, rate_per_minute: float):
    """计算达到下一个整数值所需的剩余时间

    参数:
    begin_minutes (int): 起始分钟数。
    rate_per_minute (float): 每分钟的增长率。

    返回:
    next_int_minutes (int): 达到下一个整数值所需的剩余时间（分钟数）。
    """
    if rate_per_minute <= 0 or begin_minutes < 0:
        # 如果每分钟增长率为0或负数 或 起始分钟数为负数，则无法达到下一个整数值
        return 0
    
    if begin_minutes == 0:
        return math.ceil(1 / rate_per_minute)
    
    # 计算当前值与下一个整数值之间的差值
    current_value = begin_minutes * rate_per_minute
    next_int_value = math.ceil(current_value)
    difference = next_int_value - current_value

    # 计算达到下一个整数值所需的剩余时间
    return math.ceil(difference / rate_per_minute)


def calculate_total_minutes(minutes: int, hours=0, days=0):
    """计算总时间"""
    return minutes + hours * 60 + days * 24 * 60

def format_remaining_time(total_minutes: int):
    """
    格式化剩余时间为字符串 "{days} 天 {hours} 小时 {minutes} 分钟"
    """
    if total_minutes <= 0:
        return "0 分钟"
    
    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60

    formatted_time = ""  # 初始化空字符串

    if days > 0:
        formatted_time += f"{days} 天 "
    if hours > 0 or days > 0:  # 如果有天数，即使小时数为0也显示
        formatted_time += f"{hours} 小时 "
    formatted_time += f"{minutes} 分钟"  # 分钟数总是显示

    return formatted_time.strip()  # 返回字符串，移除尾部可能的多余空格
