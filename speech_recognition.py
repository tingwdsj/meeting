"""
语音识别模块 - 会议纪要生成神器
"""

import os
from os import path
import torch
import threading
from typing import Optional, Callable, List, Dict, Any, Union
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from config import config

class SpeechRecognizer:
    """语音识别类"""
    
    def __init__(self):
        self.model: Optional[AutoModel] = None
        self.device: str = "cuda" if torch.cuda.is_available() and config.get("use_gpu", True) else "cpu"
        self.is_initialized: bool = False
        self.initialization_lock: threading.Lock = threading.Lock()
        
        # 获取本地环境路径，确保不为None
        self.local_env_path = config.get("local_env_path")
        if not self.local_env_path:
            self.local_env_path = "local_env"
        self.local_env_path = str(self.local_env_path)
        
        # SenseVoiceSmall模型路径
        self.model_dir: str = path.join(str(self.local_env_path), "meeting-minutes-local", "models", "iic", "SenseVoiceSmall")
        
    def initialize_model(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> None:
        """
        初始化语音识别模型
        
        Args:
            progress_callback: 进度回调函数
        """
        if self.is_initialized:
            return
            
        with self.initialization_lock:
            if self.is_initialized:  # 双重检查
                return
                
            try:
                if progress_callback:
                    progress_callback("正在加载语音识别模型...", 0.1)
                
                # 确保模型目录存在
                if not path.exists(self.model_dir):
                    raise Exception(f"模型文件不存在，请先运行 modelscope download --model iic/SenseVoiceSmall")
                
                if progress_callback:
                    progress_callback("正在初始化模型...", 0.3)
                
                # 初始化模型
                vad_dir = os.path.join(str(self.local_env_path), "meeting-minutes-local", "models", "iic", "speech_fsmn_vad_zh-cn-16k-common-pytorch")
                required_files = ["model.pt", "config.yaml"]
                missing_files = [f for f in required_files if not os.path.exists(os.path.join(vad_dir, f))]
                if not os.path.exists(vad_dir) or missing_files:
                    raise Exception(f"本地VAD模型不完整，请检查目录：{vad_dir}，缺失文件: {missing_files}")
                self.model = AutoModel(
                    model=self.model_dir,
                    trust_remote_code=True,
                    remote_code="./model.py",
                    vad_model=vad_dir,
                    vad_kwargs={"max_single_segment_time": 30000},
                    device=f"{self.device}" if self.device == "cpu" else "cuda:0",
                    disable_update=True
                )
                
                if progress_callback:
                    progress_callback("模型加载完成", 1.0)
                
                self.is_initialized = True
                print(f"语音识别模型已加载到设备: {self.device}")
                
            except Exception as e:
                print(f"模型初始化失败: {e}")
                raise Exception(f"语音识别模型初始化失败: {str(e)}")
    
    def recognize_audio(self, audio_path: str, progress_callback: Optional[Callable[[str, float], None]] = None) -> str:
        """
        识别音频文件
        
        Args:
            audio_path: 音频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            识别结果文本
        """
        if not self.is_initialized or self.model is None:
            self.initialize_model(progress_callback)
            if self.model is None:
                raise Exception("模型初始化失败")
        
        try:
            if progress_callback:
                progress_callback("正在识别音频...", 0.5)
            
            # 执行语音识别
            result = self.model.generate(
                input=audio_path,
                cache={},
                language="auto",  # 自动检测语言
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15,
            )
            
            if progress_callback:
                progress_callback("识别完成", 1.0)
            
            # 提取并后处理识别结果
            if result and len(result) > 0:
                text = rich_transcription_postprocess(result[0]["text"])
                return text
            else:
                return ""
                
        except Exception as e:
            print(f"语音识别失败: {e}")
            raise Exception(f"语音识别失败: {str(e)}")
    
    def recognize_audio_batch(self, audio_paths: List[str], progress_callback: Optional[Callable[[str, float], None]] = None) -> List[str]:
        """
        批量识别音频文件
        
        Args:
            audio_paths: 音频文件路径列表
            progress_callback: 进度回调函数
            
        Returns:
            识别结果文本列表
        """
        if not self.is_initialized:
            self.initialize_model(progress_callback)
        
        results = []
        total_files = len(audio_paths)
        
        for i, audio_path in enumerate(audio_paths):
            try:
                if progress_callback:
                    progress = (i / total_files) * 0.8 + 0.1  # 10%-90%
                    progress_callback(f"正在识别第 {i+1}/{total_files} 个文件...", progress)
                
                result = self.recognize_audio(audio_path)
                results.append(result)
                
            except Exception as e:
                print(f"识别文件 {audio_path} 失败: {e}")
                results.append(f"[识别失败: {str(e)}]")
        
        if progress_callback:
            progress_callback("批量识别完成", 1.0)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_name": "iic/SenseVoiceSmall",
            "device": self.device,
            "is_initialized": self.is_initialized,
            "cuda_available": torch.cuda.is_available(),
            "gpu_enabled": config.get("use_gpu", True)
        }
    
    def cleanup(self) -> None:
        """清理模型资源"""
        if self.model is not None:
            try:
                # 释放GPU内存
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                self.model = None
                self.is_initialized = False
                print("语音识别模型已清理")
            except Exception as e:
                print(f"清理模型失败: {e}")

# 全局语音识别器实例
speech_recognizer = SpeechRecognizer() 