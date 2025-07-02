@echo off
setlocal enabledelayedexpansion

echo 正在安装 ModelScope...
pip install modelscope

echo 正在安装 FunASR...
pip install "funasr[all]"

echo 正在下载 SenseVoiceSmall 模型...
set LOCAL_ENV_PATH=%~dp0local_env\meeting-minutes-local
set MODEL_PATH=%LOCAL_ENV_PATH%\models\iic\SenseVoiceSmall

if not exist "%MODEL_PATH%" (
    mkdir "%MODEL_PATH%"
    modelscope download --model iic/SenseVoiceSmall --cache-dir "%LOCAL_ENV_PATH%\models"
)

echo 安装完成！
pause 