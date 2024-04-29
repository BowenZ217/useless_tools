import os
import pickle
import re

from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

# 设置 Matplotlib 的字体
plt.rcParams['font.family'] = 'SimHei'  # 设置字体为 SimHei
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# --------------------------------------
# Global variables
# --------------------------------------

RANK_MATCH = {'C': 0, 'CC': 1, 'CCC': 2, 'B': 3, 'BB': 4, 'BBB': 5, 'A': 6, 'AA': 7, 'AAA': 8, 'S': 9, 'SS': 10, 'SSS': 11}

# 字典来维护每个装备名称对应的属性名称列表
ATTR_ORDER_DICT = {}

# --------------------------------------
# File I/O
# --------------------------------------

def unpickle(file):
    """
    Unpickle file
    :param file: file path

    :return: dict
    """
    if not os.path.exists(file):
        return {}
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

def load_and_merge_equity_data(data_folder_path, start_year, start_month, end_year, end_month):
    """
    Load and merge equity data from specified period into a single DataFrame.

    :param start_year: int, start year
    :param start_month: int, start month
    :param end_year: int, end year
    :param end_month: int, end month

    :return: DataFrame
    """
    all_equity_data = []
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            # 构建文件名
            filename = f"momozhen_{year}_{month}.pkl"
            file_path = os.path.join(data_folder_path, filename)
            data = unpickle(file_path)
            if data and "equity_data" in data:
                all_equity_data.extend(data["equity_data"])

    # 合并所有股权数据到一个 DataFrame
    if all_equity_data:
        df = pd.DataFrame(all_equity_data)
        # 为 df 添加 df['mysterious'] 列, 依照 attributes list 中只要一项存在字符 '神秘属性'
        df['mysterious'] = df['attributes'].apply(lambda x: any('神秘属性' in s for s in x))
        attribute_pattern = re.compile(r'\((\d+)%\)')
        for i in range(4):  # 假设我们关心的 attributes 从 1 到 4
            attr_col = f'attr_{i+1}'
            df[attr_col] = df['attributes'].apply(lambda x: int(attribute_pattern.search(x[i]).group(1)) if attribute_pattern.search(x[i]) else None)
        return df
    else:
        return pd.DataFrame()
    
def load_and_merge_user_info(data_folder_path, start_year, start_month, end_year, end_month):
    """
    Load and merge user info data from specified period into a single DataFrame.

    :param start_year: int, start year
    :param start_month: int, start month
    :param end_year: int, end year
    :param end_month: int, end month

    :return: DataFrame
    """
    user_info = {}
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            # 构建文件名
            filename = f"momozhen_{year}_{month}.pkl"
            file_path = os.path.join(data_folder_path, filename)
            data = unpickle(file_path)
            if data and "user_info" in data:
                for day, day_data in data["user_info"].items():
                    user_info[f'{year}-{month}-{day}'] = day_data
    # 合并用户所有数据到一个 DataFrame
    if user_info:
        # 将字典转换为 DataFrame，其中字典的键作为行索引
        df = pd.DataFrame.from_dict(user_info, orient='index')
        df.index = pd.to_datetime(df.index)
        df['Rank Numeric'] = df['rank'].map(RANK_MATCH)
        return df
    else:
        return pd.DataFrame()

# --------------------------------------
# Data poltting
# --------------------------------------

def plot_attribute_percentages(percentages, attribute_name):
    """
    显示给定属性的百分比值的频率图
    """
    if attribute_name not in percentages:
        print(f"No data available for {attribute_name}")
        return
    data = percentages[attribute_name]
    x = list(data.keys())
    y = list(data.values())

    # 计算最小和最大百分比值
    min_percentage = min(x)
    max_percentage = max(x)

    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=range(min_percentage, max_percentage+1), weights=y, color='skyblue') # 属性正常范围应该为 50 - 150%
    plt.xlabel('Percentage')
    plt.ylabel('Frequency')
    plt.title(f'{attribute_name} ({min_percentage} - {max_percentage}%)')
    plt.grid(axis='y')
    plt.show()
    return

