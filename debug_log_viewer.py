"""
调试日志查看器详情显示问题
"""

import json
from datetime import datetime
from logger import conversation_logger

def debug_log_detail():
    """调试日志详情显示"""
    print("=" * 60)
    print("调试日志查看器详情显示问题")
    print("=" * 60)
    
    # 1. 获取日志数据
    print("\n1. 获取日志数据...")
    logs_data = conversation_logger.get_conversation_history(limit=10)
    print(f"   获取到 {len(logs_data)} 条日志记录")
    
    if not logs_data:
        print("   ✗ 没有找到日志数据")
        return
    
    # 2. 显示第一条日志的详细信息
    print("\n2. 显示第一条日志的详细信息...")
    first_log = logs_data[0]
    print(f"   会话ID: {first_log.get('session_id')}")
    print(f"   时间: {first_log.get('timestamp')}")
    print(f"   模型: {first_log.get('model_name')}")
    print(f"   API地址: {first_log.get('api_url')}")
    print(f"   状态: {'成功' if first_log.get('success') else '失败'}")
    print(f"   处理时间: {first_log.get('processing_time', 0):.2f}秒")
    print(f"   会议信息: {first_log.get('meeting_info', '无')}")
    print(f"   录音文本长度: {first_log.get('transcription_length', 0)} 字符")
    print(f"   自定义提示词: {first_log.get('custom_prompt', '无')}")
    
    # 3. 测试详情文本生成
    print("\n3. 测试详情文本生成...")
    detail_text = generate_detail_text(first_log)
    print("   生成的详情文本:")
    print("-" * 40)
    print(detail_text)
    print("-" * 40)
    
    # 4. 测试所有日志的详情生成
    print("\n4. 测试所有日志的详情生成...")
    for i, log in enumerate(logs_data[:3]):  # 只测试前3条
        print(f"\n   日志 {i+1}:")
        detail = generate_detail_text(log)
        print(f"   详情长度: {len(detail)} 字符")
        print(f"   前100字符: {detail[:100]}...")

def generate_detail_text(log_data):
    """生成详情文本（复制自log_viewer.py的逻辑）"""
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
    
    return detail_text

def test_log_viewer_integration():
    """测试日志查看器集成"""
    print("\n" + "=" * 60)
    print("测试日志查看器集成")
    print("=" * 60)
    
    try:
        from log_viewer import LogViewer
        import tkinter as tk
        
        print("✓ 成功导入LogViewer")
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        log_viewer = LogViewer(root)
        print("✓ 成功创建LogViewer实例")
        
        # 测试加载日志
        log_viewer.load_logs()
        print(f"✓ 成功加载日志，数据条数: {len(log_viewer.logs_data)}")
        
        # 测试详情显示
        if log_viewer.logs_data:
            first_log = log_viewer.logs_data[0]
            log_viewer.display_log_detail(first_log)
            print("✓ 成功显示日志详情")
            
            # 获取详情文本内容
            detail_content = log_viewer.detail_text.get("1.0", tk.END)
            print(f"✓ 详情文本长度: {len(detail_content)} 字符")
            if len(detail_content.strip()) > 0:
                print("✓ 详情文本不为空")
            else:
                print("✗ 详情文本为空")
        else:
            print("✗ 没有日志数据可显示")
        
        root.destroy()
        
    except ImportError as e:
        print(f"✗ 导入LogViewer失败: {e}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == "__main__":
    debug_log_detail()
    test_log_viewer_integration() 