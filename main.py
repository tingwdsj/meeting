"""
会议纪要生成神器（本地保密版）V1.0
主程序入口
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """检查依赖项"""
    missing_deps = []
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        import ffmpeg
    except ImportError:
        missing_deps.append("ffmpeg-python")
    
    try:
        import pydub
    except ImportError:
        missing_deps.append("pydub")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from docx import Document
    except ImportError:
        missing_deps.append("python-docx")
    
    try:
        import librosa
    except ImportError:
        missing_deps.append("librosa")
    
    try:
        import soundfile
    except ImportError:
        missing_deps.append("soundfile")
    
    if missing_deps:
        print("缺少以下依赖项:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_ffmpeg():
    """检查FFmpeg是否可用"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True
    except:
        pass
    
    print("警告: 未检测到FFmpeg，音频处理功能可能受限")
    print("请安装FFmpeg: https://ffmpeg.org/download.html")
    return False

def check_ollama():
    """检查Ollama服务是否可用"""
    try:
        from text_generator import text_generator
        if text_generator.test_connection():
            print("✓ Ollama服务连接正常")
            return True
        else:
            print("✗ 无法连接到Ollama服务")
            print("请确保Ollama正在运行: https://ollama.ai/")
            return False
    except Exception as e:
        print(f"✗ 检查Ollama服务失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("会议纪要生成神器（本地保密版）V1.0")
    print("=" * 60)
    
    # 检查依赖项
    print("\n正在检查依赖项...")
    if not check_dependencies():
        input("\n按回车键退出...")
        return
    
    # 检查FFmpeg
    print("\n正在检查FFmpeg...")
    check_ffmpeg()
    
    # 检查Ollama服务
    print("\n正在检查Ollama服务...")
    ollama_available = check_ollama()
    
    if not ollama_available:
        print("\n注意: 虽然Ollama服务不可用，但您仍可以使用语音识别功能")
        print("生成会议纪要功能需要Ollama服务")
    
    print("\n正在启动应用...")
    
    try:
        # 导入并启动GUI
        from gui import MeetingMinutesApp
        
        app = MeetingMinutesApp()
        app.run()
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保所有依赖项已正确安装")
        input("\n按回车键退出...")
        
    except Exception as e:
        print(f"启动应用失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        input("\n按回车键退出...")

if __name__ == "__main__":
    main() 