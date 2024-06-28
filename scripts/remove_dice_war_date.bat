@echo off
setlocal enabledelayedexpansion

for %%f in (dice_war_*.txt) do (
    set "filename=%%~nf"
    set "extension=%%~xf"

    rem 移除 'dice_war_' 前缀和 '.txt' 后缀，只处理中间部分
    set "base=!filename:dice_war_=!"
    
    rem 提取索引部分，假设结构为 index 或 index_date
    for /f "tokens=1 delims=_" %%i in ("!base!") do set "index=%%i"
    
    rem 重构文件名，添加 'dice_war_' 前缀和 '.txt' 后缀
    set "newname=dice_war_!index!!extension!"

    if not "%%f"=="!newname!" (
        echo Renaming %%f to !newname!
        ren "%%f" "!newname!"
    )
)

echo Done.
pause
