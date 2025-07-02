@echo off
setlocal enabledelayedexpansion

set CONDA_ENV_PATH=D:\项目大全\会议纪要生成神器（本地保密版）V1.0\local_env\meeting-minutes-local

echo ========================================
echo 正在安装项目依赖...
echo 环境路径: %CONDA_ENV_PATH%
echo ========================================

REM 检查环境是否存在
if not exist "%CONDA_ENV_PATH%" (
    echo 错误：conda环境不存在！
    echo 请先运行 create_local_env.py 创建环境
    pause
    exit /b 1
)

echo.
echo 正在安装基础依赖...
call conda run -p "%CONDA_ENV_PATH%" pip install -r requirements.txt
if errorlevel 1 (
    echo 安装基础依赖失败！
    pause
    exit /b 1
)

echo.
echo 正在安装 ModelScope...
call conda run -p "%CONDA_ENV_PATH%" pip install "modelscope[audio]"
if errorlevel 1 (
    echo 安装 ModelScope 失败！
    pause
    exit /b 1
)

echo.
echo 正在安装 FunASR...
call conda run -p "%CONDA_ENV_PATH%" pip install "funasr[all]"
if errorlevel 1 (
    echo 安装 FunASR 失败！
    pause
    exit /b 1
)

echo.
echo 正在下载 SenseVoiceSmall 模型...
set MODEL_PATH=%CONDA_ENV_PATH%\models\iic\SenseVoiceSmall

if not exist "%MODEL_PATH%" (
    mkdir "%MODEL_PATH%"
    call conda run -p "%CONDA_ENV_PATH%" modelscope download --model iic/SenseVoiceSmall --cache-dir "%CONDA_ENV_PATH%\models"
)

echo.
echo ========================================
echo 所有依赖安装完成！
echo ========================================
pause 