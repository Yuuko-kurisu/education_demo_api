import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
# API_KEY_Deepseek = "sk-29b1eada98c142cda17fcbf1b2f7ba2b"  
API_KEY_Deepseek = os.environ.get('API_KEY_Deepseek')
API_KEY_zhipu = os.environ.get('ZHIPUAI_API_KEY')

API_KEY = API_KEY_Deepseek

# deepseek.py 
 
import requests
 
# 填写你的 API Key

 
url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
 
data = {
    "model": "deepseek-chat",  # 指定使用 R1 模型（deepseek-reasoner）或者 V3 模型（deepseek-chat）
    "messages": [
        {"role": "system", "content": "你是一个专业的助手"},
        {"role": "user", "content": "你是谁？"}
    ],
    "stream": False  # 关闭流式传输
}
 
# response = requests.post(url, headers=headers, json=data)
 
# if response.status_code == 200:
#     result = response.json()
#     print(result['choices'][0]['message']['content'])
# else:
#     print("请求失败，错误码：", response.status_code)


import requests

# def deepseek_chat(system_prompt=None, user_prompt=None, api_key=API_KEY):
#     """
#     调用DeepSeek API生成对话回复
    
#     参数:
#     system_prompt (str): 系统提示词，默认值"你是一个专业的助手"
#     user_prompt (str): 用户输入的提示词（必填）
#     api_key (str): DeepSeek API密钥（必填）
    
#     返回:
#     str: 模型生成的回复内容
#     """
#     # 参数校验
#     if not user_prompt:
#         raise ValueError("user_prompt参数不能为空")
#     if not api_key:
#         raise ValueError("api_key参数不能为空")
    
#     url = "https://api.deepseek.com/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_key}"
#     }
    
#     data = {
#         "model": "deepseek-chat",
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ],
#         "stream": False
#     }
    
#     try:
#         response = requests.post(url, headers=headers, json=data, timeout=30)
#         response.raise_for_status()  # 处理HTTP错误状态码
#         result = response.json()
#         return result['choices'][0]['message']['content']
#     except requests.exceptions.RequestException as e:
#         print(f"请求失败: {str(e)}")
#         raise
#     except KeyError as e:
#         print(f"解析响应失败: {str(e)}")
#         print("原始响应:", response.text)
#         raise

def zhipuai_chat(system_prompt=None, user_prompt=None, api_key=API_KEY_zhipu):
    """
    调用DeepSeek API生成对话回复
    
    参数:
    system_prompt (str): 系统提示词，默认值"你是一个专业的助手"
    user_prompt (str): 用户输入的提示词（必填）
    api_key (str): DeepSeek API密钥（必填）
    
    返回:
    str: 模型生成的回复内容
    """
    # 参数校验
    if not user_prompt:
        raise ValueError("user_prompt参数不能为空")
    if not api_key:
        raise ValueError("api_key参数不能为空")
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "chatglm-6b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # 处理HTTP错误状态码
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        raise
    except KeyError as e:
        print(f"解析响应失败: {str(e)}")
        print("原始响应:", response.text)
        raise

# # 使用示例
# response = deepseek_chat(
#     system_prompt="你是一个精通Python的专家",
#     user_prompt="介绍自己？",
#     api_key=API_KEY
# )
# print(response)

def deepseek_chat(user_prompt=None,system_prompt="你是一个专业的助手", model = 'DeepSeek',api_key=API_KEY):
    """
    调用DeepSeek API生成对话回复
    
    参数:
    system_prompt (str): 系统提示词，默认值"你是一个专业的助手"
    user_prompt (str): 用户输入的提示词（必填）
    api_key (str): DeepSeek API密钥（必填）
    
    返回:
    str: 模型生成的回复内容
    """
    # 参数校验
    if not user_prompt:
        raise ValueError("user_prompt参数不能为空")
    if not api_key:
        raise ValueError("api_key参数不能为空")
    
    if model == 'DeepSeek':
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # 处理HTTP错误状态码
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        raise
    except KeyError as e:
        print(f"解析响应失败: {str(e)}")
        print("原始响应:", response.text)
        raise