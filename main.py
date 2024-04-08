import datetime
import time

# 引用 src 包下的模块
from src.utils import logger, json_data_handler
from src import kf_momozhen, sayhuahuo, kf_feiyue, level_plus, vikacg, galcg, jmcomic
# from src import kf_momozhen_backup_1

def main():
    # 设置日志
    log = logger.setup_logging()
    current_year = datetime.datetime.now().year
    json_path = f"./data/others_{current_year}.json"
    json_data_handler.set_data_file_path(json_path)
    json_data_handler.increment_value(1, "total_run_count")

    # 开始执行 花火链接
    sayhuahuo.sayhuahuo_start()

    # 开始执行 kf 绯月
    kf_momozhen.kf_momozhen_start()
    # kf_momozhen_backup_1.kf_momozhen_start() # 备用
    time.sleep(1)
    kf_feiyue.kf_feiyue_start()

    # leve-plus 签到
    level_plus.level_plus_start()

    # vikacg 签到
    vikacg.vikacg_start()

    # galcg 签到
    galcg.galcg_start()

    # jmcomic 签到
    jmcomic.jmcomic_start()
    return

def test():
    # 设置日志
    log = logger.setup_logging()

    # 测试 xxx 模块
    # kf_momozhen.kf_momozhen_start()

    # 测试 json_data_handler 模块
    # import datetime
    # current_year = datetime.datetime.now().year
    # json_path = f"./data/kf_momozhen_{current_year}.json"
    # json_data_handler.set_data_file_path(json_path)
    # json_data_handler.increment_value(10, "4", "battle_info", "win_count")
    # json_data_handler.increment_value(9, "4", "battle_info", "lose_count")
    # json_data_handler.increment_value(1, "4", "battle_info", "draw_count")
    # # try delete
    # json_data_handler.delete_key("4", "battle_info", "draw_count")
    # exist = json_data_handler.path_exists("4", "battle_info", "draw_count")
    # print(f"draw_count exist: {exist}")
    # exist = json_data_handler.path_exists("4", "battle_info", "lose_count")
    # print(f"lose_count exist: {exist}")
    # # json_data_handler.write_data()
    # json_path = f"./data/others_{current_year}.json"
    # json_data_handler.set_data_file_path(json_path)
    # json_data_handler.increment_value(1, "4", "level_plus", "task 1")
    # json_data_handler.increment_value(1, "4", "level_plus", "task 2")
    # json_data_handler.increment_value(1, "4", "level_plus", "task 3")

    
    jmcomic.jmcomic_start()

    return

if __name__ == "__main__":
    main()
    # test()
