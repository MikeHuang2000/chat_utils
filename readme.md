# `chat_utils.py` 文档

<div style="
  background-color: #1A1B26;
  border: 1px solid #00DDC0;
  border-radius: 12px;
  padding: 30px 40px;
  font-family: 'Courier New', Courier, monospace;
  text-align: center;
  max-width: 650px;
  margin: 20px auto;
  box-shadow: 0 6px 25px rgba(0, 221, 192, 0.5);">
  <div style="
    font-size: 36px;
    font-weight: bold;
    letter-spacing: 3px;
    background-image: linear-gradient(90deg, #18C8FF, #32FFB4);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    filter: drop-shadow(0 0 6px rgba(0, 221, 192, 0.7));">
    华南理工大学 IBM俱乐部<span style="
      display: inline-block;
      width: 15px;
      height: 36px;
      margin-left: 12px;
      border-radius: 2px;
      vertical-align: bottom;
      background-image: linear-gradient(90deg, #18C8FF, #32FFB4);
      animation: blink 1s step-end infinite;">
    </span>
  </div>
</div>



`chat_utils.py` 是一个用于构建命令行或基于控制台的 LLM（大型语言模型）聊天界面的实用工具库。它提供了客户端初始化、消息管理、文件输入处理、聊天历史保存（JSON和Markdown）以及流式输出等功能。

## 目录

1.  环境依赖
2.  核心功能
3.  文件和输入处理
4.  配置和通用工具

---

## 1. 环境依赖

本库依赖以下 Python 包：

*   `openai`
*   `tkinter` (用于文件选择对话框)
*   `configparser`

## 2. 核心功能

### 1. 客户端管理

#### `create_client(base_url: str, api_key: str) -> Optional[OpenAI]`
创建一个 OpenAI 客户端实例。

*   **参数**:
    *   `base_url (str)`: API 的基础 URL。
    *   `api_key (str)`: 用于认证的 API 密钥。
*   **返回**: `OpenAI` 客户端实例，如果 `api_key` 为空或创建失败则返回 `None`。

---

### 2. 消息管理

#### `add_message(messages, role, content, image_path=None)`
向消息列表中添加一条新消息。

*   **参数**:
    *   `messages (List[Dict])`: 要添加到的消息列表。
    *   `role (str)`: 消息角色，建议使用库内常量，如 `chat.ROLE_USER`。
    *   `content (str)`: 消息的文本内容。
    *   `image_path (Optional[str])`: 图片文件的路径。**注意：图片只能在 `role='user'` 的消息中添加。**
*   **示例**:
    ```python
    messages = []
    # 添加纯文本消息
    chat.add_message(messages, chat.ROLE_USER, "请介绍一下这张图片。")
    # 添加图文消息
    chat.add_message(messages, chat.ROLE_USER, "这幅画的作者是谁？", image_path="path/to/mona_lisa.jpg")
    ```

---

### 3. 对话历史持久化

#### `save_message(messages, output_filename=None)`
将消息历史记录保存为 JSON 文件。

*   **参数**:
    *   `messages (List[Dict])`: 消息列表。
    *   `output_filename (Optional[str])`: 输出的 JSON 文件路径。如果为 `None`，将自动在 `chat_history/` 目录下生成文件名。

#### `load_message(input_filename: str) -> List[Dict]`
从 JSON 文件加载消息历史记录。

*   **参数**:
    *   `input_filename (str)`: 输入的 JSON 文件路径。
*   **返回**: 加载的消息列表。如果文件不存在或加载失败，返回一个空列表 `[]`。

#### `save_markdown(messages, output_filename=None)`
将消息历史记录保存为格式优美的 Markdown 文件。

*   **说明**: 如果消息中包含图片，图片将被解码并保存到与 Markdown 文件同名的 `.assets` 文件夹中，并在 Markdown 文件中正确引用。
*   **参数**:
    *   `messages (List[Dict])`: 消息列表。
    *   `output_filename (Optional[str])`: 输出的 Markdown 文件路径。如果为 `None`，将自动在 `chat_history/` 目录下生成文件名。

---

### 4. 模型交互

#### `send_message(client, origin_messages, model, enable_print=True, **extra_body)`
向大模型发送消息并流式处理输出。

*   **参数**:
    *   `client (OpenAI)`: 已创建的客户端实例。
    *   `origin_messages (List[Dict])`: 发送给模型的完整消息列表。
    *   `model (str)`: 要使用的模型名称。
    *   `enable_print (bool)`: 是否在控制台实时打印模型的思考和回答。
    *   `thinking_callback (Callable)`: `(str) -> None`，接收**思考过程**流式片段的回调函数。
    *   `content_callback (Callable)`: `(str) -> None`，接收**回答内容**流式片段的回调函数。
    *   `stop_callback (Callable)`: `(Tuple[str, str]) -> None`，在流结束后接收 `(完整回答, 完整思考)` 元组的回调函数。
    *   `**extra_body`: 其他要传递给 OpenAI API 的参数，例如 `temperature`, `top_p`, `enable_thinking=True` 等。
*   **返回**: 一个元组 `(full_answer, full_thinking)`，分别包含完整的回答字符串和完整的思考过程字符串。失败时返回 `(None, None)`。
*   **回调函数示例**:
    ```python
    def handle_thinking(chunk):
        print(f"Thinking: {chunk}")
    
    def handle_content(chunk):
        print(f"Content: {chunk}")
    
    def handle_stop(result):
        answer, thinking = result
        print(f"\n--- DONE ---\nAnswer Length: {len(answer)}\nThinking Length: {len(thinking)}")
    
    chat.send_message(
        client, messages, "your-model",
        thinking_callback=handle_thinking,
        content_callback=handle_content,
        stop_callback=handle_stop
    )
    ```

---

### 5. 用户界面与输入

#### `select_file_dialog(*filetypes) -> str`
打开一个对话框让用户选择文件。

*   **参数**:
    *   `*filetypes`: 可变参数，用于指定文件类型过滤器，格式为 `('描述', '通配符')`。
*   **返回**: 用户选择的文件的完整路径。如果取消，返回空字符串。
*   **示例**: `chat.select_file_dialog(('JSON files', '*.json'), ('All files', '*.*'))`

#### `select_directory_dialog() -> str`
打开一个对话框让用户选择一个文件夹。

*   **返回**: 用户选择的文件夹的完整路径。如果取消，返回空字符串。

#### `get_input(prompt=None) -> Tuple[str, Optional[str]]`
在命令行接收多行输入。

*   **说明**: 用户可以输入多行文本。通过输入 `Ctrl+Z` (Windows) 或 `Ctrl+D` (Linux/macOS) 来结束输入。在输入过程中，输入 `/image` 或 `/file` 会弹出文件选择框。
*   **返回**: 一个元组 `(文本内容, 文件路径)`。如果未选择文件，文件路径为 `None`。

---

### 6. 通用工具函数

#### `read_file(file_path: str) -> Optional[str]`
读取指定文件的全部文本内容。

*   **返回**: 文件内容的字符串，读取失败则返回 `None`。

#### `get_filenames(directory: str) -> List[Dict]`
获取指定目录下所有文件的文件名和扩展名（不递归）。

*   **返回**: 一个字典列表，例如 `[{"name": "file1", "ext": ".txt"}, ...]`。

#### `read_config(filename: str, section=None) -> Optional[Dict]`
读取 `.ini` 配置文件。

*   **参数**:
    *   `filename (str)`: `.ini` 文件路径。
    *   `section (Optional[str])`: 要读取的节。如果为 `None`，则读取所有节并合并。
*   **返回**: 包含配置项的字典，失败则返回 `None`。

#### `apply_replacements(strings: List[str], replacement_rules: Dict) -> List[str]`
对一个字符串列表批量应用替换规则。

*   **参数**:
    *   `strings (List[str])`: 待处理的字符串列表。
    *   `replacement_rules (Dict[str, str])`: 替换规则，格式为 `{旧内容: 新内容}`。
*   **返回**: 处理后的新字符串列表。

## 使用示例

```python
import chat_utils as cu

"""
-------------------------------------------
配置信息：
-------------------------------------------

"""
conf = cu.read_config("config.ini")

API_KEY = str(conf["api_key"])

BASE_URL = str(conf["base_url"])

MODEL = str(conf["model_name"])

SYSTEM_PROMPT = str(conf["system_prompt"])
# SYSTEM_PROMPT = "你是一个乐于回答各种问题的小助手，你的任务是提供专业、准确、有洞察力的回答。"

# 初始化消息，客户端
msg = []
cli = cu.create_client(BASE_URL,API_KEY)

# 添加系统提示词
cu.add_message(msg,"system",SYSTEM_PROMPT)

# 添加用户消息
cu.add_message(msg,"user","描述图片内容","C:\\Users\\Lenovo\\Pictures\\Saved Pictures\\AI\\2025.7.13\\test\\1322389258914.jpeg")

# 获取模型输出,拼接消息
res,thk = cu.send_message(cli,msg,MODEL)
cu.add_message(msg,"thinking",thk)
cu.add_message(msg,"assistant",res)

# 自由多行输入
word,imgpth = cu.get_input()
cu.add_message(msg,"user",word,imgpth)

# 获取模型输出,拼接消息
res,thk = cu.send_message(cli,msg,MODEL)
cu.add_message(msg,"thinking",thk)
cu.add_message(msg,"assistant",res)

# 保存json(可加载)和Markdown文件
cu.save_message(msg)
cu.save_markdown(msg)
```

## 配置文件示例

```
[Settings]

# API网址
base_url = https://open.bigmodel.cn/api/paas/v4

# API秘钥
api_key = 552763d4d9754aa99e110d604e2c4d0d.g9mvI9WCBctGCbv1

model_name = GLM-4.1V-Thinking-Flash

system_prompt = prompts/default assistant.txt

# 可选API网址，浏览器访问查看各自的官方申请和配置教程

# 智谱：https://bigmodel.cn/
# flash系列模型免费无限调用

# 阿里ModelScope：https://www.modelscope.cn/docs/model-service/API-Inference/intro
# 一天2000次调用，不限上下文长度

# 谷歌：https://ai.google.dev/gemini-api/docs/openai?hl=zh-cn
# Gemini-2.5-pro一天免费100次，Flash一天免费250次
# 需要外网环境
```

