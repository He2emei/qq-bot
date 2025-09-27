# handlers/faq_handler.py
from services.database_manager import database_manager
from utils.image_utils import image_manager
from utils.api_utils import send_group_message
import config

def handle_faq_edit(event_data):
    """处理FAQ编辑命令: #not edit <key> <contents>"""
    group_id = event_data['group_id']
    message = event_data['message'].strip()

    if not message.startswith('#not edit '):
        return

    content_part = message[10:].strip()
    if not content_part:
        send_group_message(group_id, "❌ 格式错误，请使用: #not edit <key> <contents>")
        return

    # 解析key和contents
    space_index = content_part.find(' ')
    if space_index == -1:
        send_group_message(group_id, "❌ 格式错误，请使用: #not edit <key> <contents>")
        return

    key = content_part[:space_index].strip().lower()
    contents = content_part[space_index + 1:].strip()

    if not key or not contents:
        send_group_message(group_id, "❌ key和contents不能为空")
        return

    # 处理内容中的图片
    processed_contents = process_faq_content(contents)

    # 保存到数据库
    success = database_manager.set_faq_content(key, processed_contents)

    if success:
        response = f"✅ FAQ条目 [{key}] 已更新"
        if processed_contents != contents:
            response += "\n🖼️ 图片已下载并保存到本地"
        send_group_message(group_id, response)
    else:
        send_group_message(group_id, "❌ 更新FAQ条目失败")

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
    """预处理FAQ内容，包括图片处理"""
    return image_manager.process_content_images(content)

def convert_content_to_cq(content):
    """将内容转换为CQ码格式（目前主要用于图片处理）"""
    return process_faq_content(content)

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
    """处理FAQ查询命令: #not <key>"""
    group_id = event_data['group_id']
    message = event_data['message'].strip()

    if not message.startswith('#not '):
        return

    parts = message[5:].strip().split()
    if len(parts) != 1:
        send_group_message(group_id, "❌ 格式错误，请使用: #not <key>")
        return

    key = parts[0].lower()
    content = database_manager.get_faq_content(key)

    if content:
        response = f"📖 FAQ [{key}]:\n\n{content}"
        send_group_message(group_id, response)
    else:
        send_group_message(group_id, f"❌ 未找到FAQ条目: {key}")