import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import config # 导入配置

def send_group_message(group_id, message):
    """发送群聊消息"""
    url = f"{config.NAPCAT_BASE_URL}/send_group_msg"
    params = {
        "group_id": group_id,
        "message": message,
    }
    try:
        response = requests.get(url, params=params, verify=False, timeout=10)
        if response.status_code == 200:
            print(f"向群 {group_id} 发送消息成功")
        else:
            print(f"向群 {group_id} 发送消息失败: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"发送消息时发生网络异常: {e}")

def get_verification_code(token):
    """从云码平台获取验证码 (原方法1)"""
    data = {'token': token}
    try:
        response = requests.post(config.JJL_QUERY_URL, data=data)
        result = response.json()
        if result.get('code') == 0:
            return result.get('data', '')
        else:
            print(f"请求验证码失败: {result.get('msg', '未知错误')}")
            return None
    except Exception as e:
        print(f"请求验证码时发生异常: {e}")
        return None

def get_dynamic_code_2(api_key):
    """获取动态码 (原方法2)"""
    payload = {'api_key': api_key}
    try:
        with requests.Session() as s:
            response = s.post(config.DYNAMIC_CODE_URL, data=payload)
            if response.status_code != 200:
                print(f"请求动态码失败，状态码：{response.status_code}")
                return None
            soup = BeautifulSoup(response.text, 'html.parser')
            code_div = soup.find('div', {'class': 'dynamic-code'})
            
            if code_div:
                dynamic_code = code_div.get_text(strip=True)
                if dynamic_code and dynamic_code != "等待提交...":
                    return dynamic_code
            print("未找到有效的动态码")
            return None
    except Exception as e:
        print(f"请求动态码时发生异常: {e}")
        return None

def get_ai_response_stream(model, messages):
    """获取AI模型的流式响应"""
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
    )
    return client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    )