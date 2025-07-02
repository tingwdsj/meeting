# meeting-minutes-local
# 会议纪要生成神器（本地保密版）V1.0

## 项目简介
本项目是一款基于本地AI模型的会议纪要生成工具，支持音频文件上传、语音识别、文本编辑与智能纪要生成，所有处理均在本地完成，确保数据安全与隐私。

## 功能亮点
- 🎵 支持多种音频格式（mp3、mp4、wav、m4a等）
- 🎤 本地语音识别（SenseVoiceSmall模型）
- 📝 文本编辑与会议描述管理
- 🧠 智能会议纪要生成（本地LLM，Ollama集成）
- 📄 Word文档导出
- ⚙️ 可视化系统参数配置
- 🔒 完全本地化，数据不出本机

## 技术架构
- 前端：CustomTkinter（现代化GUI）
- 音频处理：FFmpeg + Pydub
- 语音识别：FunAudioLLM/SenseVoiceSmall
- 文本生成：Ollama本地LLM
- 文档生成：python-docx

## 系统要求
- 操作系统：Windows 10/11
- Python：3.8+
- 内存：建议8GB及以上
- 推荐GPU：NVIDIA（支持CUDA）
- 需安装ffmpeg（系统级，详见下文）

## 快速开始

### 1. 安装Anaconda/Miniconda
请先安装 [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)。

### 2. 一键自动化环境搭建（推荐）
在项目根目录下运行：
```bash
python create_local_env.py
```
该脚本将自动：
- 创建本地虚拟环境 `local_env/meeting-minutes-local`
- 安装所有依赖
- 生成启动脚本 `run_local.bat`（Windows）/`run_local.sh`（Linux/Mac）

### 3. 启动程序
- Windows：双击或命令行运行 `run_local.bat`
- Linux/Mac：`./run_local.sh`

### 4. 首次模型下载
- 首次运行会自动下载 SenseVoiceSmall 语音识别模型 和 VAD 语音活动检测模型（speech_fsmn_vad_zh-cn-16k-common-pytorch）
- 两个模型都将被放置在：
  - `local_env/meeting-minutes-local/models/iic/SenseVoiceSmall`
  - `local_env/meeting-minutes-local/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
- 如需手动下载，可运行：
  - `python download_sensevoice_model.py`
  - 或 `install_model.bat`（仅SenseVoiceSmall，推荐用前者）

### 5. 手动环境搭建（可选）
如需手动操作：
```bash
conda create -p ./local_env/meeting-minutes-local python=3.8
conda activate ./local_env/meeting-minutes-local
pip install -r requirements.txt
```

## 依赖说明
- 主要依赖见 `requirements.txt`
- 需系统级安装 ffmpeg：
  - Windows: [下载地址](https://ffmpeg.org/download.html) 或 `choco install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`

## 脚本说明
- `run_local.bat`/`run_local.sh`：本地环境下启动主程序（自动生成，**强烈推荐**）
- `install_model.bat`：SenseVoiceSmall模型下载脚本，推荐用于模型损坏或单独更新时使用
- `install_dependencies.bat`：如需在已存在的本地虚拟环境下单独重装依赖可用（一般无需手动运行）
- `run.bat`：兼容全局环境启动，已加注释，建议仅在特殊情况下使用
- `create_local_env.py`：自动化本地虚拟环境创建与依赖安装，推荐首选
- `download_sensevoice_model.py`：Python方式自动下载并复制 SenseVoiceSmall 和 VAD 语音活动检测模型
- `check_environment.py`：环境和依赖检测

## 使用说明
1. 启动程序后，点击"上传音频文件"选择录音文件
2. 系统自动进行音频处理和语音识别
3. 在"会议描述信息"区域填写会议基本信息
4. 编辑识别生成的文本内容
5. 点击"生成会议纪要"按钮
6. 下载Word格式的会议纪要或完整信息

## 配置说明
- Ollama API地址：`http://127.0.0.1:11434/v1/chat/completions`
- 默认LLM模型：`deepseek-r1:1.5b`
- 音频时长限制：2小时
- 文件大小限制：1GB
- 详细参数可在 `config.json` 或界面中配置

## 数据安全与隐私
- 所有音频、文本、模型均本地处理
- 不上传任何数据到云端
- 适合对数据安全有高要求的用户

## 常见问题FAQ
- **Q: ffmpeg未安装如何处理？**
  - 按上文依赖说明安装ffmpeg
- **Q: 模型下载失败怎么办？**
  - 检查网络，或手动运行 `download_sensevoice_model.py` 或 `install_model.bat`
- **Q: 依赖安装报错如何排查？**
  - 确认已激活本地虚拟环境，或用 `check_environment.py` 检查
- **Q: 如何切换/升级本地LLM模型？**
  - 修改 `config.json` 或界面参数，确保Ollama本地已下载对应模型
- **Q: 脚本报路径错误？**
  - 请确保所有操作均在项目根目录下进行，避免绝对路径问题
- **Q: VAD模型缺失或报错怎么办？**
  - 请运行 `python download_sensevoice_model.py`，确保 `local_env/meeting-minutes-local/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/` 下有 `model.pt` 和 `config.yaml`

## 贡献指南
- 欢迎提交PR和Issue，建议先fork后开发
- 代码风格建议PEP8，提交前请自测
- 有问题请在GitHub Issue区留言

## 许可证
MIT License

## 联系方式
- Issue区留言或邮箱联系（请补充）

## Ollama本地大模型部署说明

本项目依赖本地Ollama服务进行智能纪要生成，所有LLM推理均在本地完成，数据绝不上传云端。

### 1. 安装Ollama
- 访问 [Ollama官网](https://ollama.com/) 下载并安装对应操作系统的Ollama：
  - Windows: 下载安装包并安装
  - Mac: `brew install ollama`
  - Linux: 参考官网说明
- 安装完成后，启动Ollama服务（一般安装后会自动启动）。
- 检查服务是否正常：
  - 打开命令行输入 `ollama --version`，有版本号即安装成功。
  - 访问 http://127.0.0.1:11434/ 能看到Ollama欢迎页面。

### 2. 下载大模型（推荐二选一）
- **高配置机器推荐：deepseek-r1:8b**
  - 适合16GB及以上内存、较新显卡
  - 下载命令：
    ```bash
    ollama run deepseek-r1:8b
    ```
- **低配置机器推荐：deepseek-r1:1.5b**
  - 适合8GB内存及普通显卡/CPU
  - 下载命令：
    ```bash
    ollama run deepseek-r1:1.5b
    ```
- 下载完成后，模型会自动注册到本地Ollama服务。

### 3. 配置本项目使用的模型
- 默认配置在 `config.json` 或界面参数中：
  - `deepseek-r1:1.5b`（低配默认）
  - `deepseek-r1:8b`（高配可手动切换）
- 如需切换模型，只需在配置中修改模型名称并重启程序。

### 4. 常见问题
- Ollama未启动或端口被占用，程序将无法生成纪要，请确保Ollama服务正常运行。
- 模型下载较慢时请耐心等待，建议提前下载。 
