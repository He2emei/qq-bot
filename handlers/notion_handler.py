# handlers/notion_handler.py
import json
from datetime import datetime
from services.notion_service import daily_manager, notion_service
from utils.notion_utils import process_notion_blocks
from utils.api_utils import send_group_message
import config


def handle_daily_command(event_data):
    """处理 #daily 命令，获取今日日记内容"""
    try:
        # 获取今日页面
        today_page = daily_manager.get_today_page()

        if not today_page:
            # 如果今日页面不存在，创建一个
            try:
                result = daily_manager.add_today_page(with_cover=True)
                message = f"今日日记页面已创建！页面ID: {result['id'][:8]}..."
            except Exception as e:
                message = f"创建今日日记失败: {str(e)}"
        else:
            # 获取页面内容
            try:
                page_content = notion_service.get_page_children(today_page["id"])
                blocks = page_content.get("results", [])

                if blocks:
                    # 处理页面内容并转换为文本
                    content_text = process_notion_blocks(blocks)
                    message = f"📅 今日日记内容:\n\n{content_text}"
                else:
                    message = "今日日记页面为空，快去添加一些内容吧！"

            except Exception as e:
                message = f"获取日记内容失败: {str(e)}"

        # 发送消息到群
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, message)

    except Exception as e:
        error_msg = f"处理每日命令时出错: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_add_daily_command(event_data):
    """处理 #add_daily 命令，创建今日日记页面"""
    try:
        # 检查今日页面是否已存在
        today_page = daily_manager.get_today_page()

        if today_page:
            message = "今日日记页面已存在！"
        else:
            # 创建今日页面
            result = daily_manager.add_today_page(with_cover=True)
            message = f"✅ 今日日记页面创建成功！\n页面ID: {result['id'][:8]}..."

        # 发送消息到群
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, message)

    except Exception as e:
        error_msg = f"创建今日日记失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_update_cover_command(event_data):
    """处理 #update_cover 命令，更新今日封面"""
    try:
        success = daily_manager.update_daily_cover()

        if success:
            message = "✅ 今日日记封面已更新为最新Bing壁纸！"
        else:
            message = "❌ 更新封面失败，请确保今日日记页面存在"

        # 发送消息到群
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, message)

    except Exception as e:
        error_msg = f"更新封面失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)




def handle_notion_command(event_data):
    """处理所有 Notion 相关命令的主入口"""
    message_text = event_data.get('message', '')

    if message_text.startswith('#daily'):
        handle_daily_command(event_data)
    elif message_text.startswith('#add_daily'):
        handle_add_daily_command(event_data)
    elif message_text.startswith('#update_cover'):
        handle_update_cover_command(event_data)
    else:
        # 未知命令
        group_id = event_data.get('group_id')
        if group_id:
            help_msg = (
                "📖 Notion 相关命令:\n\n"
                "🗓️ 日记功能:\n"
                "#daily - 查看今日日记内容\n"
                "#add_daily - 创建今日日记页面\n"
                "#update_cover - 更新今日日记封面为Bing壁纸"
            )
            send_group_message(group_id, help_msg)