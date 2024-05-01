import datetime
import os
import pickle
import re

from bs4 import BeautifulSoup

CURRENT_DAY = str(datetime.datetime.now().day)
CURRENT_MONTH = str(datetime.datetime.now().month)
CURRENT_YEAR = str(datetime.datetime.now().year)

KF_MOMOZHEN_FOLDER_PATH = "data"
KF_MOMOZHEN_DATA_PATH = os.path.join(KF_MOMOZHEN_FOLDER_PATH, f"momozhen_{CURRENT_YEAR}_{CURRENT_MONTH}.pkl")
KF_MOMOZHEN_BATTLE_DATA_PATH = os.path.join(KF_MOMOZHEN_FOLDER_PATH, f"momozhen_battle_{CURRENT_YEAR}_{CURRENT_MONTH}.pkl")

KF_MOMOZHEN_DATA = {}
KF_MOMOZHEN_BATTLE_DATA = []

# -----------------------
# File I/O
# -----------------------

def unpickle(file):
    """
    Unpickle file
    :param file: file path

    :return: dict
    """
    if not os.path.exists(file):
        return None
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

def pickle_data(data, file):
    """
    Pickle data to file

    :param data: data to pickle
    :param file: file path
    """
    with open(file, 'wb') as fo:
        pickle.dump(data, fo)

def load_data():
    """
    Load data from pickle file
    """
    global KF_MOMOZHEN_DATA, KF_MOMOZHEN_BATTLE_DATA
    KF_MOMOZHEN_DATA = unpickle(KF_MOMOZHEN_DATA_PATH)
    if KF_MOMOZHEN_DATA is None:
        KF_MOMOZHEN_DATA = {}
    KF_MOMOZHEN_BATTLE_DATA = unpickle(KF_MOMOZHEN_BATTLE_DATA_PATH)
    if KF_MOMOZHEN_BATTLE_DATA is None:
        KF_MOMOZHEN_BATTLE_DATA = []

def save_data():
    """
    Save data to pickle file
    """
    global KF_MOMOZHEN_DATA, KF_MOMOZHEN_BATTLE_DATA
    pickle_data(KF_MOMOZHEN_DATA, KF_MOMOZHEN_DATA_PATH)
    pickle_data(KF_MOMOZHEN_BATTLE_DATA, KF_MOMOZHEN_BATTLE_DATA_PATH)

# -----------------------
# Data parsing
# -----------------------

def parse_guguzhen_battle_state(soup):
    def extract_skills(skill_section):
        skills = []
        for skill in skill_section.find_all('i', class_='icon'):
            if skill.b:
                skills.append(skill.b.text.strip())
        return skills

    def extract_stats(stats_section):
        stats = {
            '技能': extract_skills(stats_section),
            '血量变化': 0,
            '护盾变化': 0,
            '绝伤': 0,
            '法伤': 0,
            '物伤': 0,
            '当前血量': 0,
            '当前护盾': 0
        }

        # Extract changes in HP and HD
        for change in stats_section.find_all('i', class_='fyg_f14'):
            text = change.text
            value = int(re.search(r'\d+', text).group())
            if 'text-danger' in change['class']:
                if 'icon-plus' in change['class']:
                    stats['血量变化'] += value
                elif 'icon-minus' in change['class']:
                    stats['血量变化'] -= value
            elif 'text-info' in change['class']:
                if 'icon-plus' in change['class']:
                    stats['护盾变化'] += value
                elif 'icon-minus' in change['class']:
                    stats['护盾变化'] = -value
            elif 'icon-bolt' in change['class']:
                if 'text-danger' in change['class']:
                    stats['绝伤'] = value
                elif 'text-primary' in change['class']:
                    stats['法伤'] = value
                elif 'text-warning' in change['class']:
                    stats['物伤'] = value

        # Extract current HP and HD
        current_stats = stats_section.find_all('span', class_='fyg_pvedt')
        if len(current_stats) == 2:
            stats['当前护盾'] = int(current_stats[0].text.strip())
            stats['当前血量'] = int(current_stats[1].text.strip())

        return stats

    stats_divs = soup.find_all("div", class_="col-md-6")
    user_stats = extract_stats(stats_divs[0])
    enemy_stats = extract_stats(stats_divs[1])

    return {
        'user_states': user_stats,
        'enemy_states': enemy_stats
    }


