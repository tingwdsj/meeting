#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Conda环境管理脚本
用于在项目目录下创建和管理conda环境，避免占用C盘空间
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class LocalCondaManager:
    def __init__(self):
        self.project_dir = Path(__file__).parent.absolute()
        self.local_env_dir = self.project_dir / "local_env"
        self.env_name = "meeting-minutes-local"
        self.env_path = self.local_env_dir / self.env_name
        
    def check_conda(self):
        """检查conda是否可用"""
        try:
            result = subprocess.run(["conda", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ 检测到conda: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ 未检测到conda环境")
            print("请先安装Anaconda或Miniconda")
            return False
    
    def create_local_env(self):
        """创建本地conda环境"""
        print(f"\n正在创建本地环境...")
        print(f"项目目录: {self.project_dir}")
        print(f"环境目录: {self.local_env_dir}")
        print(f"环境名称: {self.env_name}")
        
        # 创建本地环境目录
        self.local_env_dir.mkdir(exist_ok=True)
        
        # 检查是否已存在环境
        if self.env_path.exists():
            print(f"\n检测到已存在的本地环境: {self.env_path}")
            choice = input("是否删除现有环境并重新创建? (y/n): ").lower()
            if choice == 'y':
                print("正在删除现有环境...")
                shutil.rmtree(self.env_path)
            else:
                print("跳过环境创建")
                return True
        
        # 创建新环境 - 只使用--prefix参数，不使用-n参数
        print(f"\n正在创建conda环境...")
        cmd = [
            "conda", "create", 
            "python=3.8", 
            "-y", 
            "--prefix", str(self.env_path)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✓ 本地环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 创建环境失败: {e}")
            return False
    
    def install_dependencies(self):
        """安装项目依赖"""
        print(f"\n正在安装项目依赖...")
        
        # 激活环境并安装依赖
        requirements_file = self.project_dir / "requirements.txt"
        if not requirements_file.exists():
            print("✗ 未找到requirements.txt文件")
            return False
        
        # 使用conda run在指定环境中运行pip install
        cmd = [
            "conda", "run", 
            "-p", str(self.env_path),
            "pip", "install", "-r", str(requirements_file)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✓ 依赖安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 依赖安装失败: {e}")
            return False
    
    def create_launch_scripts(self):
        """创建启动脚本"""
        print(f"\n正在创建启动脚本...")
        
        # Windows批处理脚本
        bat_content = f'''@echo off
chcp 65001
echo ========================================
echo 会议纪要生成神器（本地保密版）V1.0
echo 本地环境启动脚本
echo ========================================
echo.

echo 正在激活本地conda环境...
call conda activate "{self.env_path}"
if errorlevel 1 (
    echo 激活环境失败，尝试使用conda run
    goto :run_with_conda_run
)

echo.
echo 正在启动应用...
python main.py
goto :end

:run_with_conda_run
echo 使用conda run启动应用...
conda run -p "{self.env_path}" python main.py

:end
if errorlevel 1 (
    echo.
    echo 应用运行出错
    echo 请检查错误信息并解决问题
    pause
)
'''
        
        with open(self.project_dir / "run_local.bat", "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        # Linux/macOS shell脚本
        sh_content = f'''#!/bin/bash
echo "========================================"
echo "会议纪要生成神器（本地保密版）V1.0"
echo "本地环境启动脚本"
echo "========================================"
echo

echo "正在激活本地conda环境..."
source "{self.env_path}/bin/activate"
if [ $? -ne 0 ]; then
    echo "激活环境失败，尝试使用conda run"
    conda run -p "{self.env_path}" python main.py
else
    echo "正在启动应用..."
    python main.py
fi
'''
        
        sh_script_path = self.project_dir / "run_local.sh"
        with open(sh_script_path, "w", encoding="utf-8") as f:
            f.write(sh_content)
        
        # 设置执行权限（Linux/macOS）
        if sys.platform != "win32":
            os.chmod(sh_script_path, 0o755)
        
        print("✓ 启动脚本创建成功:")
        print(f"  - Windows: run_local.bat")
        print(f"  - Linux/macOS: run_local.sh")
    
    def update_gitignore(self):
        """更新.gitignore文件"""
        gitignore_path = self.project_dir / ".gitignore"
        
        if not gitignore_path.exists():
            # 创建新的.gitignore文件
            content = """# Python
__pycache__/
*.py[cod]
*$py.class

# Local environment
local_env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary files
temp/
*.tmp
*.log
"""
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("✓ 创建.gitignore文件")
        else:
            # 检查是否已包含local_env
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "local_env/" not in content:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n# Local environment\nlocal_env/\n")
                print("✓ 已添加local_env/到.gitignore")
            else:
                print("✓ .gitignore已包含local_env/")
    
    def show_usage_info(self):
        """显示使用信息"""
        print(f"\n" + "="*50)
        print("迁移完成！")
        print("="*50)
        print(f"\n环境信息:")
        print(f"  - 环境名称: {self.env_name}")
        print(f"  - 环境路径: {self.env_path}")
        print(f"  - 启动脚本: run_local.bat (Windows) / run_local.sh (Linux/macOS)")
        
        print(f"\n使用方法:")
        print(f"  1. 运行启动脚本:")
        if sys.platform == "win32":
            print(f"     run_local.bat")
        else:
            print(f"     ./run_local.sh")
        
        print(f"  2. 或手动激活环境:")
        print(f"     conda activate \"{self.env_path}\"")
        print(f"     python main.py")
        
        print(f"  3. 或使用conda run:")
        print(f"     conda run -p \"{self.env_path}\" python main.py")
        
        print(f"\n注意事项:")
        print(f"  - 本地环境已保存在项目目录下，不会占用C盘空间")
        print(f"  - 如需删除环境，可删除 local_env 文件夹")
        print(f"  - 建议将 local_env 添加到版本控制忽略列表")
        print(f"  - 环境大小约占用 {self.get_env_size():.1f} MB")
    
    def get_env_size(self):
        """获取环境大小（MB）"""
        if not self.env_path.exists():
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.env_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def run(self):
        """运行完整的迁移流程"""
        print("会议纪要生成神器 - Conda环境迁移工具")
        print("="*50)
        
        if not self.check_conda():
            return False
        
        if not self.create_local_env():
            return False
        
        if not self.install_dependencies():
            return False
        
        self.create_launch_scripts()
        self.update_gitignore()
        self.show_usage_info()
        
        return True

def main():
    manager = LocalCondaManager()
    success = manager.run()
    
    if success:
        print(f"\n✓ 环境迁移成功完成！")
    else:
        print(f"\n✗ 环境迁移失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main() 