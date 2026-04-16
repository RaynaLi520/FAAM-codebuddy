@echo off
chcp 65001 >nul
echo ========================================
echo   FAAM 历史数据导入工具
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set HISTORY_SCRIPT=%SCRIPT_DIR%import_history.py

echo 正在执行历史数据导入...
echo 时间: %date% %time%
echo.

python "%HISTORY_SCRIPT%"

if errorlevel 1 (
    echo.
    echo [失败] 导入失败,请查看错误信息
) else (
    echo.
    echo [成功] 历史数据导入完成!
)

echo.
pause
