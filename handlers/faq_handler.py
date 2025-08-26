# handlers/faq_handler.py
from services.database_manager import database_manager
from utils.api_utils import send_group_message
import config
import re


def convert_content_to_cq(content):
    """将内容中的图片URL转换为CQ码格式（如果还没有转换的话）"""
    # 检查是否已经是CQ码格式
    if '[CQ:image' in content:
        # 如果已经是CQ码格式，直接返回
        return content

    # 匹配常见的图片URL格式
    image_url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'

    def replace_image_url(match):
        url = match.group(0)
        return f'[CQ:image,url={url}]'

    # 替换所有的图片URL为CQ码
    converted_content = re.sub(image_url_pattern, replace_image_url, content, flags=re.IGNORECASE)
    return converted_content


def handle_faq_query(event_data):
    """处理 #faq [key] 命令，查询FAQ内容"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#faq '):
            send_group_message(group_id, "格式错误，请使用: #faq <key>")
            return

        key = message_text[5:].strip()
        if not key:
            send_group_message(group_id, "请指定要查询的key")
            return

        # 获取FAQ内容
        content = database_manager.get_faq_content(key)

        if content is None:
            send_group_message(group_id, f"未找到FAQ条目: {key}")
            return

        # 转换内容中的图片URL为CQ码格式
        converted_content = convert_content_to_cq(content)

        # 发送内容
        response = f"📖 FAQ [{key}]:\n\n{converted_content}"
        send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"查询FAQ失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_faq_edit(event_data):
    """处理 #faq edit [key] [contents] 命令，编辑FAQ内容"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#faq edit '):
            send_group_message(group_id, "格式错误，请使用: #faq edit <key> <contents>")
            return

        content_part = message_text[10:].strip()  # 移除 '#faq edit ' 前缀
        if not content_part:
            send_group_message(group_id, "请提供key和内容")
            return

        # 解析key和contents，第一个空格后的内容都是contents
        space_index = content_part.find(' ')
        if space_index == -1:
            send_group_message(group_id, "请提供key和内容，用空格分隔")
            return

        key = content_part[:space_index].strip()
        contents = content_part[space_index + 1:].strip()

        if not key or not contents:
            send_group_message(group_id, "key和内容不能为空")
            return

        # 设置FAQ内容
        success = database_manager.set_faq_content(key, contents)

        if success:
            send_group_message(group_id, f"✅ FAQ条目 [{key}] 已更新")
        else:
            send_group_message(group_id, f"❌ 更新FAQ条目 [{key}] 失败")

    except Exception as e:
        error_msg = f"编辑FAQ失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_faq_command(event_data):
    """处理所有FAQ相关命令的主入口"""
    message_text = event_data.get('message', '')

    if message_text.startswith('#faq edit '):
        handle_faq_edit(event_data)
    elif message_text.startswith('#faq '):
        handle_faq_query(event_data)
    else:
        # 未知命令或帮助
        group_id = event_data.get('group_id')
        if group_id:
            help_msg = (
                "📚 FAQ 功能帮助:\n\n"
                "🔍 查询FAQ:\n"
                "#faq <key> - 查询指定key的FAQ内容\n\n"
                "✏️ 编辑FAQ:\n"
                "#faq edit <key> <contents> - 新增或覆盖指定key的FAQ内容\n\n"
                "💡 提示: contents支持文本和图片URL\n"
                "🖼️ 图片格式: https://example.com/image.jpg (会自动转换为CQ码)"
            )
            send_group_message(group_id, help_msg)
