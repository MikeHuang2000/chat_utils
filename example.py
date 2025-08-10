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