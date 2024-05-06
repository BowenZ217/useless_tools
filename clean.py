import shutil
import os

# 定义要删除的目录列表
directories_to_remove = [
    "logs",
    "sayhuahuo",
    "kf_feiyue",
    "kf_guguzhen",
    "kf_momozhen",
    "level_plus",
    "vikacg",
    "galcg",
    "zodgame",
]

def clean():
    # 遍历目录列表，删除每一个目录
    for directory in directories_to_remove:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"{directory} 已删除。")
        else:
            print(f"{directory} 目录不存在。")

    print("清理完成。")

def main():
    print("是否要清理所有文件夹？(Y/N)")
    user_input = input()
    if user_input.lower() == "y":
        clean()
    else:
        print("取消清理。")

if __name__ == "__main__":
    main()