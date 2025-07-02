"""
文本生成模块 - 会议纪要生成神器
"""

import json
import requests
from typing import Optional, Dict, Any, Callable
import time

from config import config
from logger import conversation_logger

class TextGenerator:
    """文本生成类"""
    
    def __init__(self):
        api_url = config.get("ollama_api_url", "http://127.0.0.1:11434/v1/chat/completions")
        self.api_url = api_url if api_url is not None else "http://127.0.0.1:11434/v1/chat/completions"
        
        model_name = config.get("ollama_model", "deepseek-r1:1.5b")
        self.model_name = model_name if model_name is not None else "deepseek-r1:1.5b"
        
        default_prompt = config.get("default_prompt", "")
        self.default_prompt = default_prompt if default_prompt is not None else ""
        
    def test_connection(self) -> bool:
        """
        测试Ollama连接
        
        Returns:
            连接是否成功
        """
        try:
            api_base = self.api_url.replace("/v1/chat/completions", "/api/tags")
            response = requests.get(api_base, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"连接Ollama失败: {e}")
            return False
    
    def get_available_models(self) -> list:
        """
        获取可用的模型列表
        
        Returns:
            模型列表
        """
        try:
            api_base = self.api_url.replace("/v1/chat/completions", "/api/tags")
            response = requests.get(api_base, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            else:
                return []
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return []
    
    def generate_text(self, 
                     transcription: str, 
                     meeting_info: str, 
                     custom_prompt: Optional[str] = None,
                     progress_callback: Optional[Callable[[str, float], None]] = None) -> str:
        """
        生成会议纪要
        
        Args:
            transcription: 会议录音文本
            meeting_info: 会议描述信息
            custom_prompt: 自定义提示词
            progress_callback: 进度回调函数
            
        Returns:
            生成的会议纪要
        """
        start_time = time.time()
        session_id = None
        
        try:
            if progress_callback:
                progress_callback("正在连接Ollama服务...", 0.1)
            
            # 检查连接
            if not self.test_connection():
                error_msg = "无法连接到Ollama服务，请确保Ollama正在运行"
                # 记录连接失败日志
                session_id = conversation_logger.log_conversation(
                    request_data={},
                    error=error_msg,
                    meeting_info=meeting_info,
                    transcription=transcription,
                    custom_prompt=custom_prompt,
                    model_name=self.model_name,
                    api_url=self.api_url,
                    processing_time=time.time() - start_time
                )
                raise Exception(error_msg)
            
            if progress_callback:
                progress_callback("正在生成会议纪要...", 0.3)
            
            # 准备提示词
            prompt = custom_prompt if custom_prompt else self.default_prompt
            if prompt:
                prompt = prompt.format(
                    meeting_info=meeting_info,
                    transcription=transcription,
                    meeting_time="[请根据会议描述信息填写]",
                    meeting_location="[请根据会议描述信息填写]",
                    host="[请根据会议描述信息填写]",
                    participants="[请根据会议描述信息填写]",
                    topics="[请根据会议内容提取]",
                    content="[请根据会议录音文本整理]",
                    decisions="[请根据会议内容提取]",
                    actions="[请根据会议内容提取]"
                )
            else:
                prompt = f"请根据以下会议录音文本和会议描述信息，生成一份格式化的会议纪要。\n\n会议描述信息：\n{meeting_info}\n\n会议录音文本：\n{transcription}"
            
            # 准备请求数据
            request_data = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            if progress_callback:
                progress_callback("正在调用LLM模型...", 0.5)
            
            # 发送请求
            response = requests.post(
                self.api_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=3600  # 1小时超时
            )
            
            if progress_callback:
                progress_callback("正在处理响应...", 0.8)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # 记录成功日志
                    session_id = conversation_logger.log_conversation(
                        request_data=request_data,
                        response_data=result,
                        meeting_info=meeting_info,
                        transcription=transcription,
                        custom_prompt=custom_prompt,
                        model_name=self.model_name,
                        api_url=self.api_url,
                        processing_time=processing_time
                    )
                    
                    if progress_callback:
                        progress_callback("生成完成", 1.0)
                    
                    return content
                else:
                    error_msg = "模型响应格式错误"
                    # 记录响应格式错误日志
                    session_id = conversation_logger.log_conversation(
                        request_data=request_data,
                        response_data=result,
                        error=error_msg,
                        meeting_info=meeting_info,
                        transcription=transcription,
                        custom_prompt=custom_prompt,
                        model_name=self.model_name,
                        api_url=self.api_url,
                        processing_time=processing_time
                    )
                    raise Exception(error_msg)
            else:
                error_msg = f"API请求失败: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                
                # 记录API请求失败日志
                session_id = conversation_logger.log_conversation(
                    request_data=request_data,
                    error=error_msg,
                    meeting_info=meeting_info,
                    transcription=transcription,
                    custom_prompt=custom_prompt,
                    model_name=self.model_name,
                    api_url=self.api_url,
                    processing_time=processing_time
                )
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时，请检查网络连接或模型响应时间"
            # 记录超时错误日志
            session_id = conversation_logger.log_conversation(
                request_data=request_data if 'request_data' in locals() else {},
                error=error_msg,
                meeting_info=meeting_info,
                transcription=transcription,
                custom_prompt=custom_prompt,
                model_name=self.model_name,
                api_url=self.api_url,
                processing_time=time.time() - start_time
            )
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "连接错误，请确保Ollama服务正在运行"
            # 记录连接错误日志
            session_id = conversation_logger.log_conversation(
                request_data=request_data if 'request_data' in locals() else {},
                error=error_msg,
                meeting_info=meeting_info,
                transcription=transcription,
                custom_prompt=custom_prompt,
                model_name=self.model_name,
                api_url=self.api_url,
                processing_time=time.time() - start_time
            )
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"生成会议纪要失败: {str(e)}"
            # 记录其他错误日志
            session_id = conversation_logger.log_conversation(
                request_data=request_data if 'request_data' in locals() else {},
                error=error_msg,
                meeting_info=meeting_info,
                transcription=transcription,
                custom_prompt=custom_prompt,
                model_name=self.model_name,
                api_url=self.api_url,
                processing_time=time.time() - start_time
            )
            raise Exception(error_msg)
    
    def update_config(self, api_url: Optional[str] = None, model_name: Optional[str] = None, prompt: Optional[str] = None):
        """
        更新配置
        
        Args:
            api_url: API地址
            model_name: 模型名称
            prompt: 提示词
        """
        if api_url:
            self.api_url = api_url
            config.set("ollama_api_url", api_url)
        
        if model_name:
            self.model_name = model_name
            config.set("ollama_model", model_name)
        
        if prompt:
            self.default_prompt = prompt
            config.set("default_prompt", prompt)
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        return {
            "api_url": self.api_url,
            "model_name": self.model_name,
            "default_prompt": self.default_prompt,
            "connection_status": self.test_connection(),
            "available_models": self.get_available_models()
        }
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Returns:
            统计信息字典
        """
        return conversation_logger.get_conversation_stats()
    
    def get_conversation_history(self, limit: int = 100) -> list:
        """
        获取对话历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            对话历史记录列表
        """
        return conversation_logger.get_conversation_history(limit)

# 全局文本生成器实例
text_generator = TextGenerator() 