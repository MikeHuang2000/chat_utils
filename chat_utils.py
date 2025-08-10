# chat_utils.py

import os
import json
import base64
import re
import tkinter as tk
from tkinter import filedialog
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
import configparser

# --- 全局常量 ---
# 角色定义
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"
ROLE_THINKING = "thinking"
ROLE_DEBUG = "debug"

# 默认目录
DEFAULT_CHAT_HISTORY_DIR = "chat_history"

# 支持的图片MIME类型
SUPPORTED_IMAGE_MIMETYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
}

# Markdown 角色表情符号
MARKDOWN_ROLE_EMOJI = {
    ROLE_SYSTEM: "⚙️",
    ROLE_USER: "👤",
    ROLE_ASSISTANT: "🤖",
    ROLE_THINKING: "📝",
    ROLE_DEBUG: "🧰",
}

# --- 1. 创建 Client ---
def create_client(base_url: str, api_key: str) -> Optional[OpenAI]:
    """
    创建一个 OpenAI 客户端实例。

    Args:
        base_url (str): API 的基础 URL。
        api_key (str): 用于认证的 API 密钥。

    Returns:
        Optional[OpenAI]: 成功则返回 OpenAI 客户端实例，否则返回 None。
    """
    if not api_key:
        print("[ERROR] API 密钥不能为空。")
        return None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client
    except Exception as e:
        print(f"[ERROR] 创建客户端时发生错误: {e}")
        return None


# --- 内部辅助函数: 图片转 Base64 ---
def _image_to_base64(image_path: str) -> Optional[Tuple[str, str]]:
    """
    将图片文件编码为 Base64 字符串，并返回MIME类型和数据。(内部使用)

    Args:
        image_path (str): 图片文件的路径。

    Returns:
        Optional[Tuple[str, str]]: 成功则返回 (图片MIME类型, Base64字符串)，否则返回 None。
    """
    print("图片处理开始...")
    try:
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = SUPPORTED_IMAGE_MIMETYPES.get(ext, 'image/jpeg')
        if ext not in SUPPORTED_IMAGE_MIMETYPES:
            print(f"[WARNING] 不支持的图片格式 {ext}，将尝试作为 jpeg 处理。")

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            print("图片处理完成。")
            return mime_type, encoded_string
    except FileNotFoundError:
        print(f"[ERROR] 文件未找到: {image_path}")
        return None
    except IOError as e:
        print(f"[ERROR] 无法读取图片文件 {image_path}: {e}")
        return None


# --- 2. 向 Message 中添加内容 ---
def add_message(
    messages: List[Dict[str, Any]],
    role: str,
    content: str,
    image_path: Optional[str] = None
) -> None:
    """
    向消息列表中添加一条新消息，支持文本和图文内容。

    Args:
        messages (List[Dict[str, Any]]): 要添加到的消息列表。
        role (str): 消息的角色 (例如 'user', 'assistant', 'system')。
        content (str): 消息的文本内容。
        image_path (Optional[str], optional): 图片文件的路径。如果提供，将作为图文消息添加。
    """
    if image_path:
        if role != ROLE_USER:
            print(f"[WARNING] 图片只能在 '{ROLE_USER}' 角色的消息中添加。")
            return

        encoded_data = _image_to_base64(image_path)
        if encoded_data:
            mime_type, base64_image = encoded_data
            message_content = [
                {"type": "text", "text": content},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                }
            ]
            messages.append({"role": ROLE_USER, "content": message_content})
            print(f"成功添加了文本和图片 '{os.path.basename(image_path)}'。")
        else:
            print("[ERROR] 因图片编码失败，未添加消息。")
    else:
        messages.append({"role": role, "content": content})
        if isinstance(content, str):
            log_preview = content.replace("\n", " ")[:20]
            print(f"成功添加了角色为 '{role}' 的文本消息: {log_preview}...")
        else:
            print(f"成功添加了角色为 '{role}' 的消息。")


