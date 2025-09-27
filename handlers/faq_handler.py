# handlers/faq_handler.py
from services.database_manager import database_manager
from utils.image_utils import image_manager
from utils.api_utils import send_group_message
import config

def handle_faq_edit(event_data):
    """处理 #not edit [key] [contents] 命令，编辑FAQ内容"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#not edit '):
            send_group_message(group_id, "格式错误，请使用: #not edit <key> <contents>")
            return

        content_part = message_text[10:].strip()
        if not content_part:
            send_group_message(group_id, "请提供key和内容")
            return

        space_index = content_part.find(' ')
        if space_index == -1:
            send_group_message(group_id, "请提供key和内容，用空格分隔")
            return

        key = content_part[:space_index].strip()
        contents = content_part[space_index + 1:].strip()

        if not key or not contents:
            send_group_message(group_id, "key和内容不能为空")
            return

        processed_contents = process_faq_content(contents)

        success = database_manager.set_faq_content(key, processed_contents)

        if success:
            send_group_message(group_id, f"✅ FAQ条目 [{key}] 已更新")
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

def handle_faq_delete(event_data):
    """处理FAQ删除命令: #not delete <key>"""
    group_id = event_data['group_id']
    message = event_data['message'].strip()

    if not message.startswith('#not delete '):
        return

    parts = message[12:].strip().split()
    if len(parts) != 1:
        send_group_message(group_id, "❌ 格式错误，请使用: #not delete <key>")
        return

    key = parts[0].lower()
    success = database_manager.delete_faq_content(key)

    if success:
        send_group_message(group_id, f"✅ FAQ条目 [{key}] 已删除")
    else:
        send_group_message(group_id, f"❌ 删除FAQ条目失败或条目不存在: {key}")

def handle_faq_list(event_data):
    """处理FAQ列表命令: #not list"""
    group_id = event_data['group_id']
    message = event_data['message'].strip()

    if message != '#not list':
        return

    keys = database_manager.list_all_faq_keys()

    if keys:
        response = "📚 FAQ 条目列表:\n\n"
        for i, key in enumerate(keys, 1):
            response += f"{i}. {key}\n"
        response += f"\n共 {len(keys)} 个FAQ条目\n💡 使用 #not <key> 查看具体内容"
        send_group_message(group_id, response)
    else:
        send_group_message(group_id, "📚 暂无FAQ条目")

def handle_faq_help(event_data):
    """处理FAQ帮助命令: #not help"""
    group_id = event_data['group_id']
    message = event_data['message'].strip()

    if message != '#not help':
        return

    help_text = """📖 FAQ系统使用帮助:

🔍 查询FAQ: #not <key>
📝 编辑FAQ: #not edit <key> <contents>
🗑️ 删除FAQ: #not delete <key>
📋 列表FAQ: #not list
❓ 显示帮助: #not help

💡 说明:
- 支持文本和图片内容
- 图片会自动下载并本地化存储
- key不区分大小写
- 所有群成员均可使用"""

    send_group_message(group_id, help_text)

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
    import re

    if '[CQ:image' in content:
        return content

    image_url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'
    def replace_image_url(match):
        url = match.group(0)
        return f'[CQ:image,url={url}]'

    converted_content = re.sub(image_url_pattern, replace_image_url, content, flags=re.IGNORECASE)
    return converted_content

def handle_faq_command(event_data):
    """主FAQ命令路由器"""
    message = event_data['message'].strip()

    if message.startswith('#not '):
        command_part = message[5:].strip()

        if command_part.startswith('edit '):
            # 对于edit命令，需要重新构造消息以正确传递参数
            # command_part = "edit test 123"，我们需要构造 "#not edit test 123"
            reconstructed_message = '#not ' + command_part
            event_data['message'] = reconstructed_message
            handle_faq_edit(event_data)
        elif command_part.startswith('delete '):
            # 类似地处理delete命令
            reconstructed_message = '#not ' + command_part
            event_data['message'] = reconstructed_message
            handle_faq_delete(event_data)
        elif command_part == 'list':
            handle_faq_list(event_data)
        elif command_part == 'help':
            handle_faq_help(event_data)
        elif command_part and not command_part.startswith(('edit', 'delete', 'list', 'help')):
            # 认为是查询命令
            handle_faq_query(event_data)
        else:
            # 无效命令格式
            group_id = event_data['group_id']
            send_group_message(group_id, "❌ 无效的FAQ命令格式，使用 #not help 查看帮助")

def handle_faq_query(event_data):
    """处理 #not [key] 命令，查询FAQ内容"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#not '):
            send_group_message(group_id, "格式错误，请使用: #not <key>")
            return

        key = message_text[5:].strip()
        if not key:
            send_group_message(group_id, "请指定要查询的key")
            return

        content = database_manager.get_faq_content(key)

        if content is None:
            send_group_message(group_id, f"未找到FAQ条目: {key}")
            return

        response = f"📖 FAQ [{key}]:\n\n{content}"
        send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"查询FAQ失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)