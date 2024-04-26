import datetime
import os
import pickle

CURRENT_DAY = str(datetime.datetime.now().day)
CURRENT_MONTH = str(datetime.datetime.now().month)
CURRENT_YEAR = str(datetime.datetime.now().year)

KF_MOMOZHEN_FOLDER_PATH = "data"
KF_MOMOZHEN_DATA_PATH = os.path.join(KF_MOMOZHEN_FOLDER_PATH, f"momozhen_{CURRENT_YEAR}_{CURRENT_MONTH}.pkl")

KF_MOMOZHEN_DATA = {}

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
        return {}
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
    global KF_MOMOZHEN_DATA
    KF_MOMOZHEN_DATA = unpickle(KF_MOMOZHEN_DATA_PATH)

def save_data():
    """
    Save data to pickle file
    """
    global KF_MOMOZHEN_DATA
    pickle_data(KF_MOMOZHEN_DATA, KF_MOMOZHEN_DATA_PATH)

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
