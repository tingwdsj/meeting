"""
GUI界面模块 - 会议纪要生成神器
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import os
from pathlib import Path
from typing import Optional

from config import config, MEETING_INFO_TEMPLATE, STATUS_MESSAGES
from audio_processor import audio_processor
from speech_recognition import speech_recognizer  # 修改：使用真正的语音识别器
from text_generator import text_generator
from document_generator import document_generator

# 设置CustomTkinter主题
ctk.set_appearance_mode(config.get("theme") or "dark")
ctk.set_default_color_theme("blue")

def show_topmost_message(parent, message_type, title, message):
    """显示置顶消息框"""
    # 创建临时顶层窗口
    temp_window = tk.Toplevel(parent)
    temp_window.withdraw()  # 先隐藏窗口
    
    # 设置窗口属性
    temp_window.title(title)
    temp_window.transient(parent)  # 设置为主窗口的临时窗口
    temp_window.grab_set()  # 模态窗口
    temp_window.attributes('-topmost', True)  # 始终置顶
    temp_window.focus_set()  # 获取焦点
    
    # 根据消息类型显示不同的消息框
    if message_type == "info":
        result = messagebox.showinfo(title, message, parent=temp_window)
    elif message_type == "warning":
        result = messagebox.showwarning(title, message, parent=temp_window)
    elif message_type == "error":
        result = messagebox.showerror(title, message, parent=temp_window)
    else:
        result = messagebox.showinfo(title, message, parent=temp_window)
    
    # 关闭临时窗口
    temp_window.destroy()
    return result

class MeetingMinutesApp:
    """会议纪要生成应用主类"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        self.setup_variables()
        
        # 应用状态 - 在setup_ui之前初始化
        self.audio_file_path = None
        self.transcription_text = ""
        self.meeting_info_text = MEETING_INFO_TEMPLATE
        self.minutes_text = ""
        self.is_recognizing = False  # 添加识别状态标志
        
        self.setup_ui()
        self.setup_bindings()
        
        # 初始化表格式界面数据
        self.initialize_meeting_info_fields()
        
    def setup_window(self):
        """设置窗口"""
        self.root.title("会议纪要生成神器（本地保密版）V1.0")
        # 设置全屏显示
        self.root.state('zoomed')  # Windows全屏
        self.root.minsize(1000, 600)
        
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
    
    def setup_variables(self):
        """设置变量"""
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        
    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame, 
            text="会议纪要生成神器（本地保密版）V1.0",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # 文件上传区域
        self.setup_file_upload_area(main_frame)
        
        # 进度条
        self.setup_progress_area(main_frame)
        
        # 主内容区域 - 使用PanedWindow实现可调节宽度
        self.content_paned = tk.PanedWindow(main_frame, orient="horizontal", sashwidth=12, sashrelief="groove")
        self.content_paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 获取屏幕宽度并三等分
        screen_width = self.root.winfo_screenwidth()
        panel_width = screen_width // 3
        
        # 创建三个主要区域
        self.setup_meeting_info_area(self.content_paned, panel_width)
        self.setup_transcription_area(self.content_paned, panel_width)
        self.setup_minutes_area(self.content_paned, panel_width)
        
        # 按钮区域
        self.setup_button_area(main_frame)
        
        # 强制按1:1:1比例分配
        self.root.update_idletasks()  # 确保窗口已布局
        total_width = self.content_paned.winfo_width()
        if total_width < 100:  # 防止初始宽度太小
            total_width = self.root.winfo_screenwidth() - 40  # 适当减去边距
        width_each = total_width // 3
        panes = self.content_paned.panes()
        if len(panes) == 3:
            self.content_paned.paneconfig(panes[0], width=width_each)
            self.content_paned.paneconfig(panes[1], width=width_each)
            self.content_paned.paneconfig(panes[2], width=width_each)
        
    def setup_file_upload_area(self, parent):
        """设置文件上传区域"""
        upload_frame = ctk.CTkFrame(parent)
        upload_frame.pack(fill="x", padx=10, pady=5)
        
        # 文件路径显示
        self.file_path_var = tk.StringVar(value="未选择文件")
        file_label = ctk.CTkLabel(upload_frame, textvariable=self.file_path_var, font=ctk.CTkFont(size=12))
        file_label.pack(side="left", padx=10, pady=10)
        
        # 文件限制提示
        max_file_size = config.get("max_file_size", 1 * 1024 * 1024 * 1024) or 1 * 1024 * 1024 * 1024
        max_audio_duration = config.get("max_audio_duration", 2 * 60 * 60) or 2 * 60 * 60
        
        limit_text = f"支持格式：mp3/mp4/wav/m4a/flac/aac/ogg/wma/avi/mov/mkv/webm/wmv/mpeg/mpg/3gp/ts/flv/f4v/m4v | 大小限制：{max_file_size // (1024*1024*1024)}GB | 时长限制：{max_audio_duration // 3600}小时"
        limit_label = ctk.CTkLabel(
            upload_frame, 
            text=limit_text, 
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        limit_label.pack(side="left", padx=(20, 10), pady=10)
        
        # 上传按钮
        upload_btn = ctk.CTkButton(
            upload_frame, 
            text="上传音频文件", 
            command=self.upload_audio_file,
            width=120
        )
        upload_btn.pack(side="right", padx=10, pady=10)
        
        # 清除按钮
        clear_btn = ctk.CTkButton(
            upload_frame, 
            text="清除", 
            command=self.clear_audio_file,
            width=80,
            fg_color="red"
        )
        clear_btn.pack(side="right", padx=5, pady=10)
        
    def setup_progress_area(self, parent):
        """设置进度显示区域"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        # 状态标签
        status_label = ctk.CTkLabel(progress_frame, textvariable=self.status_var, font=ctk.CTkFont(size=12))
        status_label.pack(side="left", padx=10, pady=5)
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(side="right", padx=10, pady=5, fill="x", expand=True)
        self.progress_bar.set(0)
        
    def setup_meeting_info_area(self, parent, width):
        """设置会议描述信息区域 - 表格式显示"""
        info_frame = ctk.CTkFrame(parent)
        parent.add(info_frame, width=width)
        
        # 标题
        info_title = ctk.CTkLabel(info_frame, text="会议描述信息", font=ctk.CTkFont(size=16, weight="bold"))
        info_title.pack(pady=5)
        
        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(info_frame, height=300)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 会议基本信息表格
        self.setup_meeting_basic_info(scroll_frame)
        
        # 会议详细信息的文本区域
        self.setup_meeting_detail_info(scroll_frame)
        
        # 按钮区域
        info_btn_frame = ctk.CTkFrame(info_frame)
        info_btn_frame.pack(fill="x", padx=10, pady=5)
        
        save_info_btn = ctk.CTkButton(
            info_btn_frame, 
            text="保存", 
            command=self.save_meeting_info,
            width=80
        )
        save_info_btn.pack(side="left", padx=5)
        
        reset_info_btn = ctk.CTkButton(
            info_btn_frame, 
            text="重置", 
            command=self.reset_meeting_info,
            width=80
        )
        reset_info_btn.pack(side="left", padx=5)
        
        # 添加格式化按钮
        format_info_btn = ctk.CTkButton(
            info_btn_frame, 
            text="格式化", 
            command=self.format_meeting_info,
            width=80
        )
        format_info_btn.pack(side="left", padx=5)
    
    def setup_meeting_basic_info(self, parent):
        """设置会议基本信息表格"""
        # 基本信息标题
        basic_title = ctk.CTkLabel(parent, text="会议基本信息", font=ctk.CTkFont(size=14, weight="bold"))
        basic_title.pack(pady=(0, 10), anchor="w")
        
        # 创建表格样式的输入框
        self.meeting_info_fields = {}
        
        # 定义字段配置
        fields_config = [
            ("meeting_time", "会议时间", "请填写会议时间（如：2024年1月15日 14:00-16:00）"),
            ("meeting_location", "会议地点", "请填写会议地点（如：会议室A、线上会议等）"),
            ("host", "主持人", "请填写主持人姓名"),
            ("participants", "参会人员", "请填写参会人员名单（用逗号分隔）"),
            ("meeting_type", "会议类型", "请填写会议类型（如：项目讨论、决策会议等）"),
            ("meeting_status", "会议状态", "请填写会议状态（如：已结束、进行中等）")
        ]
        
        # 创建表格行
        for i, (field_key, field_label, placeholder) in enumerate(fields_config):
            # 创建行框架
            row_frame = ctk.CTkFrame(parent)
            row_frame.pack(fill="x", pady=2)
            
            # 标签
            label = ctk.CTkLabel(row_frame, text=f"{field_label}:", width=100, anchor="w")
            label.pack(side="left", padx=(10, 5), pady=5)
            
            # 输入框
            if field_key == "participants":
                # 参会人员使用更大的输入框
                entry = ctk.CTkEntry(row_frame, placeholder_text=placeholder, height=30)
                entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
            else:
                entry = ctk.CTkEntry(row_frame, placeholder_text=placeholder, height=30)
                entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
            
            # 存储字段引用
            self.meeting_info_fields[field_key] = entry
    
    def setup_meeting_detail_info(self, parent):
        """设置会议详细信息"""
        # 详细信息标题
        detail_title = ctk.CTkLabel(parent, text="会议详细信息", font=ctk.CTkFont(size=14, weight="bold"))
        detail_title.pack(pady=(20, 10), anchor="w")
        
        # 议题标签
        topics_label = ctk.CTkLabel(parent, text="会议议题:", anchor="w")
        topics_label.pack(anchor="w", padx=10)
        
        # 议题输入框
        self.topics_textbox = ctk.CTkTextbox(parent, height=60)
        self.topics_textbox.pack(fill="x", padx=10, pady=(0, 10))
        self.topics_textbox.insert("1.0", "请填写主要议题（每行一个议题）")
        
        # 背景标签
        background_label = ctk.CTkLabel(parent, text="会议背景:", anchor="w")
        background_label.pack(anchor="w", padx=10)
        
        # 背景输入框
        self.background_textbox = ctk.CTkTextbox(parent, height=80)
        self.background_textbox.pack(fill="x", padx=10, pady=(0, 10))
        self.background_textbox.insert("1.0", "请填写会议背景信息")
        
        # 备注标签
        notes_label = ctk.CTkLabel(parent, text="备注:", anchor="w")
        notes_label.pack(anchor="w", padx=10)
        
        # 备注输入框
        self.notes_textbox = ctk.CTkTextbox(parent, height=60)
        self.notes_textbox.pack(fill="x", padx=10, pady=(0, 10))
        self.notes_textbox.insert("1.0", "请填写其他备注信息")
    
    def setup_transcription_area(self, parent, width):
        """设置识别文本区域"""
        trans_frame = ctk.CTkFrame(parent)
        parent.add(trans_frame, width=width)
        
        # 标题
        trans_title = ctk.CTkLabel(trans_frame, text="识别生成文本", font=ctk.CTkFont(size=16, weight="bold"))
        trans_title.pack(pady=5)
        
        # 文本区域
        self.transcription_textbox = ctk.CTkTextbox(trans_frame, height=200)
        self.transcription_textbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 按钮区域
        trans_btn_frame = ctk.CTkFrame(trans_frame)
        trans_btn_frame.pack(fill="x", padx=10, pady=5)
        
        save_trans_btn = ctk.CTkButton(
            trans_btn_frame, 
            text="保存", 
            command=self.save_transcription,
            width=80
        )
        save_trans_btn.pack(side="left", padx=5)
        
        recognize_btn = ctk.CTkButton(
            trans_btn_frame, 
            text="开始识别", 
            command=self.recognize_audio,
            width=80
        )
        recognize_btn.pack(side="left", padx=5)
        
    def setup_minutes_area(self, parent, width):
        """设置会议纪要区域"""
        minutes_frame = ctk.CTkFrame(parent)
        parent.add(minutes_frame, width=width)
        
        # 标题
        minutes_title = ctk.CTkLabel(minutes_frame, text="会议纪要", font=ctk.CTkFont(size=16, weight="bold"))
        minutes_title.pack(pady=5)
        
        # 文本区域
        self.minutes_textbox = ctk.CTkTextbox(minutes_frame, height=200)
        self.minutes_textbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 按钮区域
        minutes_btn_frame = ctk.CTkFrame(minutes_frame)
        minutes_btn_frame.pack(fill="x", padx=10, pady=5)
        
        save_minutes_btn = ctk.CTkButton(
            minutes_btn_frame, 
            text="保存", 
            command=self.save_minutes,
            width=80
        )
        save_minutes_btn.pack(side="left", padx=5)
        
        generate_btn = ctk.CTkButton(
            minutes_btn_frame, 
            text="生成纪要", 
            command=self.generate_minutes,
            width=80
        )
        generate_btn.pack(side="left", padx=5)
        
    def setup_button_area(self, parent):
        """设置按钮区域"""
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 下载按钮
        download_minutes_btn = ctk.CTkButton(
            button_frame, 
            text="下载会议纪要", 
            command=self.download_minutes,
            width=150,
            height=40
        )
        download_minutes_btn.pack(side="left", padx=10, pady=10)
        
        download_complete_btn = ctk.CTkButton(
            button_frame, 
            text="下载完整信息", 
            command=self.download_complete_info,
            width=150,
            height=40
        )
        download_complete_btn.pack(side="left", padx=10, pady=10)
        
        # 查看日志按钮
        view_logs_btn = ctk.CTkButton(
            button_frame, 
            text="查看日志", 
            command=self.open_log_viewer,
            width=120,
            height=40,
            fg_color="orange"
        )
        view_logs_btn.pack(side="left", padx=10, pady=10)
        
        # 配置按钮
        config_btn = ctk.CTkButton(
            button_frame, 
            text="系统配置", 
            command=self.open_config_window,
            width=120,
            height=40
        )
        config_btn.pack(side="right", padx=10, pady=10)
        
    def setup_bindings(self):
        """设置事件绑定"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def upload_audio_file(self):
        """上传音频文件"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择音频文件",
                filetypes=[
                    ("音频文件", "*.mp3 *.mp4 *.wav *.m4a *.flac *.aac *.ogg *.wma"),
                    ("所有文件", "*.*")
                ]
            )
            
            if file_path:
                # 验证文件
                if not os.path.exists(file_path):
                    error_msg = "文件不存在"
                    show_topmost_message(self.root, "error", "文件错误", error_msg)
                    return
                
                # 使用audio_processor进行完整验证（包括文件大小和音频时长）
                is_valid, error_msg = audio_processor.validate_audio_file(file_path)
                
                if not is_valid:
                    show_topmost_message(self.root, "error", "文件错误", error_msg)
                    return
                
                # 新增：判断是否为视频格式，自动转码为mp3
                file_ext = os.path.splitext(file_path)[1].lower()
                video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.mpeg', '.mpg', '.3gp', '.ts', '.flv', '.f4v', '.m4v']
                if file_ext in video_exts:
                    try:
                        audio_path = audio_processor.convert_audio(file_path)
                        self.audio_file_path = audio_path
                        self.file_path_var.set(os.path.basename(audio_path) + "（已转码）")
                        self.status_var.set("视频已转音频，准备识别")
                        self._is_temp_audio = True  # 标记为临时音频
                    except Exception as e:
                        show_topmost_message(self.root, "error", "转码失败", f"视频转音频失败: {str(e)}")
                        return
                else:
                    self.audio_file_path = file_path
                    self.file_path_var.set(os.path.basename(file_path))
                    self.status_var.set("文件已上传")
                    self._is_temp_audio = False  # 非临时音频
                
                # 自动开始语音识别
                self.recognize_audio()
                
        except Exception as e:
            error_msg = f"上传文件失败: {str(e)}"
            show_topmost_message(self.root, "error", "文件错误", error_msg)
    
    def clear_audio_file(self):
        """清除音频文件"""
        # 如果是临时转码音频，自动删除
        if hasattr(self, '_is_temp_audio') and self._is_temp_audio and self.audio_file_path:
            try:
                if os.path.exists(self.audio_file_path):
                    os.remove(self.audio_file_path)
            except Exception as e:
                print(f"删除临时音频文件失败: {e}")
        self.audio_file_path = None
        self.file_path_var.set("未选择文件")
        self.status_var.set("就绪")
    
    def recognize_audio(self):
        """识别音频"""
        if not self.audio_file_path:
            show_topmost_message(self.root, "warning", "警告", "请先上传音频文件")
            return
        
        # 防止重复调用
        if self.is_recognizing:
            show_topmost_message(self.root, "warning", "警告", "语音识别正在进行中，请稍候...")
            return
        
        # 在新线程中识别音频
        thread = threading.Thread(target=self._recognize_audio_thread)
        thread.daemon = True
        thread.start()
    
    def _recognize_audio_thread(self):
        """识别音频线程"""
        try:
            # 设置识别状态
            self.is_recognizing = True
            self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['recognizing']))
            self.root.after(0, lambda: self.progress_bar.set(0.1))
            
            def progress_callback(message, progress):
                self.root.after(0, lambda: self.status_var.set(message))
                self.root.after(0, lambda: self.progress_bar.set(0.1 + progress * 0.8))
            
            # 进行语音识别
            if self.audio_file_path:  # 确保文件路径不为None
                transcription = speech_recognizer.recognize_audio(
                    self.audio_file_path, 
                    progress_callback=progress_callback
                )
                
                # 更新界面
                self.root.after(0, lambda: self.transcription_textbox.delete("1.0", "end"))
                self.root.after(0, lambda: self.transcription_textbox.insert("1.0", transcription))
                self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['completed']))
                self.root.after(0, lambda: self.progress_bar.set(1.0))
                
                self.transcription_text = transcription
            
                # 识别完成后自动删除临时音频文件（如果有）
                if hasattr(self, '_is_temp_audio') and self._is_temp_audio and self.audio_file_path:
                    try:
                        if os.path.exists(self.audio_file_path):
                            os.remove(self.audio_file_path)
                    except Exception as e:
                        print(f"删除临时音频文件失败: {e}")
                    self.audio_file_path = None
                    self.file_path_var.set("未选择文件")
                    self.status_var.set("就绪")
            
        except Exception as e:
            error_msg = f"语音识别失败: {str(e)}"
            self.root.after(0, lambda: show_topmost_message(self.root, "error", "错误", error_msg))
            self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['error']))
            self.root.after(0, lambda: self.progress_bar.set(0))
        finally:
            # 重置识别状态
            self.is_recognizing = False
    
    def generate_minutes(self):
        """生成会议纪要"""
        if not self.transcription_text.strip():
            show_topmost_message(self.root, "warning", "警告", "请先进行语音识别")
            return
        
        # 获取当前文本
        meeting_info = self.get_formatted_meeting_info()
        transcription = self.transcription_textbox.get("1.0", "end-1c")
        
        if not meeting_info.strip() or not transcription.strip():
            show_topmost_message(self.root, "warning", "警告", "请填写会议描述信息和识别文本")
            return
        
        # 在新线程中生成纪要
        thread = threading.Thread(target=self._generate_minutes_thread, args=(meeting_info, transcription))
        thread.daemon = True
        thread.start()
    
    def _generate_minutes_thread(self, meeting_info: str, transcription: str):
        """生成会议纪要线程"""
        try:
            self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['generating']))
            self.root.after(0, lambda: self.progress_bar.set(0.1))
            
            def progress_callback(message, progress):
                self.root.after(0, lambda: self.status_var.set(message))
                self.root.after(0, lambda: self.progress_bar.set(0.1 + progress * 0.8))
            
            # 生成会议纪要
            minutes = text_generator.generate_text(
                transcription, 
                meeting_info, 
                progress_callback=progress_callback
            )
            
            # 更新界面
            self.root.after(0, lambda: self.minutes_textbox.delete("1.0", "end"))
            self.root.after(0, lambda: self.minutes_textbox.insert("1.0", minutes))
            self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['completed']))
            self.root.after(0, lambda: self.progress_bar.set(1.0))
            
            self.minutes_text = minutes
            
        except Exception as e:
            error_msg = f"生成会议纪要失败: {str(e)}"
            self.root.after(0, lambda: show_topmost_message(self.root, "error", "错误", error_msg))
            self.root.after(0, lambda: self.status_var.set(STATUS_MESSAGES['error']))
            self.root.after(0, lambda: self.progress_bar.set(0))
    
    def save_meeting_info(self):
        """保存会议描述信息"""
        self.meeting_info_text = self.get_formatted_meeting_info()
        show_topmost_message(self.root, "info", "提示", "会议描述信息已保存")
    
    def reset_meeting_info(self):
        """重置会议描述信息"""
        # 清空所有字段
        for field in self.meeting_info_fields.values():
            field.delete(0, "end")
        
        # 清空文本区域
        self.topics_textbox.delete("1.0", "end")
        self.background_textbox.delete("1.0", "end")
        self.notes_textbox.delete("1.0", "end")
    
    def format_meeting_info(self):
        """格式化会议信息"""
        formatted_text = self.get_formatted_meeting_info()
        show_topmost_message(self.root, "info", "格式化结果", f"格式化后的会议信息：\n\n{formatted_text}")
    
    def get_formatted_meeting_info(self):
        """获取格式化的会议信息"""
        # 获取基本信息
        meeting_time = self.meeting_info_fields["meeting_time"].get().strip()
        meeting_location = self.meeting_info_fields["meeting_location"].get().strip()
        host = self.meeting_info_fields["host"].get().strip()
        participants = self.meeting_info_fields["participants"].get().strip()
        meeting_type = self.meeting_info_fields["meeting_type"].get().strip()
        meeting_status = self.meeting_info_fields["meeting_status"].get().strip()
        
        # 获取详细信息
        topics = self.topics_textbox.get("1.0", "end-1c").strip()
        background = self.background_textbox.get("1.0", "end-1c").strip()
        notes = self.notes_textbox.get("1.0", "end-1c").strip()
        
        # 构建格式化文本
        formatted_text = f"""会议时间：{meeting_time if meeting_time else '[请填写会议时间]'}
会议地点：{meeting_location if meeting_location else '[请填写会议地点]'}
主持人：{host if host else '[请填写主持人姓名]'}
参会人员：{participants if participants else '[请填写参会人员名单]'}
会议类型：{meeting_type if meeting_type else '[请填写会议类型]'}
会议状态：{meeting_status if meeting_status else '[请填写会议状态]'}
会议议题：{topics if topics else '[请填写主要议题]'}
会议背景：{background if background else '[请填写会议背景信息]'}
备注：{notes if notes else '[请填写其他备注信息]'}"""
        
        return formatted_text
    
    def initialize_meeting_info_fields(self):
        """初始化会议信息字段"""
        try:
            # 解析模板数据
            lines = self.meeting_info_text.split('\n')
            field_data = {}
            
            for line in lines:
                line = line.strip()
                if '：' in line:
                    key, value = line.split('：', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 映射字段名
                    if key == "会议时间":
                        field_data["meeting_time"] = value.replace('[请填写会议时间]', '')
                    elif key == "会议地点":
                        field_data["meeting_location"] = value.replace('[请填写会议地点]', '')
                    elif key == "主持人":
                        field_data["host"] = value.replace('[请填写主持人姓名]', '')
                    elif key == "参会人员":
                        field_data["participants"] = value.replace('[请填写参会人员名单]', '')
                    elif key == "会议议题":
                        field_data["topics"] = value.replace('[请填写主要议题]', '')
                    elif key == "会议背景":
                        field_data["background"] = value.replace('[请填写会议背景信息]', '')
            
            # 填充字段
            for field_key, field_value in field_data.items():
                if field_key in self.meeting_info_fields:
                    self.meeting_info_fields[field_key].insert(0, field_value)
                elif field_key == "topics" and hasattr(self, 'topics_textbox'):
                    self.topics_textbox.insert("1.0", field_value)
                elif field_key == "background" and hasattr(self, 'background_textbox'):
                    self.background_textbox.insert("1.0", field_value)
                    
        except Exception as e:
            print(f"初始化会议信息字段失败: {e}")
            # 如果解析失败，保持默认状态
            pass
    
    def save_transcription(self):
        """保存识别文本"""
        self.transcription_text = self.transcription_textbox.get("1.0", "end-1c")
        show_topmost_message(self.root, "info", "提示", "识别文本已保存")
    
    def save_minutes(self):
        """保存会议纪要"""
        self.minutes_text = self.minutes_textbox.get("1.0", "end-1c")
        show_topmost_message(self.root, "info", "提示", "会议纪要已保存")
    
    def download_minutes(self):
        """下载会议纪要"""
        if not self.minutes_text.strip():
            show_topmost_message(self.root, "warning", "警告", "请先生成会议纪要")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存会议纪要",
                defaultextension=".docx",
                filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                self.status_var.set(STATUS_MESSAGES['saving'])
                self.progress_bar.set(0.5)
                
                # 生成文档
                meeting_info = self.get_formatted_meeting_info()
                transcription = self.transcription_textbox.get("1.0", "end-1c")
                minutes = self.minutes_textbox.get("1.0", "end-1c")
                
                document_generator.create_meeting_minutes_doc(
                    meeting_info, transcription, minutes, file_path
                )
                
                self.status_var.set(STATUS_MESSAGES['completed'])
                self.progress_bar.set(1.0)
                show_topmost_message(self.root, "info", "成功", f"会议纪要已保存到: {file_path}")
                
        except Exception as e:
            show_topmost_message(self.root, "error", "错误", f"保存失败: {str(e)}")
            self.status_var.set(STATUS_MESSAGES['error'])
            self.progress_bar.set(0)
    
    def download_complete_info(self):
        """下载完整信息"""
        if not self.transcription_text.strip():
            show_topmost_message(self.root, "warning", "警告", "请先进行语音识别")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存会议完整信息",
                defaultextension=".docx",
                filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                self.status_var.set(STATUS_MESSAGES['saving'])
                self.progress_bar.set(0.5)
                
                # 生成文档
                meeting_info = self.get_formatted_meeting_info()
                transcription = self.transcription_textbox.get("1.0", "end-1c")
                minutes = self.minutes_textbox.get("1.0", "end-1c")
                
                document_generator.create_complete_info_doc(
                    meeting_info, transcription, minutes, file_path
                )
                
                self.status_var.set(STATUS_MESSAGES['completed'])
                self.progress_bar.set(1.0)
                show_topmost_message(self.root, "info", "成功", f"会议完整信息已保存到: {file_path}")
                
        except Exception as e:
            show_topmost_message(self.root, "error", "错误", f"保存失败: {str(e)}")
            self.status_var.set(STATUS_MESSAGES['error'])
            self.progress_bar.set(0)
    
    def open_config_window(self):
        """打开配置窗口"""
        config_window = ConfigWindow(self.root)
        
    def open_log_viewer(self):
        """打开日志查看器"""
        try:
            from log_viewer import LogViewer
            import tkinter as tk
            
            # 创建新窗口
            log_window = tk.Toplevel(self.root)
            log_viewer = LogViewer(log_window)
            
            # 设置窗口属性
            log_window.title("对话日志查看器 - 会议纪要生成神器")
            log_window.geometry("1200x800")
            log_window.transient(self.root)  # 设置为主窗口的临时窗口
            log_window.grab_set()  # 模态窗口
            log_window.attributes('-topmost', True)  # 始终置顶
            
        except ImportError as e:
            show_topmost_message(self.root, "error", "错误", f"无法导入日志查看器模块: {str(e)}")
        except Exception as e:
            show_topmost_message(self.root, "error", "错误", f"打开日志查看器失败: {str(e)}")
        
    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 清理临时文件
            audio_processor.cleanup_temp_files()
        except:
            pass
        
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


class ConfigWindow:
    """配置窗口"""
    
    def __init__(self, parent):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("系统配置")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.transient(parent)  # 设置为主窗口的临时窗口
        self.window.grab_set()         # 模态，阻止主窗口操作
        self.window.attributes('-topmost', True)  # 始终置顶
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        """设置界面"""
        # Ollama配置
        ollama_frame = ctk.CTkFrame(self.window)
        ollama_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(ollama_frame, text="Ollama配置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # API地址
        ctk.CTkLabel(ollama_frame, text="API地址:").pack(anchor="w", padx=10)
        self.api_url_entry = ctk.CTkEntry(ollama_frame, width=400)
        self.api_url_entry.pack(padx=10, pady=5)
        
        # 模型名称
        ctk.CTkLabel(ollama_frame, text="模型名称:").pack(anchor="w", padx=10)
        self.model_entry = ctk.CTkEntry(ollama_frame, width=400)
        self.model_entry.pack(padx=10, pady=5)
        
        # 提示词配置
        prompt_frame = ctk.CTkFrame(self.window)
        prompt_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(prompt_frame, text="提示词配置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.prompt_textbox = ctk.CTkTextbox(prompt_frame, height=200)
        self.prompt_textbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 按钮
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(button_frame, text="保存", command=self.save_config).pack(side="right", padx=10)
        ctk.CTkButton(button_frame, text="取消", command=self.window.destroy).pack(side="right", padx=10)
        ctk.CTkButton(button_frame, text="测试连接", command=self.test_connection).pack(side="left", padx=10)
    
    def load_config(self):
        """加载配置"""
        config_data = text_generator.get_config()
        self.api_url_entry.insert(0, config_data["api_url"])
        self.model_entry.insert(0, config_data["model_name"])
        self.prompt_textbox.insert("1.0", config_data["default_prompt"])
    
    def save_config(self):
        """保存配置"""
        try:
            api_url = self.api_url_entry.get()
            model_name = self.model_entry.get()
            prompt = self.prompt_textbox.get("1.0", "end-1c")
            
            text_generator.update_config(api_url, model_name, prompt)
            show_topmost_message(self.window, "info", "成功", "配置已保存")
            self.window.destroy()
            
        except Exception as e:
            show_topmost_message(self.window, "error", "错误", f"保存配置失败: {str(e)}")
    
    def test_connection(self):
        """测试连接"""
        try:
            api_url = self.api_url_entry.get()
            text_generator.api_url = api_url
            
            if text_generator.test_connection():
                show_topmost_message(self.window, "info", "成功", "Ollama连接正常")
            else:
                show_topmost_message(self.window, "error", "失败", "无法连接到Ollama服务")
                
        except Exception as e:
            show_topmost_message(self.window, "error", "错误", f"连接测试失败: {str(e)}")


# 全局应用实例
app = None 