def _generate_default_filename(messages: List[Dict[str, Any]]) -> str:
    """
    根据消息内容生成一个默认的文件基础名（不含扩展名和目录）。(内部使用)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    prefix = "未命名聊天"

    first_user_text = None
    for msg in messages:
        if msg.get("role") == ROLE_USER:
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

    safe_prefix = re.sub(r'[\\/*?:"<>|]', '_', prefix).strip()
    if not safe_prefix:
        safe_prefix = "未命名聊天"

    return f"{safe_prefix}_{timestamp}"


# --- 3. save_message_to_json ---
def save_message(messages: List[Dict[str, Any]], output_filename: Optional[str] = None) -> None:
    """
    将消息历史记录保存为 JSON 文件。

    如果未提供文件名，将根据第一条用户消息和时间戳自动生成。

    Args:
        messages (List[Dict[str, Any]]): 消息列表。
        output_filename (Optional[str], optional): 输出的 JSON 文件路径。默认为 None。
    """
    if not output_filename:
        base_name = _generate_default_filename(messages)
        output_filename = os.path.join(DEFAULT_CHAT_HISTORY_DIR, f"{base_name}.json")

    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
        print(f"消息已成功保存到: {output_filename}")
    except (IOError, TypeError) as e:
        print(f"[ERROR] 保存 JSON 文件时出错: {e}")


# --- 4. 读取 Message 到变量 ---
def load_message(input_filename: str) -> List[Dict[str, Any]]:
    """
    从 JSON 文件加载消息历史记录。

    Args:
        input_filename (str): 输入的 JSON 文件路径。

    Returns:
        List[Dict[str, Any]]: 加载的消息列表，如果文件不存在或加载失败则返回空列表。
    """
    if not os.path.exists(input_filename):
        return []
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        print(f"消息已从 {input_filename} 加载。")
        return messages
    except (IOError, json.JSONDecodeError) as e:
        print(f"[ERROR] 从 JSON 文件加载消息时出错: {e}")
        return []


# --- 5. save_message_to_markdown ---
def save_markdown(messages: List[Dict[str, Any]], output_filename: Optional[str] = None) -> None:
    """
    将消息历史记录保存为格式优美的 Markdown 文件。

    如果未提供文件名，将自动生成。图片等资源将保存在同名的 `.assets` 文件夹中。

    Args:
        messages (List[Dict[str, Any]]): 消息列表。
        output_filename (Optional[str], optional): 输出的 Markdown 文件路径。默认为 None。
    """
    if not output_filename:
        base_name = _generate_default_filename(messages)
        output_filename = os.path.join(DEFAULT_CHAT_HISTORY_DIR, f"{base_name}.md")

    try:
        output_dir = os.path.dirname(output_filename)
        assets_dir_name = f"{os.path.splitext(os.path.basename(output_filename))[0]}.assets"
        assets_dir = os.path.join(output_dir, assets_dir_name)
        os.makedirs(assets_dir, exist_ok=True)
        img_counter = 0

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("# 对话记录\n\n")
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                emoji = MARKDOWN_ROLE_EMOJI.get(role, "❓")
                f.write(f"## {emoji} {role.capitalize()}\n\n")

                if isinstance(content, str):
                    cleaned_content = "\n".join(line for line in content.strip().split('\n') if line.strip())
                    if role in (ROLE_THINKING, ROLE_SYSTEM, ROLE_DEBUG):
                        summary_text = {
                            ROLE_THINKING: "查看思考过程",
                            ROLE_SYSTEM: "查看系统提示词",
                            ROLE_DEBUG: "查看DEBUG信息"
                        }.get(role)
                        f.write(f"<details>\n<summary>{summary_text}</summary>\n{cleaned_content}\n</details>\n\n")
                    else:
                        f.write(f"{content}\n\n")
                elif isinstance(content, list):
                    for part in content:
                        if part.get("type") == "text":
                            f.write(f"{part.get('text', '')}\n\n")
                        elif part.get("type") == "image_url":
                            image_data_url = part.get("image_url", {}).get("url", "")
                            match = re.search(r'data:image/(\w+);base64,(.+)', image_data_url)
                            if match:
                                img_ext, base64_data = match.groups()
                                img_bytes = base64.b64decode(base64_data)
                                
                                img_filename = f"image_{img_counter}.{img_ext}"
                                img_path = os.path.join(assets_dir, img_filename)
                                
                                with open(img_path, 'wb') as img_file:
                                    img_file.write(img_bytes)
                                
                                relative_img_path = os.path.join(assets_dir_name, img_filename)
                                f.write(f"![附件图片]({relative_img_path.replace(os.sep, '/')})\n\n")
                                img_counter += 1
                
                f.write("---\n\n")
        print(f"消息已成功保存到 Markdown 文件: {output_filename}")
    except Exception as e:
        print(f"[ERROR] 保存 Markdown 文件时出错: {e}")


# --- 6. 发送 Message 并流式输出 ---
def send_message(
    client: OpenAI,
    origin_messages: List[Dict[str, Any]],
    model: str,
    enable_print: bool = True,
    thinking_callback: Optional[Callable[[str], None]] = None,
    content_callback: Optional[Callable[[str], None]] = None,
    stop_callback: Optional[Callable[[Tuple[str, str]], None]] = None,
    **extra_body: Any
) -> Tuple[Optional[str], Optional[str]]:
    """
    向大模型发送消息并流式处理输出，支持区分思考和回答。

    Args:
        client (OpenAI): OpenAI 客户端实例。
        origin_messages (List[Dict[str, Any]]): 发送给模型的原始消息列表。
        model (str): 要使用的模型名称。
        enable_print (bool, optional): 是否在控制台打印流式输出。默认为 True。
        thinking_callback (Optional[Callable]): 接收思考过程(chunk)的回调函数。
        content_callback (Optional[Callable]): 接收正文(chunk)的回调函数。
        stop_callback (Optional[Callable]): 在结束后接收完整(思考, 正文)的回调函数。
        **extra_body (Any): 附加参数，如 temperature, top_p, stream, enable_thinking。

    Returns:
        Tuple[Optional[str], Optional[str]]: 返回一个元组 (完整回答文本, 完整思考过程文本)。
                                             失败时返回 (None, None)。
    """
    params = {"stream": True, **extra_body}
    has_callbacks = all(cb is not None for cb in [thinking_callback, content_callback, stop_callback])
    
    # 净化消息列表，移除无效角色和字段，防止API调用失败
    valid_roles = {ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM}
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in origin_messages
        if isinstance(msg, dict) and "role" in msg and "content" in msg and msg["role"] in valid_roles
    ]
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **params
        )

        full_response_content = []
        thinking_log = []
        is_thinking_started = False
        is_answer_started = False

        if enable_print:
            print(f"{MARKDOWN_ROLE_EMOJI[ROLE_ASSISTANT]} Assistant: ", end="", flush=True)

        for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            
            # 捕获思考过程
            reasoning_chunk = getattr(delta, 'reasoning_content', None)
            if reasoning_chunk:
                if not is_thinking_started:
                    if enable_print:
                        print("🤔 (正在思考...)\n", end="", flush=True)
                    is_thinking_started = True
                if enable_print:
                    print(reasoning_chunk, end="", flush=True)
                thinking_log.append(reasoning_chunk)
                if has_callbacks:
                    thinking_callback(reasoning_chunk)

            # 捕获正式回答
            answer_chunk = getattr(delta, 'content', None)
            if answer_chunk:
                if not is_answer_started:
                    if is_thinking_started and enable_print:
                        print("\n\n✅ (回答如下)\n", end="", flush=True)
                    is_answer_started = True
                if enable_print:
                    print(answer_chunk, end="", flush=True)
                full_response_content.append(answer_chunk)
                if has_callbacks:
                    content_callback(answer_chunk)
        
        if enable_print:
            print()  # 确保在流式输出后换行

        full_answer = "".join(full_response_content)
        full_thinking = "".join(thinking_log)
        
        if has_callbacks:
            stop_callback((full_answer, full_thinking))

        return full_answer, full_thinking

    except Exception as e:
        print(f"\n[ERROR] 请求大模型时发生错误: {e}")
        return None, None


# --- 7. 选取文件 ---
def select_file_dialog(*filetypes: Tuple[str, str]) -> str:
    """
    打开一个对话框让用户选择文件。

    Args:
        *filetypes (Tuple[str, str]): 可变参数，用于指定文件类型过滤器。
            格式: ('描述', '通配符'), 例如 ('JSON files', '*.json')。
            如果不提供，则允许所有文件。

    Returns:
        str: 用户选择的文件的完整路径，如果取消选择则返回空字符串。
    """
    root = tk.Tk()
    root.withdraw()
    
    if not filetypes:
        filetypes = (("所有文件", "*.*"),)

    try:
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        return filepath or ""
    except Exception as e:
        print(f"[ERROR] 打开文件对话框时出错: {e}")
        return ""


# --- 8. 选取路径 ---
def select_directory_dialog() -> str:
    """
    打开一个对话框让用户选择一个文件夹路径。

    Returns:
        str: 用户选择的文件夹的完整路径，如果取消选择则返回空字符串。
    """
    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.askdirectory()
        return path or ""
    except Exception as e:
        print(f"[ERROR] 打开目录对话框时出错: {e}")
        return ""


# --- 9. 接受多行输入 ---
def get_input(prompt: str = None) -> Tuple[str, Optional[str]]:
    """
    在命令行接收多行输入，直到用户输入空行或EOF (Ctrl+Z/D)。
    支持通过输入 '/image' 或 '/file' 命令来选择文件。

    Args:
        prompt (str, optional): 显示给用户的提示信息。

    Returns:
        Tuple[str, Optional[str]]: (用户输入的文本内容, 选择的文件路径或None)。
    """
    if prompt:
        print(f"{prompt} (输入 /image 或 /file 选择文件，Ctrl+Z/D 结束输入):")
    else:
        print("(输入 /image 或 /file 选择文件，Ctrl+Z/D 结束输入):")
        
    lines = []
    while True:
        try:
            line = input()
            command = line.strip().lower()

            if command in ('/image', '/file'):
                print("... 打开文件选择对话框 ...")
                filepath = select_file_dialog(
                    ("图片文件", "*.jpg *.jpeg *.png *.webp *.gif"),
                    ("所有文件", "*.*")
                )
                if filepath:
                    return "\n".join(lines), filepath
                else:
                    print("... 取消了文件选择，请继续输入 ...")
                    continue
            lines.append(line)
        except EOFError:
            break
            
    return "\n".join(lines), None


# --- 10. 读取文件 ---
def read_file(file_path: str) -> Optional[str]:
    """
    读取指定文件的全部文本内容。

    Args:
        file_path (str): 文件路径。

    Returns:
        Optional[str]: 文件内容字符串，如果读取失败则返回 None。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except (IOError, UnicodeDecodeError) as e:
        print(f"[ERROR] 读取文件 {file_path} 时出错: {e}")
        return None

    
