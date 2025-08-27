# handlers/faq_handler.py
from services.database_manager import database_manager
from utils.api_utils import send_group_message
from utils.image_utils import image_manager
import config
import re


def process_faq_content(content):
    """处理FAQ内容，将图片URL下载到本地并转换为CQ码格式"""
    try:
        # 使用图片管理器处理内容中的图片
        processed_content = image_manager.process_content_images(content)
        return processed_content
    except Exception as e:
        print(f"处理FAQ内容失败: {e}")
        return content


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

        # 内容已经是处理过的格式（包含本地图片路径），直接发送
        response = f"📖 FAQ [{key}]:\n\n{content}"
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

        # 处理内容中的图片，下载到本地
        processed_contents = process_faq_content(contents)

        # 设置FAQ内容
        success = database_manager.set_faq_content(key, processed_contents)

        if success:
            send_group_message(group_id, f"✅ FAQ条目 [{key}] 已更新")
            # 如果内容包含图片，显示处理结果
            if '[CQ:image' in processed_contents and processed_contents != contents:
                send_group_message(group_id, "🖼️ 图片已下载并保存到本地")
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
                "💡 提示: contents支持文本和图片\n"
                "🖼️ 图片处理: 系统会自动下载图片并保存到本地，确保图片永久可用\n"
                "📎 支持格式: 直接发送图片或使用图片URL"
            )
            send_group_message(group_id, help_msg)
