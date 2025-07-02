"""
日志查看器 - 会议纪要生成神器
用于查看和管理对话日志
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from logger import conversation_logger
from config import config

class LogViewer:
    """日志查看器类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("对话日志查看器 - 会议纪要生成神器")
        self.root.geometry("1200x800")
        
        # 设置样式和全局字体
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", font=("微软雅黑", 13))
        style.configure("Treeview.Heading", font=("微软雅黑", 14, "bold"))
        style.configure("TButton", font=("微软雅黑", 13))
        style.configure("TLabel", font=("微软雅黑", 13))
        style.configure("TLabelframe.Label", font=("微软雅黑", 13, "bold"))
        
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="对话日志查看器", font=("微软雅黑", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky="ew")
        
        # 按钮字体
        btn_font = ("微软雅黑", 13)
        
        # 刷新按钮
        refresh_btn = ttk.Button(control_frame, text="刷新日志", command=self.load_logs, style="TButton")
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清理日志按钮
        clear_btn = ttk.Button(control_frame, text="清理旧日志", command=self.clear_old_logs, style="TButton")
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 导出日志按钮
        export_btn = ttk.Button(control_frame, text="导出日志", command=self.export_logs, style="TButton")
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 统计信息按钮
        stats_btn = ttk.Button(control_frame, text="查看统计", command=self.show_stats, style="TButton")
        stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 搜索框架
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索:", font=btn_font).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_logs)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20, font=btn_font)
        search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 日志列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 10))
        
        # 日志列表
        columns = ("时间", "会话ID", "模型", "状态", "处理时间", "响应长度")
        self.log_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20, style="Treeview")
        
        # 设置列标题和宽度
        self.log_tree.heading("时间", text="时间")
        self.log_tree.heading("会话ID", text="会话ID")
        self.log_tree.heading("模型", text="模型")
        self.log_tree.heading("状态", text="状态")
        self.log_tree.heading("处理时间", text="处理时间(秒)")
        self.log_tree.heading("响应长度", text="响应长度")
        
        self.log_tree.column("时间", width=150)
        self.log_tree.column("会话ID", width=120)
        self.log_tree.column("模型", width=100)
        self.log_tree.column("状态", width=80)
        self.log_tree.column("处理时间", width=100)
        self.log_tree.column("响应长度", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.log_tree.bind("<Double-1>", self.show_log_detail)
        
        # 详情框架
        detail_frame = ttk.LabelFrame(main_frame, text="日志详情", padding="10")
        detail_frame.grid(row=2, column=2, sticky="nsew")
        
        # 详情文本
        self.detail_text = tk.Text(detail_frame, wrap=tk.WORD, width=50, height=30, font=("微软雅黑", 14))
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, font=("微软雅黑", 12))
        status_bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        # 存储日志数据
        self.logs_data = []
    
    def load_logs(self):
        """加载日志数据"""
        try:
            # 清空现有数据
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            
            # 获取日志数据
            self.logs_data = conversation_logger.get_conversation_history(limit=1000)
            
            # 添加到树形视图
            for log in self.logs_data:
                timestamp = log.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        time_str = timestamp
                else:
                    time_str = "未知"
                
                session_id = str(log.get("session_id", "未知"))
                model_name = log.get("model_name", "未知")
                success = log.get("success", False)
                status = "成功" if success else "失败"
                processing_time = log.get("processing_time", 0)
                response_length = log.get("response_data", {}).get("response_length", 0) if success else 0
                
                # 设置标签颜色
                tags = ("success",) if success else ("error",)
                
                self.log_tree.insert("", "end", values=(
                    time_str, session_id, model_name, status, 
                    f"{processing_time:.2f}", response_length
                ), tags=tags)
            
            # 设置标签颜色
            self.log_tree.tag_configure("success", background="#e8f5e8")
            self.log_tree.tag_configure("error", background="#ffe8e8")
            
            self.status_var.set(f"已加载 {len(self.logs_data)} 条日志记录")
            
            # 自动显示第一条日志的详情
            if self.logs_data:
                first_log = self.logs_data[0]
                self.display_log_detail(first_log)
                print(f"调试: 自动显示第一条日志详情，会话ID: {first_log.get('session_id')}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载日志失败: {str(e)}")
            self.status_var.set("加载日志失败")
    
    def filter_logs(self, *args):
        """过滤日志"""
        search_term = self.search_var.get().lower()
        
        # 清空现有显示
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # 重新添加匹配的日志
        for log in self.logs_data:
            # 检查是否匹配搜索条件
            match = False
            if search_term in str(log.get("session_id", "")).lower():
                match = True
            elif search_term in log.get("model_name", "").lower():
                match = True
            elif search_term in log.get("meeting_info", "").lower():
                match = True
            elif search_term in str(log.get("error", "")).lower():
                match = True
            
            if match or not search_term:
                timestamp = log.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        time_str = timestamp
                else:
                    time_str = "未知"
                
                session_id = str(log.get("session_id", "未知"))
                model_name = log.get("model_name", "未知")
                success = log.get("success", False)
                status = "成功" if success else "失败"
                processing_time = log.get("processing_time", 0)
                response_length = log.get("response_data", {}).get("response_length", 0) if success else 0
                
                tags = ("success",) if success else ("error",)
                
                self.log_tree.insert("", "end", values=(
                    time_str, session_id, model_name, status, 
                    f"{processing_time:.2f}", response_length
                ), tags=tags)
    
    def show_log_detail(self, event):
        """显示日志详情"""
        selection = self.log_tree.selection()
        if not selection:
            print("调试: 没有选中的项目")
            return
        
        # 获取选中的项目
        item = self.log_tree.item(selection[0])
        values = item['values']
        print(f"调试: 选中的项目值: {values}")
        
        if len(values) < 2:
            print("调试: 项目值数量不足")
            return
            
        session_id = str(values[1])  # 确保会话ID是字符串格式
        print(f"调试: 查找会话ID: {session_id}")
        session_id_digits = ''.join(filter(str.isdigit, session_id))
        
        # 查找对应的日志数据
        log_data = None
        for log in self.logs_data:
            log_session_id = str(log.get("session_id", ""))
            log_session_id_digits = ''.join(filter(str.isdigit, log_session_id))
            if log_session_id == session_id or log_session_id_digits == session_id_digits:
                log_data = log
                print(f"调试: 找到匹配的日志数据")
                break
        
        if log_data:
            print(f"调试: 显示日志详情，会话ID: {session_id}")
            self.display_log_detail(log_data)
        else:
            print(f"调试: 未找到匹配的日志数据")
            # 显示错误信息
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, f"未找到会话ID为 {session_id} 的日志数据")
    
    def display_log_detail(self, log_data):
        """显示日志详情（分段加载）"""
        try:
            self.detail_text.delete(1.0, tk.END)
            detail_text = f"""会话ID: {log_data.get('session_id', '未知')}
时间: {log_data.get('timestamp', '未知')}
模型: {log_data.get('model_name', '未知')}
API地址: {log_data.get('api_url', '未知')}
状态: {'成功' if log_data.get('success', False) else '失败'}
处理时间: {log_data.get('processing_time', 0):.2f}秒

会议信息:
{log_data.get('meeting_info', '无')}

录音文本长度: {log_data.get('transcription_length', 0)} 字符

自定义提示词:
{log_data.get('custom_prompt', '无')}

请求数据:
{json.dumps(log_data.get('request_data', {}), ensure_ascii=False, indent=2)}

"""
            if log_data.get('success'):
                response_data = log_data.get('response_data', {})
                detail_text += f"""响应数据:
状态码: {response_data.get('status_code', '未知')}
响应长度: {response_data.get('response_length', 0)} 字符
Token使用情况: {json.dumps(response_data.get('usage', {}), ensure_ascii=False, indent=2)}

响应内容:
{response_data.get('choices', [{}])[0].get('message', {}).get('content', '无')}
"""
            else:
                detail_text += f"""错误信息:
{log_data.get('error', '未知错误')}
"""
            self.full_detail_text = detail_text
            # 分段
            chunk_size = 2000
            self.detail_chunks = [detail_text[i:i+chunk_size] for i in range(0, len(detail_text), chunk_size)]
            self.current_chunk_index = 0
            # 显示第一段
            if self.detail_chunks:
                self.detail_text.insert(tk.END, self.detail_chunks[0])
                self.current_chunk_index = 1
            # 绑定滚动事件
            self.detail_text.bind('<MouseWheel>', self.on_detail_scroll)
            self.detail_text.bind('<KeyRelease>', self.on_detail_scroll)
            self.detail_text.bind('<Button-4>', self.on_detail_scroll)  # Linux
            self.detail_text.bind('<Button-5>', self.on_detail_scroll)  # Linux
            print(f"调试: 详情文本已插入，长度: {len(detail_text)} 字符")
        except Exception as e:
            print(f"调试: 显示日志详情时出错: {e}")
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, f"显示日志详情时出错: {str(e)}")

    def on_detail_scroll(self, event=None):
        """滚动到末尾时加载下一段"""
        # 检查是否已到达底部
        if float(self.detail_text.yview()[1]) == 1.0:
            if hasattr(self, 'detail_chunks') and self.current_chunk_index < len(self.detail_chunks):
                self.detail_text.insert(tk.END, self.detail_chunks[self.current_chunk_index])
                self.current_chunk_index += 1
    
    def clear_old_logs(self):
        """清理旧日志"""
        try:
            days = config.get("log_retention_days", 30)
            conversation_logger.clear_logs(days)
            messagebox.showinfo("成功", f"已清理 {days} 天前的日志文件")
            self.load_logs()
        except Exception as e:
            messagebox.showerror("错误", f"清理日志失败: {str(e)}")
    
    def export_logs(self):
        """导出日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="导出日志文件"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.logs_data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {str(e)}")
    
    def show_stats(self):
        """显示统计信息"""
        try:
            stats = conversation_logger.get_conversation_stats()
            
            stats_text = f"""对话统计信息:

总对话数: {stats.get('total_conversations', 0)}
成功对话: {stats.get('successful_conversations', 0)}
失败对话: {stats.get('failed_conversations', 0)}
成功率: {stats.get('success_rate', 0):.2f}%
平均处理时间: {stats.get('average_processing_time', 0):.2f}秒
总Token使用量: {stats.get('total_tokens_used', 0)}

使用的模型:
"""
            
            models_used = stats.get('models_used', {})
            for model, count in models_used.items():
                stats_text += f"  {model}: {count}次\n"
            
            messagebox.showinfo("统计信息", stats_text)
        except Exception as e:
            messagebox.showerror("错误", f"获取统计信息失败: {str(e)}")

def main():
    """主函数"""
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main() 