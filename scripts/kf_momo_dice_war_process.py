import bz2
import json
import os
import pickle
import re

from bs4 import BeautifulSoup

# Global variables to store the statistics and battle records
total_rewards_statistics = {}
awards_count_statistics = {}
battle_results_statistics = {}
battle_records = []

KF_MOMOZHEN_DICE_WAR_REWARD_STATS_PATH = "./data/kf_momozhen_dice_war_reward_stats.json"
KF_MOMOZHEN_DICE_WAR_BATTLE_RECORDS_PATH = "./data/kf_momozhen_dice_war_battle_records.pkl"
KF_MOMOZHEN_DICE_WAR_DATA_FOLDER = "./kf_momozhen" # "dice_war_{id}.txt"

# -----------------------
# File I/O
# -----------------------

def unpickle(file):
    """
    Unpickle file using bz2 and pickle.
    :param file: file path

    :return: data from file
    """
    if not os.path.exists(file):
        return None
    with bz2.open(file, 'rb') as fo:
        return pickle.load(fo)

def pickle_data(data, file):
    """
    Pickle data to file using bz2 and pickle.

    :param data: data to pickle
    :param file: file path
    """
    with bz2.open(file, 'wb') as fo:
        pickle.dump(data, fo)

def load_data():
    global total_rewards_statistics
    global awards_count_statistics
    global battle_results_statistics
    global battle_records

    try:
        with open(KF_MOMOZHEN_DICE_WAR_REWARD_STATS_PATH, "r", encoding="utf-8") as f:
            reward_states = json.load(f)
            total_rewards_statistics = reward_states["总奖励统计"]
            awards_count_statistics = reward_states["奖励次数统计"]
            battle_results_statistics = reward_states["战斗结果统计"]
    except FileNotFoundError:
        total_rewards_statistics = {}
        awards_count_statistics = {}
        battle_results_statistics = {}
    
    try:
        # with open(KF_MOMOZHEN_DICE_WAR_BATTLE_RECORDS_PATH, "r", encoding="utf-8") as f:
        #     battle_records = json.load(f)
        battle_records = unpickle(KF_MOMOZHEN_DICE_WAR_BATTLE_RECORDS_PATH)
        if not battle_records:
            battle_records = []
    except FileNotFoundError:
        battle_records = []