# --- 11. 获取目录文件名 ---
def get_filenames(directory: str) -> List[Dict[str, str]]:
    """
    获取指定目录下所有文件的文件名和扩展名（不递归）。

    Args:
        directory (str): 要扫描的目录路径。

    Returns:
        List[Dict[str, str]]: 文件信息字典的列表。
            每个字典包含 "name" (基础名) 和 "ext" (扩展名) 两个键。
    """
    if not os.path.isdir(directory):
        print(f"[ERROR] 目录不存在: {directory}")
        return []
    
    result = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    name, ext = os.path.splitext(entry.name)
                    result.append({"name": name, "ext": ext})
    except OSError as e:
        print(f"[ERROR] 扫描目录 {directory} 时出错: {e}")

    return result


# --- 12. 读取ini文件 ---
def read_config(filename: str, section: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    读取 .ini 配置文件并返回一个字典。

    Args:
        filename (str): .ini 文件的路径。
        section (Optional[str], optional): 要读取的特定节(section)的名称。
                                         如果为 None，则读取所有节并合并到一个字典中。
                                         默认为 None。

    Returns:
        Optional[Dict[str, str]]: 包含配置项的字典，如果失败则返回 None。
    """
    if not os.path.exists(filename):
        print(f"[ERROR] 配置文件未找到: {filename}")
        return None

    config = configparser.ConfigParser()
    try:
        config.read(filename, encoding="utf-8-sig")
    except configparser.Error as e:
        print(f"[ERROR] 解析配置文件 {filename} 时出错: {e}")
        return None

    settings = {}
    if section is None:
        for sec in config.sections():
            settings.update(config.items(sec))
    elif config.has_section(section):
        settings.update(config.items(section))
    else:
        print(f"[ERROR] 在配置文件 {filename} 中未找到节: '{section}'")
        return None

    return settings


# --- 13. 字典规则替换（列表） ---
def apply_replacements(strings: List[str], replacement_rules: Dict[str, str]) -> List[str]:
    """
    对字符串列表中的每个字符串应用一个字典定义的替换规则。

    Args:
        strings (List[str]): 包含待处理字符串的列表。
        replacement_rules (Dict[str, str]): 替换规则字典，格式为 {旧内容: 新内容}。

    Returns:
        List[str]: 处理后的字符串列表。
    """
    processed_strings = []
    for s in strings:
        processed_str = s
        for old, new in replacement_rules.items():
            processed_str = processed_str.replace(old, new)
        processed_strings.append(processed_str)
    
    return processed_strings