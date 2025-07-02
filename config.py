"""
配置文件 - 会议纪要生成神器
"""

import os
import json
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            # Ollama配置
            "ollama_api_url": "http://127.0.0.1:11434/v1/chat/completions",
            "ollama_model": "deepseek-r1:1.5b",
            
            # 系统限制
            "max_audio_duration": 2 * 60 * 60,  # 2小时（秒）
            "max_file_size": 1 * 1024 * 1024 * 1024,  # 1GB（字节）
            
            # 音频处理
            "audio_format": "mp3",
            "audio_sample_rate": 16000,
            "audio_channels": 1,
            
            # 日志配置
            "log_dir": "logs",
            "log_retention_days": 30,
            "enable_conversation_logging": True,
            "log_level": "INFO",
            
            # 默认提示词
            "default_prompt": """请根据以下会议录音文本和会议描述信息，生成一份格式化的会议纪要。

会议描述信息：
{meeting_info}

会议录音文本：
{transcription}

请按照以下格式生成会议纪要：

# 会议纪要

## 会议基本信息
- 会议时间：{meeting_time}
- 会议地点：{meeting_location}
- 主持人：{host}
- 参会人员：{participants}

## 会议议题
{topics}

## 会议内容
{content}

## 会议决议
{decisions}

## 后续行动
{actions}

请确保会议纪要内容准确、简洁、条理清晰，突出重点内容。""",
            
            # 临时文件路径
            "temp_dir": "temp",
            
            # 模型配置
            "speech_model": "SenseVoiceSmall",
            "use_gpu": True,
            
            # 界面配置
            "window_width": 1200,
            "window_height": 800,
            "theme": "dark"
        }
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    for key, value in loaded_config.items():
                        if key in self.default_config:
                            self.default_config[key] = value
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.default_config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self.default_config[key] = value
        self.save_config()
    
    def get_all(self):
        """获取所有配置"""
        return self.default_config.copy()

# 全局配置实例
config = Config()

# 会议描述模板
MEETING_INFO_TEMPLATE = """会议时间：[请填写会议时间]
会议地点：[请填写会议地点]
主持人：[请填写主持人姓名]
参会人员：[请填写参会人员名单]
会议议题：[请填写主要议题]
会议背景：[请填写会议背景信息]"""

# 支持的文件格式
SUPPORTED_AUDIO_FORMATS = [
    '.mp3', '.mp4', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'
]

# 状态消息
STATUS_MESSAGES = {
    'uploading': '正在上传音频文件...',
    'converting': '正在转换音频格式...',
    'recognizing': '正在进行语音识别...',
    'generating': '正在生成会议纪要...',
    'saving': '正在保存文件...',
    'completed': '处理完成',
    'error': '处理出错'
} 