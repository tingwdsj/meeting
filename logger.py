"""
日志记录模块 - 会议纪要生成神器
用于记录系统调用ollama大模型的对话记录
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

from config import config

# 定义东八区
beijing_tz = timezone(timedelta(hours=8))

class ConversationLogger:
    """对话记录日志类"""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志文件目录，如果为None则使用配置文件中的设置
        """
        # 从配置文件获取日志设置
        config_log_dir = config.get("log_dir", "logs")
        if config_log_dir is None:
            config_log_dir = "logs"
        
        self.log_dir = Path(log_dir if log_dir is not None else config_log_dir)
        
        log_retention_days = config.get("log_retention_days", 30)
        self.log_retention_days = log_retention_days if log_retention_days is not None else 30
        
        enable_logging = config.get("enable_conversation_logging", True)
        self.enable_logging = enable_logging if enable_logging is not None else True
        
        log_level = config.get("log_level", "INFO")
        self.log_level = log_level if log_level is not None else "INFO"
        
        # 如果禁用日志记录，直接返回
        if not self.enable_logging:
            return
            
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志文件名（按日期）
        today = datetime.now(beijing_tz).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"conversation_{today}.log"
        self.json_file = self.log_dir / f"conversation_{today}.json"
        
        # 初始化日志记录器
        self._setup_logger()
        
        # 初始化JSON记录文件
        self._init_json_file()
        
        # 定期清理旧日志
        self._cleanup_old_logs()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 创建logger
        self.logger = logging.getLogger('conversation_logger')
        
        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(self.log_level, logging.INFO))
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 创建文件handler
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(level_map.get(self.log_level, logging.INFO))
            
            # 创建控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level_map.get(self.log_level, logging.INFO))
            
            # 创建格式器
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加handler
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _init_json_file(self):
        """初始化JSON记录文件"""
        if not self.json_file.exists():
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def _cleanup_old_logs(self):
        """清理旧日志文件"""
        try:
            self.clear_logs(self.log_retention_days)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"清理旧日志失败: {e}")
    
    def log_conversation(self, 
                        request_data: Dict[str, Any],
                        response_data: Optional[Dict[str, Any]] = None,
                        error: Optional[str] = None,
                        meeting_info: Optional[str] = None,
                        transcription: Optional[str] = None,
                        custom_prompt: Optional[str] = None,
                        model_name: Optional[str] = None,
                        api_url: Optional[str] = None,
                        processing_time: Optional[float] = None) -> str:
        """
        记录对话日志
        
        Args:
            request_data: 请求数据
            response_data: 响应数据
            error: 错误信息
            meeting_info: 会议信息
            transcription: 会议录音文本
            custom_prompt: 自定义提示词
            model_name: 模型名称
            api_url: API地址
            processing_time: 处理时间（秒）
            
        Returns:
            会话ID
        """
        # 如果禁用日志记录，返回空会话ID
        if not self.enable_logging:
            return ""
        
        # 生成会话ID
        session_id = datetime.now(beijing_tz).strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 构建日志记录
        log_entry = {
            "session_id": session_id,
            "timestamp": datetime.now(beijing_tz).isoformat(),
            "model_name": model_name,
            "api_url": api_url,
            "meeting_info": meeting_info,
            "transcription_length": len(transcription) if transcription else 0,
            "custom_prompt": custom_prompt,
            "request_data": {
                "model": request_data.get("model"),
                "messages": request_data.get("messages"),
                "stream": request_data.get("stream"),
                "temperature": request_data.get("temperature"),
                "max_tokens": request_data.get("max_tokens")
            },
            "processing_time": processing_time,
            "success": error is None
        }
        
        if response_data:
            log_entry["response_data"] = {
                "status_code": 200,
                "choices": response_data.get("choices", []),
                "usage": response_data.get("usage", {}),
                "response_length": len(response_data.get("choices", [{}])[0].get("message", {}).get("content", "")) if response_data.get("choices") else 0
            }
        elif error:
            log_entry["error"] = error
        
        # 记录到JSON文件
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            logs.append(log_entry)
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"保存JSON日志失败: {e}")
        
        # 记录到文本日志
        if hasattr(self, 'logger'):
            if error:
                self.logger.error(f"会话 {session_id} - 模型调用失败: {error}")
            else:
                response_length = log_entry.get("response_data", {}).get("response_length", 0)
                self.logger.info(f"会话 {session_id} - 模型调用成功 - 响应长度: {response_length} 字符 - 处理时间: {processing_time:.2f}秒")
        
        return session_id
    
    def get_conversation_history(self, limit: int = 100) -> list:
        """
        获取对话历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            对话历史记录列表
        """
        if not self.enable_logging or not hasattr(self, 'json_file'):
            return []
            
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 按时间倒序排列，取最新的记录
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"读取对话历史失败: {e}")
            return []
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Returns:
            统计信息字典
        """
        if not self.enable_logging or not hasattr(self, 'json_file'):
            return {
                "total_conversations": 0,
                "successful_conversations": 0,
                "failed_conversations": 0,
                "success_rate": 0.0,
                "average_processing_time": 0.0,
                "total_tokens_used": 0,
                "models_used": {},
                "logging_enabled": False
            }
            
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not logs:
                return {
                    "total_conversations": 0,
                    "successful_conversations": 0,
                    "failed_conversations": 0,
                    "success_rate": 0.0,
                    "average_processing_time": 0.0,
                    "total_tokens_used": 0,
                    "models_used": {},
                    "logging_enabled": True
                }
            
            total = len(logs)
            successful = sum(1 for log in logs if log.get("success", False))
            failed = total - successful
            success_rate = (successful / total) * 100 if total > 0 else 0
            
            # 计算平均处理时间
            processing_times = [log.get("processing_time", 0) for log in logs if log.get("processing_time")]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # 统计使用的模型
            models_used = {}
            for log in logs:
                model = log.get("model_name", "unknown")
                models_used[model] = models_used.get(model, 0) + 1
            
            # 统计总token使用量
            total_tokens = 0
            for log in logs:
                if log.get("response_data", {}).get("usage"):
                    usage = log["response_data"]["usage"]
                    total_tokens += usage.get("total_tokens", 0)
            
            return {
                "total_conversations": total,
                "successful_conversations": successful,
                "failed_conversations": failed,
                "success_rate": round(success_rate, 2),
                "average_processing_time": round(avg_processing_time, 2),
                "total_tokens_used": total_tokens,
                "models_used": models_used,
                "logging_enabled": True
            }
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"计算统计信息失败: {e}")
            return {
                "total_conversations": 0,
                "successful_conversations": 0,
                "failed_conversations": 0,
                "success_rate": 0.0,
                "average_processing_time": 0.0,
                "total_tokens_used": 0,
                "models_used": {},
                "logging_enabled": True,
                "error": str(e)
            }
    
    def clear_logs(self, days: Optional[int] = None):
        """
        清理指定天数之前的日志
        
        Args:
            days: 保留天数，如果为None则使用配置文件中的设置
        """
        if not self.enable_logging:
            return
            
        if days is None:
            days = self.log_retention_days
            
        try:
            cutoff_date = datetime.now(beijing_tz).timestamp() - (days * 24 * 60 * 60)
            
            # 清理JSON文件
            if hasattr(self, 'json_file') and self.json_file.exists():
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                
                # 过滤掉旧的记录
                filtered_logs = []
                for log in logs:
                    try:
                        log_timestamp = datetime.fromisoformat(log.get("timestamp", "")).timestamp()
                        if log_timestamp >= cutoff_date:
                            filtered_logs.append(log)
                    except:
                        # 如果时间戳格式有问题，保留记录
                        filtered_logs.append(log)
                
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_logs, f, ensure_ascii=False, indent=2)
            
            # 清理文本日志文件
            if hasattr(self, 'log_dir'):
                for log_file in self.log_dir.glob("conversation_*.log"):
                    try:
                        if log_file.stat().st_mtime < cutoff_date:
                            log_file.unlink()
                    except:
                        pass
            
            if hasattr(self, 'logger'):
                self.logger.info(f"已清理 {days} 天前的日志文件")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"清理日志失败: {e}")

# 全局日志记录器实例
conversation_logger = ConversationLogger() 