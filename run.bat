:: 推荐优先使用 run_local.bat 启动项目，确保依赖和环境隔离。
:: 本脚本仅供全局环境已配置好依赖时临时使用。
@echo off
chcp 65001
echo ========================================
echo 会议纪要生成神器（本地保密版）V1.0
echo 启动脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python环境
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo 正在检查依赖项...
python -c "import customtkinter, ffmpeg, pydub, requests, docx, librosa, soundfile" >nul 2>&1
if errorlevel 1 (
    echo 错误: 缺少必要的依赖项
    echo 请运行 install.bat 安装依赖项
    pause
    exit /b 1
)

echo 正在启动应用...
python main.py

if errorlevel 1 (
    echo.
    echo 应用运行出错
    echo 请检查错误信息并解决问题
    pause
) 