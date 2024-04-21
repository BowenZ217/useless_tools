import datetime
import json
import os


CURRENT_MONTH = str(datetime.datetime.now().month)
CURRENT_YEAR = str(datetime.datetime.now().year)

REPORT_FILE_PATH = f"./reports/report_{CURRENT_YEAR}.md"

# DATA FILE PATH
KF_MOMOZHEN_DATA_FILE_PATH = f"./data/kf_momozhen_{CURRENT_YEAR}.json"
OTHERS_DATA_FILE_PATH = f"./data/others_{CURRENT_YEAR}.json"

KF_MOMOZHEN_DATA = {}
OTHERS_DATA = {}

# ----------------------------------------------
# 初始化数据文件
# ----------------------------------------------

def init_data():
    """初始化全局数据"""
    global KF_MOMOZHEN_DATA
    global OTHERS_DATA

    if os.path.exists(KF_MOMOZHEN_DATA_FILE_PATH):
        with open(KF_MOMOZHEN_DATA_FILE_PATH, "r", encoding="utf-8") as file:
            KF_MOMOZHEN_DATA = json.load(file)
    else:
        return False
    if os.path.exists(OTHERS_DATA_FILE_PATH):
        with open(OTHERS_DATA_FILE_PATH, "r", encoding="utf-8") as file:
            OTHERS_DATA = json.load(file)
    else:
        return False
    return True


# ----------------------------------------------
# helper functions
# ----------------------------------------------

def clear_file(filename):
    """清空文件内容"""
    # 使用'w'模式打开文件，这将清空文件内容
    with open(filename, 'w') as file:
        pass  # 打开文件后不做任何操作，自动清空内容

def merge_data(data1, data2):
    """合并两个数据字典"""
    for key in data2:
        if key in data1:
            data1[key] += data2[key]
        else:
            data1[key] = data2[key]
    return data1

# ----------------------------------------------
# 报告
# ----------------------------------------------

def generate_report(kf_momozhen_data, others_data):
    """
    生成报告 (md 格式) 并写入文件

    :param kf_momozhen_data: dict
    :param others_data: dict
    """
    rarity_name_map = {
        '1': "黑色",
        '2': "蓝色",
        '3': "绿色",
        '4': "黄色",
        '5': "红色",
    }

    with open(REPORT_FILE_PATH, "a", encoding="utf-8") as file:
        # file.write(f"## {CURRENT_YEAR} 年 {month} 月报告\n\n")
        file.write("### kf 绯月 (咕咕镇) 数据\n\n")
        file.write("#### 争夺战场\n\n")
        file.write("##### 出击情况\n\n")
        file.write(f"使用 `体力药水`: {kf_momozhen_data['使用体力药水']['次数']} 次\n\n")
        file.write(f"胜利次数: {kf_momozhen_data['battle']['win_count']}\n\n")
        file.write(f"败北次数: {kf_momozhen_data['battle']['lose_count']}\n\n")
        file.write(f"平局次数: {kf_momozhen_data['battle']['draw_count']}\n\n")
        file.write("##### 翻牌情况\n\n")
        file.write("###### 次数统计\n\n")
        for key, count in kf_momozhen_data["翻牌"]["次数统计"].items():
            file.write(f"`{key}` : {count} 次\n\n")
        file.write("###### 奖励统计\n\n")
        for key, count in kf_momozhen_data["翻牌"]["奖励"].items():
            file.write(f"`{key}` : {count}\n\n")

        file.write("#### 我的沙滩 (装备)\n\n")
        file.write("##### 神秘装备\n\n")
        for key, count in kf_momozhen_data["沙滩"]["神秘装备"].items():
            file.write(f"出现 `{rarity_name_map[key]}` 神秘装备 {count} 件\n\n")

        # 写入领取信息
        file.write("##### 领取\n\n")
        for key, count in kf_momozhen_data["沙滩"]["pick_count"].items():
            file.write(f"`{rarity_name_map[key]}` 装备 {count} 件\n\n")

        # 写入熔炼信息
        file.write("##### 熔炼\n\n")
        for key, count in kf_momozhen_data["沙滩"]["melt_count"].items():
            file.write(f"`{rarity_name_map[key]}` 装备 {count} 件\n\n")
        file.write("收获护符:\n\n")
        for charm, levels in kf_momozhen_data["护符信息"].items():
            for level, number in levels.items():
                file.write(f"`{charm}` (+ {level}) {number} 个\n\n")

        # 写入清理信息
        file.write("##### 清理\n\n")
        for key, count in kf_momozhen_data["沙滩"]["clean_count"].items():
            file.write(f"`{rarity_name_map[key]}` 装备 {count} 件\n\n")
        file.write("清理得到:\n\n")
        for item, amount in kf_momozhen_data["沙滩"]["clean_result"].items():
            file.write(f"{amount} 个 `{item}`\n\n")

        file.write("#### 宝石工坊\n\n")
        for key, count in kf_momozhen_data["宝石工坊"]["奖励"].items():
            file.write(f"`{key}` : {count}\n\n")

        file.write("#### 许愿池\n\n")
        for key, count in kf_momozhen_data["许愿池"]["词条次数"].items():
            file.write(f"{count} 次 `{key}`\n\n")


        file.write("### level-plus 数据\n\n")
        file.write("#### 完成任务\n\n")
        for key, count in others_data["level_plus"]["tasks_completed"].items():
            file.write(f"`{key}` : {count} 次\n\n")

        file.write("### vikacg 数据\n\n")
        file.write(f"签到获得 {others_data['vikacg']['credit_added']} 积分\n\n")

        file.write("### galcg 数据\n\n")
        file.write(f"签到获得 {others_data['galcg']['credit_added']} 积分\n\n")
    return

def generate_current_year_report():
    """生成当前年度报告"""
    kf_momozhen_year_total_data = {}
    others_year_total_data = {}
    for month in range(1, 13):
        month = str(month)
        if month in KF_MOMOZHEN_DATA:
            kf_momozhen_year_total_data = merge_data(kf_momozhen_year_total_data, KF_MOMOZHEN_DATA[month])
        if month in OTHERS_DATA:
            others_year_total_data = merge_data(others_year_total_data, OTHERS_DATA[month])
    
    with open(REPORT_FILE_PATH, "a", encoding="utf-8") as file:
        file.write(f"## {CURRENT_YEAR} 年 统计报告\n\n")
    generate_report(kf_momozhen_year_total_data, others_year_total_data)

    # 生成每个月的报告
    for month in range(1, 13):
        month = str(month)
        if month in KF_MOMOZHEN_DATA and month in OTHERS_DATA:
            with open(REPORT_FILE_PATH, "a", encoding="utf-8") as file:
                file.write("\n-------------------------------------\n\n\n")
                file.write(f"## {CURRENT_YEAR} 年 {month} 月报告\n\n")
            generate_report(KF_MOMOZHEN_DATA[month], OTHERS_DATA[month])

    return








# ----------------------------------------------
# 主函数
# ----------------------------------------------
def main():
    """主函数"""
    if not init_data():
        print("初始化数据失败")
        return
    
    clear_file(REPORT_FILE_PATH)
    generate_current_year_report()
    return

if __name__ == "__main__":
    main()
