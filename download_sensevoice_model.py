import os
import shutil
from modelscope.hub.snapshot_download import snapshot_download

# SenseVoiceSmall 目标路径
SENSEVOICE_PATH = os.path.join(
    'local_env', 'meeting-minutes-local', 'models', 'iic', 'SenseVoiceSmall'
)
# VAD模型目标路径
VAD_PATH = os.path.join(
    'local_env', 'meeting-minutes-local', 'models', 'iic', 'speech_fsmn_vad_zh-cn-16k-common-pytorch'
)

# 下载 SenseVoiceSmall
print('正在下载 SenseVoiceSmall 语音识别模型...')
sensevoice_dir = snapshot_download('iic/SenseVoiceSmall',
                                  cache_dir=None,
                                  revision=None,
                                  ignore_file_pattern=[r'.*\.bin\.tmp$'])
print(f'SenseVoiceSmall 模型已下载到: {sensevoice_dir}')
os.makedirs(SENSEVOICE_PATH, exist_ok=True)
print(f'正在复制 SenseVoiceSmall 到: {SENSEVOICE_PATH}')
for item in os.listdir(sensevoice_dir):
    s = os.path.join(sensevoice_dir, item)
    d = os.path.join(SENSEVOICE_PATH, item)
    if os.path.isdir(s):
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)
print('SenseVoiceSmall 复制完成！')

# 下载 VAD 模型
print('正在下载 VAD 语音活动检测模型...')
vad_dir = snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
                           cache_dir=None,
                           revision=None,
                           ignore_file_pattern=[r'.*\.bin\.tmp$'])
print(f'VAD 模型已下载到: {vad_dir}')
os.makedirs(VAD_PATH, exist_ok=True)
print(f'正在复制 VAD 模型到: {VAD_PATH}')
for item in os.listdir(vad_dir):
    s = os.path.join(vad_dir, item)
    d = os.path.join(VAD_PATH, item)
    if os.path.isdir(s):
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)
print('VAD 模型复制完成！') 