def plot_attribute_percentages_all(percentages):
    """
    将所有属性的加成百分比转换为一张百分比频率图
    """
    data = defaultdict(int)
    for attribute_name, attribute_data in percentages.items():
        for percentage, count in attribute_data.items():
            data[percentage] += count

    x = list(data.keys())
    y = list(data.values())

    min_percentage = min(x)
    max_percentage = max(x)

    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=range(min_percentage, max_percentage+1), weights=y, color='skyblue') # 属性正常范围应该为 50 - 150%
    plt.xlabel('Percentage')
    plt.ylabel('Frequency')
    plt.title(f'All attributes ({min_percentage} - {max_percentage}%)')
    plt.grid(axis='y')
    plt.show()
    return

def plot_attribute_percentages_i(df, i):
    """
    显示第 i 个属性的百分比值的频率图 (f'attr_{i}', i=1,2,3,4) (histogram)
    
    """
    attr_col = f'attr_{i}'
    x = df[attr_col]

    min_percentage = int(x.min())
    max_percentage = int(x.max())

    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=range(min_percentage, max_percentage+1), color='skyblue') # 属性正常范围应该为 50 - 150%
    plt.xlabel('Percentage')
    plt.ylabel('Frequency')
    plt.title(f'属性 {i} ({min_percentage} - {max_percentage}%)')
    plt.grid(axis='y')
    plt.show()
    return

def plot_total_percentage(df):
    """
    显示 装备 的 `total_percentage` 的频率图 (histogram)

    :param df: DataFrame
    """
    x = df['total_percentage']
    min_percentage = int(x.min())
    max_percentage = int(x.max())

    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=range(min_percentage, max_percentage+1), color='skyblue') # total_percentage 正常范围应该为 200 - 700%
    plt.xlabel('总属性')
    plt.ylabel('Frequency')
    plt.title(f'属性合计 ({min_percentage} - {max_percentage})')
    plt.grid(axis='y')
    plt.show()
    return

def plot_level(df):
    """
    显示 装备 等级的频率图 (histogram)

    :param df: DataFrame
    """
    x = df['level']

    min_level = int(x.min())
    max_level = int(x.max())

    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=range(min_level, max_level+1), color='skyblue')
    plt.xlabel('Level')
    plt.ylabel('Frequency')
    plt.title(f'等级分布 ({min_level} - {max_level})')
    plt.grid(axis='y')
    plt.show()
    return

def plot_pie_chart(df, column):
    """
    绘制给定列的饼图
    """
    # 检查列是否在 DataFrame 中
    if column not in df:
        print(f"Column '{column}' not found in the DataFrame.")
        return
    
    # 按照 momozhen 网站 css 颜色定义
    color_map = {
        "黑色": "dimgrey",   # 灰色, TODO: 不确定
        "红色": "#ea644a",
        "黄色": "#f1a325",
        "绿色": "#38b03f",
        "蓝色": "#03b8cf"
    }
    # 计算每个类别的计数
    data = df[column].value_counts()
    # 分配颜色：如果在 color_map 中则使用预定义颜色，否则随机生成颜色
    colors = [color_map.get(x, plt.cm.tab20.colors[i % len(plt.cm.tab20.colors)]) for i, x in enumerate(data.index)]


    # 创建饼图，无标签显示在图中
    plt.figure(figsize=(12, 6))
    plt.subplot(121)  # 定义一个1行2列的子图，并在第1个位置绘图
    patches, texts, autotexts = plt.pie(data, colors=colors, autopct='%1.1f%%', startangle=140)

    # 去除饼图中的标签
    for text in texts + autotexts:
        text.set_visible(False)

    plt.title(f'Pie Chart of {column}')

    # 创建图例，显示颜色、标签和百分比
    plt.subplot(122)  # 在第2个位置绘图
    legend_labels = [f"{label}: {perc.get_text()}" for label, perc in zip(data.index, autotexts)]
    plt.axis('off')  # 关闭坐标轴
    plt.legend(patches, legend_labels, loc='center', frameon=False)

    plt.tight_layout()
    plt.show()
    return

