#!/usr/bin/env python3
"""
环境检查脚本
用于验证Python环境和依赖项是否正确配置
"""

import sys
import os
from pathlib import Path

def check_python_environment():
    """检查Python环境"""
    print("=" * 60)
    print("Python环境检查")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ 运行在虚拟环境中")
        print(f"虚拟环境路径: {sys.prefix}")
    else:
        print("⚠ 未检测到虚拟环境")
    
    print()

def check_dependencies():
    """检查依赖项"""
    print("=" * 60)
    print("依赖项检查")
    print("=" * 60)
    
    dependencies = [
        ("customtkinter", "GUI框架"),
        ("tkinter", "基础GUI框架"),
        ("ffmpeg", "音频处理"),
        ("pydub", "音频处理"),
        ("requests", "HTTP请求"),
        ("docx", "Word文档处理"),
        ("librosa", "音频分析"),
        ("soundfile", "音频文件处理"),
        ("numpy", "数值计算"),
        ("scipy", "科学计算")
    ]
    
    missing_deps = []
    
    for module_name, description in dependencies:
        try:
            if module_name == "docx":
                from docx import Document
                version = "已安装"
            elif module_name == "ffmpeg":
                import ffmpeg
                version = "已安装"
            else:
                module = __import__(module_name)
                version = getattr(module, '__version__', '已安装')
            
            print(f"✓ {module_name:<15} ({description:<15}) - {version}")
        except ImportError as e:
            print(f"✗ {module_name:<15} ({description:<15}) - 未安装")
            missing_deps.append(module_name)
        except Exception as e:
            print(f"⚠ {module_name:<15} ({description:<15}) - 错误: {e}")
    
    print()
    
    if missing_deps:
        print("缺少的依赖项:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("✓ 所有依赖项都已正确安装")
        return True

def check_project_structure():
    """检查项目结构"""
    print("=" * 60)
    print("项目结构检查")
    print("=" * 60)
    
    required_files = [
        "main.py",
        "gui.py",
        "config.py",
        "requirements.txt",
        "local_env/meeting-minutes-local/python.exe"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)
    
    print()
    
    if missing_files:
        print("缺少的文件:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✓ 项目结构完整")
        return True

def main():
    """主函数"""
    print("会议纪要生成神器（本地保密版）V1.0 - 环境检查")
    print()
    
    # 检查Python环境
    check_python_environment()
    
    # 检查项目结构
    structure_ok = check_project_structure()
    
    # 检查依赖项
    deps_ok = check_dependencies()
    
    print("=" * 60)
    print("检查结果总结")
    print("=" * 60)
    
    if structure_ok and deps_ok:
        print("✓ 环境配置正确，可以正常运行项目")
        print("\n建议:")
        print("1. 在IDE中设置Python解释器为: ./local_env/meeting-minutes-local/python.exe")
        print("2. 使用 run_local.bat 启动项目")
    else:
        print("✗ 环境配置存在问题，请解决上述问题后重试")
    
    print("\n按回车键退出...")
    input()

if __name__ == "__main__":
    main() 