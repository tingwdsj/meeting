"""
音频处理模块 - 会议纪要生成神器
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg
from pydub import AudioSegment
import librosa
import soundfile as sf

from config import config, SUPPORTED_AUDIO_FORMATS

class AudioProcessor:
    """音频处理类"""
    
    def __init__(self):
        temp_dir_str = config.get("temp_dir", "temp")
        if temp_dir_str is None:
            temp_dir_str = "temp"
        self.temp_dir = Path(temp_dir_str)
        self.temp_dir.mkdir(exist_ok=True)
        
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        验证音频文件
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 检查文件扩展名
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in SUPPORTED_AUDIO_FORMATS:
            return False, f"不支持的文件格式: {file_ext}"
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        max_size = config.get("max_file_size", 1 * 1024 * 1024 * 1024)
        if max_size is not None and file_size > max_size:
            return False, f"文件过大: {file_size / (1024*1024*1024):.2f}GB > 1GB"
        
        # 检查音频时长
        try:
            duration = self.get_audio_duration(file_path)
            max_duration = config.get("max_audio_duration", 2 * 60 * 60)
            if max_duration is not None and duration > max_duration:
                return False, f"音频时长过长: {duration/3600:.2f}小时 > 2小时"
        except Exception as e:
            return False, f"无法读取音频文件: {str(e)}"
        
        return True, ""
    
    def get_audio_duration(self, file_path: str) -> float:
        """
        获取音频时长
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            音频时长（秒）
        """
        try:
            # 使用ffmpeg获取时长
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            # 备用方法：使用librosa
            try:
                y, sr = librosa.load(file_path, sr=None)
                duration = len(y) / sr
                return duration
            except Exception:
                raise Exception(f"无法获取音频时长: {str(e)}")
    
    def convert_audio(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        转换音频格式
        
        Args:
            input_path: 输入音频文件路径
            output_path: 输出音频文件路径（可选）
            
        Returns:
            转换后的音频文件路径
        """
        if output_path is None:
            output_filename = f"converted_{Path(input_path).stem}.mp3"
            output_path = str(self.temp_dir / output_filename)
        
        try:
            # 使用ffmpeg进行转换
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream, 
                output_path,
                acodec='mp3',
                ar=config.get("audio_sample_rate", 16000),
                ac=config.get("audio_channels", 1),
                ab='128k'
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            return output_path
            
        except Exception as e:
            # 备用方法：使用pydub
            try:
                audio = AudioSegment.from_file(input_path)
                audio = audio.set_frame_rate(config.get("audio_sample_rate", 16000))
                audio = audio.set_channels(config.get("audio_channels", 1))
                audio.export(output_path, format="mp3", bitrate="128k")
                return output_path
            except Exception as pydub_error:
                raise Exception(f"音频转换失败: {str(e)}, 备用方法也失败: {str(pydub_error)}")
    
    def normalize_audio(self, audio_path: str) -> str:
        """
        音频标准化处理
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            标准化后的音频文件路径
        """
        output_path = str(self.temp_dir / f"normalized_{Path(audio_path).name}")
        
        try:
            # 使用ffmpeg进行标准化
            stream = ffmpeg.input(audio_path)
            stream = ffmpeg.filter(stream, 'loudnorm')
            stream = ffmpeg.output(stream, output_path, acodec='mp3')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            return output_path
            
        except Exception as e:
            # 备用方法：使用pydub
            try:
                audio = AudioSegment.from_file(audio_path)
                # 标准化音量
                audio = audio.normalize()
                audio.export(output_path, format="mp3")
                return output_path
            except Exception as pydub_error:
                raise Exception(f"音频标准化失败: {str(e)}, 备用方法也失败: {str(pydub_error)}")
    
    def split_audio(self, audio_path: str, max_duration: int = 300) -> list:
        """
        分割长音频文件
        
        Args:
            audio_path: 音频文件路径
            max_duration: 每段最大时长（秒）
            
        Returns:
            分割后的音频文件路径列表
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_ms = len(audio)
            max_duration_ms = max_duration * 1000
            
            if duration_ms <= max_duration_ms:
                return [audio_path]
            
            segments = []
            for i in range(0, duration_ms, max_duration_ms):
                segment = audio[i:i + max_duration_ms]
                segment_path = str(self.temp_dir / f"segment_{i//max_duration_ms}_{Path(audio_path).name}")
                segment.export(segment_path, format="mp3")
                segments.append(segment_path)
            
            return segments
            
        except Exception as e:
            raise Exception(f"音频分割失败: {str(e)}")
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        获取音频文件信息
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            音频信息字典
        """
        try:
            probe = ffmpeg.probe(file_path)
            format_info = probe['format']
            stream_info = probe['streams'][0] if probe['streams'] else {}
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'sample_rate': int(stream_info.get('sample_rate', 0)),
                'channels': int(stream_info.get('channels', 0)),
                'format': format_info.get('format_name', ''),
                'codec': stream_info.get('codec_name', '')
            }
        except Exception as e:
            raise Exception(f"获取音频信息失败: {str(e)}")

# 全局音频处理器实例
audio_processor = AudioProcessor() 