def plot_user_rank(df):
    """
    绘制用户等级的频率图
    """
    # 绘图展示排位变化
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Rank Numeric'], marker='o')  # 使用日期作为X轴
    plt.xlabel('Date')
    plt.ylabel('段位')
    plt.title('段位 变化图')
    plt.yticks(range(len(RANK_MATCH)), RANK_MATCH.keys())  # 设置Y轴的刻度标签
    plt.grid(axis='y')
    plt.show()
    return

# --------------------------------------
# Data analysis
# --------------------------------------

def print_missing_total_percentage(df, num_initial_missing, num_final_missing):
    """
    打印 装备 的 `total_percentage` 缺失的数值
    """
    # 计算最小值和最大值
    min_percentage = df['total_percentage'].min()
    max_percentage = df['total_percentage'].max()

    # 生成完整的整数序列
    full_range = set(range(min_percentage, max_percentage + 1))

    # 找出缺失的数字
    missing_numbers = list(full_range - set(df['total_percentage']))

    # 对缺失的数字进行排序
    missing_numbers.sort()

    if num_initial_missing > 0:
        # 打印前 num_initial_missing 个缺失的值
        print(f"前 {num_initial_missing} 个缺失的值:")
        if len(missing_numbers) > 0:
            print(missing_numbers[0], "// + 0")  # 第一个缺失值
            for i in range(1, min(num_initial_missing, len(missing_numbers))):
                print(missing_numbers[i], "// +", missing_numbers[i] - missing_numbers[i-1])

    if num_final_missing > 0:
        # 打印后 num_final_missing 个缺失的值
        print(f"\n后 {num_final_missing} 个缺失的值:")
        if len(missing_numbers) > 0:
            start_index = max(0, len(missing_numbers) - num_final_missing)
            for i in range(start_index, len(missing_numbers)):
                if i == start_index:
                    print(missing_numbers[i], "// + 0")  # 为了格式对齐，标记为+0
                else:
                    print(missing_numbers[i], "// +", missing_numbers[i] - missing_numbers[i-1])
    return

def get_attribute_percentages(df):
    """

    """
    # 从 attributes 中提取每项属性的加成百分比 (先检查是否存在 '神秘属性' 词条, 如果存在则不提取, 单独统计出现次数)
    mysterious_count = 0
    attr_perc_dict = defaultdict(lambda: defaultdict(int))

    attribute_pattern = re.compile(r'([^\[]+)\s+\+(\d+\.?\d*)\s+\((\d+)%\)')
    for attributes in df['attributes']:
        for attribute in attributes:
            if '神秘属性' in attribute:
                mysterious_count += 1
            else:
                match = attribute_pattern.match(attribute)
                if match:
                    attr_name = match.group(1).strip()
                    percent = int(match.group(3))
                    attr_perc_dict[attr_name][percent] += 1
    return attr_perc_dict, mysterious_count


# --------------------------------------
# Checking data
# --------------------------------------

def parse_attribute_names(attributes):
    """
    函数从属性字符串解析出属性名称
    """
    # 生命偷取 +19.4% (79%)
    # 提取为 '生命偷取'
    attribute_pattern = re.compile(r'(.+?)\s\+')
    attr_names = []
    for attr in attributes:
        match = attribute_pattern.match(attr)
        if match:
            attr_name = match.group(1).strip()
            attr_names.append(attr_name)
    return attr_names[:4]  # 只取前四个属性

# 检查属性名称的一致性
def check_attribute_consistency(row):
    name = row['name']
    current_attrs = row['parsed_attributes']
    if name in ATTR_ORDER_DICT:
        # 比较属性顺序
        return ATTR_ORDER_DICT[name] == current_attrs
    else:
        # 存储这个名称的属性顺序
        ATTR_ORDER_DICT[name] = current_attrs
        return True

def check_equipment_attribute_data(df):
    """
    检查装备数据的一致性
    
    返回一个新的 df, 包含 'id', 'name', 'parsed_attributes' 和 'is_consistent' 列
    """
    new_df = pd.DataFrame()
    new_df['id'] = df['id']
    new_df['name'] = df['name']
    new_df['parsed_attributes'] = df['attributes'].apply(parse_attribute_names)
    new_df['is_consistent'] = new_df.apply(check_attribute_consistency, axis=1)
    return new_df

