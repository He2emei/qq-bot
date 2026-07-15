import requests
import json
import uuid

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: BeautifulSoup (bs4) not available. Some features may not work properly.")

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI package not available. AI features may not work properly.")
    # Create a dummy OpenAI class to prevent import errors
    class OpenAI:
        def __init__(self, api_key=None, base_url=None):
            pass
import config # 导入配置

try:
    import websockets.sync.client
    HAS_WEBSOCKETS_SYNC = True
except ImportError:
    HAS_WEBSOCKETS_SYNC = False


def _napcat_ws_request(action, params, timeout=20):
    if not getattr(config, "NAPCAT_WS_URL", ""):
        return None

    if not HAS_WEBSOCKETS_SYNC:
        print("websockets.sync.client 不可用，无法使用 NapCat WebSocket")
        return None

    headers = {}
    if getattr(config, "NAPCAT_ACCESS_TOKEN", ""):
        headers["Authorization"] = f"Bearer {config.NAPCAT_ACCESS_TOKEN}"

    payload = {
        "action": action,
        "params": params,
        "echo": str(uuid.uuid4()),
    }

    try:
        with websockets.sync.client.connect(
            config.NAPCAT_WS_URL,
            additional_headers=headers,
            open_timeout=timeout,
            close_timeout=5,
        ) as websocket:
            websocket.send(json.dumps(payload, ensure_ascii=False))
            while True:
                raw_message = websocket.recv(timeout=timeout)
                data = json.loads(raw_message)
                if data.get("echo") == payload["echo"]:
                    if data.get("status") == "ok":
                        return data
                    print(f"NapCat WebSocket action失败: {action}, {data}")
                    return None
    except Exception as e:
        print(f"NapCat WebSocket请求失败: {action} - {e}")
        return None


def send_group_message(group_id, message):
    """发送群聊消息"""
    ws_result = _napcat_ws_request(
        "send_group_msg",
        {
            "group_id": group_id,
            "message": message,
        },
        timeout=10,
    )
    if ws_result:
        print(f"向群 {group_id} 发送消息成功")
        return ws_result

    url = f"{config.NAPCAT_BASE_URL}/send_group_msg"
    params = {
        "group_id": group_id,
        "message": message,
    }
    try:
        response = requests.get(url, params=params, verify=False, timeout=10)
        if response.status_code == 200:
            result = _parse_http_onebot_response(response, "send_group_msg")
            if result is None:
                return None
            print(f"向群 {group_id} 发送消息成功")
            return result
        else:
            print(f"向群 {group_id} 发送消息失败: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"发送消息时发生网络异常: {e}")
    return None

def send_group_forward_message(group_id, messages):
    """发送群合并转发消息"""
    ws_result = _napcat_ws_request(
        "send_group_forward_msg",
        {
            "group_id": group_id,
            "messages": messages,
        },
        timeout=20,
    )
    if ws_result:
        print(f"向群 {group_id} 发送合并转发消息成功")
        return ws_result

    url = f"{config.NAPCAT_BASE_URL}/send_group_forward_msg"
    payload = {
        "group_id": group_id,
        "messages": messages,
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=20)
        if response.status_code == 200:
            result = _parse_http_onebot_response(response, "send_group_forward_msg")
            if result is None:
                return None
            print(f"向群 {group_id} 发送合并转发消息成功")
            return result
        else:
            print(f"向群 {group_id} 发送合并转发消息失败: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"发送合并转发消息时发生网络异常: {e}")

    return None


def _parse_http_onebot_response(response, action):
    try:
        payload = response.json()
    except ValueError:
        return {"raw": response.text}

    if isinstance(payload, dict):
        status = payload.get("status")
        retcode = payload.get("retcode")
        if (status is not None and status != "ok") or (retcode is not None and retcode != 0):
            print(f"NapCat HTTP action失败: {action}, status={status}, retcode={retcode}")
            return None
    return payload


def send_private_message(user_id, message):
    """发送私聊消息，并仅在 OneBot 确认成功时返回结果。"""
    ws_result = _napcat_ws_request(
        "send_private_msg",
        {"user_id": user_id, "message": message},
        timeout=10,
    )
    if ws_result:
        print(f"向用户 {user_id} 发送消息成功")
        return ws_result

    url = f"{config.NAPCAT_BASE_URL}/send_private_msg"
    try:
        response = requests.get(
            url,
            params={"user_id": user_id, "message": message},
            verify=False,
            timeout=10,
        )
        if response.status_code == 200:
            result = _parse_http_onebot_response(response, "send_private_msg")
            if result is not None:
                print(f"向用户 {user_id} 发送消息成功")
            return result
        print(f"向用户 {user_id} 发送消息失败: {response.status_code}, {response.text}")
    except requests.RequestException as exc:
        print(f"发送私聊消息时发生网络异常: {exc}")
    return None

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

            if not HAS_BS4:
                print("BeautifulSoup not available, cannot parse HTML response")
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
