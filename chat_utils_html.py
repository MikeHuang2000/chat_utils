import os
import re
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional

# 尝试导入 markdown 库，如果失败则给出提示
try:
    import markdown
except ImportError:
    raise ImportError("需要安装 `Markdown` 库才能导出为 HTML。请运行: pip install markdown Pygments")

def _generate_default_filename(messages: List[Dict[str, Any]]) -> str:
    """
    根据消息内容生成一个默认的文件基础名（不含扩展名）。
    (内部使用)

    规则:
    1. 寻找第一条用户消息的文本内容。
    2. 使用其前10个字符作为文件名前缀。
    3. 如果找不到用户消息或消息无文本，则使用'未命名聊天'。
    4. 附加 YYYYMMDD_HHMMSS 格式的时间戳。
    5. 清理文件名中的非法字符。

    Returns:
        str: 生成的文件基础名。
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    prefix = "未命名聊天"
    
    # 寻找第一条 user 消息的文本内容
    first_user_text = None
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                first_user_text = content.strip()
                break
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text" and part.get("text", "").strip():
                        first_user_text = part["text"].strip()
                        break
            if first_user_text:
                break
    
    if first_user_text:
        prefix = first_user_text[:10]

    # 移除Windows和Linux文件名中的非法字符
    safe_prefix = re.sub(r'[\\/*?:"<>|]', '_', prefix).strip()
    if not safe_prefix: # 如果清理后前缀为空（例如，用户输入了"<>:?"）
        safe_prefix = "未命名聊天"
        
    return f"chat_history\\{safe_prefix}_{timestamp}"

# --- 新的 HTML 导出模块 ---

def save_html(messages: List[Dict[str, Any]], output_filename: Optional[str] = None) -> None:
    """
    将消息历史记录保存为格式优美、带有样式的 HTML 文件。
    如果未提供文件名，将根据第一条用户消息和时间戳自动生成。

    Args:
        messages (List[Dict[str, Any]]): 消息列表。
        output_filename (Optional[str], optional): 输出的 HTML 文件名。默认为 None。
    """
    if not output_filename:
        base_name = _generate_default_filename(messages)
        output_filename = f"{base_name}.html"

    ROLE_EMOJI = {
        "system": "⚙️",
        "user": "👤",
        "assistant": "🤖",
        "thinking": "📝",
        "debug": "🧰",
    }
    
    # HTML 和 CSS 模板 (保持不变)
    html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对话记录</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
            background-color: #f0f2f5;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .chat-header {{
            background-color: #0d6efd;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .chat-body {{
            padding: 20px;
        }}
        .message {{
            display: flex;
            margin-bottom: 20px;
            align-items: flex-start;
        }}
        .message.user {{
            justify-content: flex-end;
        }}
        .message.assistant {{
            justify-content: flex-start;
        }}
        /* 将 details-box 居中显示 */
        .message.details-wrapper {{
            justify-content: center;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8em;
            flex-shrink: 0;
        }}
        .message.user .avatar {{
            order: 2;
            margin-left: 12px;
            background-color: #0d6efd;
        }}
        .message.assistant .avatar {{
            order: 1;
            margin-right: 12px;
            background-color: #198754;
        }}
        .content {{
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            position: relative;
        }}
        .message.user .content {{
            background-color: #e7f0ff;
            border-top-right-radius: 4px;
            order: 1;
        }}
        .message.assistant .content {{
            background-color: #f1f1f1;
            border-top-left-radius: 4px;
            order: 2;
        }}
        .content p {{
            margin: 0;
            line-height: 1.6;
        }}
        .content img.attached-image {{
            max-width: 100%;
            border-radius: 8px;
            margin-top: 10px;
        }}
        /* --- 代码块样式 --- */
        .content pre {{
            background-color: #282c34;
            color: #abb2bf;
            padding: 1em;
            border-radius: 8px;
            overflow-x: auto;
            font-family: "Fira Code", "Courier New", monospace;
            font-size: 0.9em;
        }}
        .content code {{
            font-family: "Fira Code", "Courier New", monospace;
        }}
        .content :not(pre) > code {{
            background-color: #e9eaec;
            color: #c7254e;
            padding: 2px 4px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        /* --- 可折叠部分样式 --- */
        .details-box {{
            margin: 10px 0;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: #fafafa;
            width: 100%; /* 让它撑满 */
        }}
        .details-box summary {{
            cursor: pointer;
            padding: 12px;
            font-weight: bold;
            outline: none;
            list-style: none; /* 移除默认的三角箭头 (在某些浏览器中) */
        }}
        .details-box summary::-webkit-details-marker {{
            display: none; /* 移除 Chrome/Safari 的三角箭头 */
        }}
        .details-box summary::before {{
            content: '▶';
            margin-right: 8px;
            font-size: 0.8em;
            color: #666;
        }}
        .details-box[open] > summary::before {{
            content: '▼';
        }}
        .details-box-content {{
            padding: 0 15px 15px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9em;
            color: #555;
            background-color: #fff;
            border-top: 1px solid #e0e0e0;
        }}
        .details-box-content pre {{
            background-color: #fdfdfd; /* 给pre一个浅色背景 */
            color: #333;
            padding: 1em;
            border-radius: 8px;
            border: 1px solid #eee;
            overflow-x: auto;
            font-family: "Courier New", monospace;
        }}
        .role-name {{
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">对话记录</div>
        <div class="chat-body">
            {chat_content}
        </div>
    </div>
</body>
</html>
    """

    try:
        assets_dir = f"{os.path.splitext(output_filename)[0]}.assets"
        os.makedirs(assets_dir, exist_ok=True)
        img_counter = 0
        
        html_content_parts = []

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            emoji = ROLE_EMOJI.get(role, "❓")

            # 处理可折叠的消息类型
            if role in ["system", "thinking", "debug"]:
                summary_text = {
                    "system": "查看系统提示词",
                    "thinking": "查看思考过程",
                    "debug": "查看DEBUG信息"
                }.get(role)
                
                cleaned_content = "\n".join(line for line in content.strip().split('\n') if line.strip())
                
                # --- BUG 修复点 ---
                # 将 <div class="details-box"> 替换为 <details class="details-box">
                # 这样它就是一个真正的可折叠元素了
                part_html = f"""
                <div class="message details-wrapper">
                    <details class="details-box">
                        <summary>{emoji} {summary_text}</summary>
                        <div class="details-box-content"><pre>{cleaned_content}</pre></div>
                    </details>
                </div>
                """
                html_content_parts.append(part_html)
                continue

            # 处理用户和助手的消息 (此部分逻辑不变)
            message_html = f'<div class="message {role}">'
            message_html += f'<div class="avatar">{emoji}</div>'
            message_html += '<div class="content">'
            
            message_html += f'<div class="role-name">{role.capitalize()}</div>'

            if isinstance(content, str):
                md_extensions = ['fenced_code', 'tables', 'codehilite']
                converted_content = markdown.markdown(content, extensions=md_extensions)
                message_html += converted_content
            
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        text_content = part.get('text', '')
                        md_extensions = ['fenced_code', 'tables', 'codehilite']
                        converted_content = markdown.markdown(text_content, extensions=md_extensions)
                        message_html += converted_content
                    
                    elif part.get("type") == "image_url":
                        image_data_url = part.get("image_url", {}).get("url", "")
                        match = re.search(r'data:image/(\w+);base64,(.+)', image_data_url)
                        if match:
                            img_ext = match.group(1)
                            base64_data = match.group(2)
                            img_bytes = base64.b64decode(base64_data)
                            
                            img_filename = f"image_{img_counter}.{img_ext}"
                            img_path = os.path.join(assets_dir, img_filename)
                            
                            with open(img_path, 'wb') as img_file:
                                img_file.write(img_bytes)
                            
                            relative_img_path = os.path.join(os.path.basename(assets_dir), img_filename)
                            message_html += f'<img src="{relative_img_path}" alt="附件图片 {img_counter}" class="attached-image">'
                            img_counter += 1

            message_html += '</div></div>'
            html_content_parts.append(message_html)

        # 组合最终的 HTML
        final_html = html_template.format(chat_content="\n".join(html_content_parts))
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"消息已成功保存到 HTML 文件 {output_filename}")

    except Exception as e:
        print(f"保存 HTML 文件时出错: {e}")