def save_data():
    reward_states = {
        "总奖励统计": total_rewards_statistics,
        "奖励次数统计": awards_count_statistics,
        "战斗结果统计": battle_results_statistics
    }
    with open(KF_MOMOZHEN_DICE_WAR_REWARD_STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(reward_states, f, ensure_ascii=False, indent=4)
    
    # with open(KF_MOMOZHEN_DICE_WAR_BATTLE_RECORDS_PATH, "w", encoding="utf-8") as f:
    #     json.dump(battle_records, f, ensure_ascii=False, indent=4)
    pickle_data(battle_records, KF_MOMOZHEN_DICE_WAR_BATTLE_RECORDS_PATH)

def process_dice_war_page(html_content: str):
    global awards_count_statistics, battle_records, battle_results_statistics

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract battle records
    battle_info = {
        "敌人名称": "",
        "战斗过程": [],
        "结果": ""
    }

    # Find enemy name and result
    enemy_btns = soup.find_all("button", class_="btn fyg_tc fyg_mp3")
    for btn in enemy_btns:
        if "你遇到了" in btn.text:
            enemy_name = btn.get_text(separator=' ', strip=True).replace("你遇到了", "").strip()
            battle_info["敌人名称"] = enemy_name
        elif any(result in btn.text for result in ["胜利", "失败", "平局"]):
            battle_info["结果"] = btn.text.strip()
            battle_results_statistics[btn.text.strip()] = battle_results_statistics.get(btn.text.strip(), 0) + 1

    # Find battle process for both sides
    process_btns = soup.find_all("button", class_=["btn fyg_tr fyg_mp3", "btn fyg_tl fyg_mp3"])
    rounds = len(process_btns) // 2  # Assuming each round has both sides

    for i in range(0, rounds * 2, 2):
        round_info = {"User": {}, "Enemy": {}}

        # Process each side
        for side in ["User", "Enemy"]:
            btn = process_btns[i + (side == "Enemy")]
            # Dice points
            # Find all <span> elements that have "fyg_f14" class
            span_elements = btn.find_all("span", class_="fyg_f14")
            for span in span_elements:
                # Check if any class of this span element starts with "label"
                if any(c.startswith("label") for c in span["class"]):
                    round_info[side]["点数"] = span.text.strip()
            # dice_span = btn.find("span", class_="fyg_f14 label")
            # if dice_span:
            #     round_info[side]["点数"] = dice_span.text.strip()

            
            # Current health status
            health_span_left = btn.find("span", class_="fyg_f14 text-success pull-left")
            health_span_right = btn.find("span", class_="fyg_f14 text-success pull-right")
            if health_span_left:
                round_info[side]["当前状态"] = health_span_left.text.strip()
            elif health_span_right:
                round_info[side]["当前状态"] = health_span_right.text.strip()
            # health_span = btn.find("span", class_="fyg_f14 text-success")
            # if health_span:
            #     round_info[side]["当前状态"] = health_span.text.strip()
            # Damage taken
            damage_icon = btn.find("i", class_="icon icon-arrow-down text-danger")
            if damage_icon:
                round_info[side]["受伤"] = damage_icon.text.strip()
            # Special condition handling
            special_condition_span = btn.find("span", class_="text-danger fyg_f14")
            if special_condition_span:
                round_info[side]["特殊状态"] = special_condition_span.text.strip()

            # Extracting health gained from "吸血" action
            health_gain_icon = btn.find("i", class_="icon icon-arrow-up text-success")
            if health_gain_icon:
                round_info[side]["血量恢复"] = health_gain_icon.text.strip()

        if round_info["User"] or round_info["Enemy"]:
            battle_info["战斗过程"].append(round_info)

    # Update global variables
    battle_records.append(battle_info)

    # Extract and update the awards_count_statistics from the script tags
    script_tags = soup.find_all("script")
    for script in script_tags:
        if "tzzzdjl" in script.text:
            match = re.search(r'tzzzdjl\("(.*?)",', script.text)
            if match:
                award_message = match.group(1)
                if award_message in awards_count_statistics:
                    awards_count_statistics[award_message] += 1
                else:
                    awards_count_statistics[award_message] = 1

def process_dice_war_pages(start_page: int = 0, end_page: int = 29):
    """
    Process the dice war page from 0 to 29
    """
    for i in range(start_page, end_page + 1):
        print(f"Processing dice war page {i}...")
        try:
            with open(f"{KF_MOMOZHEN_DICE_WAR_DATA_FOLDER}/dice_war_{i}.txt", "r", encoding="utf-8") as f:
                html_content = f.read()
                process_dice_war_page(html_content)
        except FileNotFoundError:
            print(f"File {KF_MOMOZHEN_DICE_WAR_DATA_FOLDER}/dice_war_{i}.txt not found.")
            continue
        except Exception as e:
            print(f"An error occurred while processing dice war page {i}: {e}")
            continue

def process_total_rewards_statistics():
    """
    统计总奖励数据
    """
    global total_rewards_statistics
    patterns = {
        "贝壳": r"获得 (\d+) 贝壳",
        "星沙": r"获得 (\d+) 星沙",
        "SVIP": r"获得SVIP (\d+) 天",
        "BVIP": r"获得BVIP (\d+) 天",
        "光环天赋石": r"获得光环天赋提升道具 光环天赋石",
        "灵魂药水": r"获得角色卡片强化道具 灵魂药水",
        "随机装备箱": r"获得沙滩装备刷新道具 随机装备箱",
        "体能刺激药水": r"获得体力恢复道具 体能刺激药水",
        # Add more patterns if needed
    }
    total_times_count = 0
    for award_message, count in awards_count_statistics.items():
        total_times_count += count
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, award_message)
            if match:
                # 如果是数字奖励类型 (如贝壳、星沙), 需要将匹配到的数量转换为整数后进行累加
                if pattern_name in ["贝壳", "星沙", "SVIP", "BVIP"]:
                    quantity = int(match.group(1)) * count  # 将数量乘以次数得到总量
                    if pattern_name in total_rewards_statistics:
                        total_rewards_statistics[pattern_name] += quantity
                    else:
                        total_rewards_statistics[pattern_name] = quantity
                else:  # 对于非数字类型的奖励, 直接累加次数
                    if pattern_name in total_rewards_statistics:
                        total_rewards_statistics[pattern_name] += count
                    else:
                        total_rewards_statistics[pattern_name] = count
    total_rewards_statistics["总次数"] = total_times_count
    return

def main():
    # Load data from JSON files
    load_data()

    process_dice_war_pages(0, 159)
    process_total_rewards_statistics()

    # Save data to JSON files
    save_data()

if __name__ == "__main__":
    main()