def parse_guguzhen_battle_info(soup):
    # Initialize the resulting object
    result = {
        'user_info': {},
        'enemy_info': {}
    }

    # Helper function to extract and format user and enemy data
    def extract_data(container, info_key):
        # Extract name, card name and level
        name_info = container.find('span', class_='fyg_f18').text.strip()
        # 格式为 "（Lv.775 默）{name}"
        name_match = re.search(r'\（Lv\.(\d+) ([^）]+)\）(.+)', name_info)
        if name_match:
            card_level, card_name, name = name_match.groups()
            result[info_key]['name'] = name.strip()
            result[info_key]['card_name'] = card_name.strip()
            result[info_key]['card_level'] = int(card_level)
        else:
            # 格式为 "{name}（梦 Lv.701）"
            name_match = re.search(r'(.+?)\（([^ ]+) Lv\.(\d+)\）', name_info)
            if name_match:
                name, card_name, card_level = name_match.groups()
                result[info_key]['name'] = name.strip()
                result[info_key]['card_name'] = card_name.strip()
                result[info_key]['card_level'] = int(card_level)

        # Extract stats
        stats = container.find_all('span', class_='label-outline')
        card_stat = {}
        for stat in stats:
            stat_text = stat.text.strip()
            stat_match = re.search(r'(\d+) (\S+)', stat_text)
            if stat_match:
                value, key = stat_match.groups()
                card_stat[key] = int(value)
        result[info_key]['card_stat'] = card_stat

        # Extract equipment and abilities
        equipment = {}
        abilities = []
        
        buttons = container.find_all('button', class_='fyg_colpzbg')
        categories = ['武器', '手饰', '衣着', '头饰']
        category_index = 0
        rarity_pattern = r'url\(ys/icon/z/z\d+_(\d)\.gif\);'
        for button in buttons:
            tooltip = button.get('data-original-title') or button.get('title')
            style = button.get('style')
            level = button.text.strip()
            rarity_match = re.search(rarity_pattern, style)
            rarity = rarity_match.group(1) if rarity_match else 'Unknown'

            if tooltip:
                category = categories[category_index % len(categories)]
                equipment[category] = {
                    'name': tooltip,
                    'rarity': rarity,
                    'level': level
                }
                category_index += 1

        # Extract talents (assumed to be all text after buttons as abilities)
        ability_text = container.text.strip()
        ability_matches = re.findall(r'\|([^|]+)\|', ability_text)
        abilities.extend(ability_matches)

        result[info_key]['武器装备'] = equipment
        result[info_key]['光环天赋'] = abilities

    # Extract user and enemy info from corresponding parts of the HTML
    user_container = soup.select_one('.alert-danger')
    enemy_container = soup.select_one('.alert-info')

    extract_data(user_container, 'user_info')
    extract_data(enemy_container, 'enemy_info')
    result['user_info']['name'] = 'User'

    return result

def parse_guguzhen_battle_final_state(winner_soup, state_soup):
    # Extract final result
    final_result = "No winner"
    winner_patterns = ['alert alert-danger with-icon fyg_tc', 'alert alert-info with-icon fyg_tc', 'alert with-icon fyg_tc']
    for pattern in winner_patterns:
        winner_div = winner_soup.find('div', class_=re.compile(pattern))
        if winner_div:
            final_result = winner_div.get_text(strip=True)
            if pattern == 'alert alert-danger with-icon fyg_tc':
                final_result = "User 获得了胜利!"
            break

    def extract_values(user):
        stats = {}

        # 定义每种类型的图标和类别样式
        categories = {
            "回血": ("icon-plus", "text-danger"),
            "掉血": ("icon-minus", "text-danger"),
            "回盾": ("icon-plus", "text-info"),
            "掉盾": ("icon-minus", "text-info"),
            "绝伤": ("icon-bolt", "text-warning"),
            "法伤": ("icon-bolt", "text-primary"),
            "物伤": ("icon-bolt", "text-danger")
        }

        # 遍历每个类型及其对应的图标和类别样式
        for name, (icon, text_class) in categories.items():
            # 查找与图标和类别样式相匹配的元素
            items = user.find_all('i', class_=re.compile(f'{icon} {text_class}'))
            values = [item.get_text(strip=True) for item in items]
            if name in values:
                index = values.index(name) + 1
                if index < len(items):
                    stats[name] = int(re.sub(r'\D', '', items[index].get_text(strip=True)))

        return stats

    # User and enemy extraction based on structure observed in the HTML
    user_div = state_soup.find_all('div', class_='col-md-6')[0]
    enemy_div = state_soup.find_all('div', class_='col-md-6')[1]

    user_final_state = extract_values(user_div)
    enemy_final_state = extract_values(enemy_div)

    return {
        'final_result': final_result,
        'user_final_state': user_final_state,
        'enemy_final_state': enemy_final_state
    }


def parse_guguzhen_battle(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    divs = soup.find_all('div')
    rows = [div for div in divs if div.get('class') == ['row']]

    info_div = rows[0] if rows else None
    battle_info = parse_guguzhen_battle_info(info_div)

    state_divs = soup.find_all('div', class_='fyg_pvero')
    battle_states = []
    for state in state_divs:
        battle_state = parse_guguzhen_battle_state(state)
        battle_states.append(battle_state)

    winner_soup = rows[-1] if rows else None
    state_soups = div_with_classes = soup.find_all('div', class_=['row', 'fyg_nw', 'fyg_tc', 'fyg_lh40'])
    state_soup = state_soups[-1] if state_soups else None
    final_state = parse_guguzhen_battle_final_state(winner_soup, state_soup)

    return {
        'battle_info': battle_info,
        'battle_states': battle_states,
        'final_state': final_state
    }

# -----------------------
# Data Manipulation
# -----------------------

def add_equity_data(equity_data: dict):
    """
    Add equity data to momozhen data

    :param equity_data: dict

        format: {
            "name": str,
            "rarity": str,
            "total_percentage": int,
            "level": int,
            "id": str,
            "attributes": list,
        }
    """
    global KF_MOMOZHEN_DATA
    if 'equity_data' not in KF_MOMOZHEN_DATA:
        KF_MOMOZHEN_DATA['equity_data'] = []
    KF_MOMOZHEN_DATA['equity_data'].append(equity_data)

def add_user_info(user_info: dict):
    """
    Add user info to momozhen data

    :param user_info: dict

    KF_MOMOZHEN_DATA['user_info'] = {
        "1": user_info_day_1
    }
    """
    global KF_MOMOZHEN_DATA
    if 'user_info' not in KF_MOMOZHEN_DATA:
        KF_MOMOZHEN_DATA['user_info'] = {}
    if CURRENT_DAY not in KF_MOMOZHEN_DATA['user_info']:
        KF_MOMOZHEN_DATA['user_info'][CURRENT_DAY] = user_info

def add_battle_data(battle_data: str):
    """
    Add battle data to momozhen data

    :param battle_data
    """
    global KF_MOMOZHEN_BATTLE_DATA
    battle_dict = parse_guguzhen_battle(battle_data)
    KF_MOMOZHEN_BATTLE_DATA.append(battle_dict)
