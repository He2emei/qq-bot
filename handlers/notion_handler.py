# handlers/notion_handler.py
import json
from datetime import datetime
from services.notion_service import daily_manager, notion_service
from services.machine_manager import machine_manager
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


def handle_machine_search_command(event_data):
    """处理 #machine_search 命令，根据产物查询机器"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_search '):
            send_group_message(group_id, "格式错误，请使用: #machine_search <产物名称>")
            return

        product = message_text[16:].strip()
        if not product:
            send_group_message(group_id, "请指定要查询的产物名称")
            return

        machines = machine_manager.search_machines_by_product(product)

        if not machines:
            send_group_message(group_id, f"未找到生产 '{product}' 的机器")
            return

        # 构建回复消息
        response = f"🔍 找到 {len(machines)} 台生产 '{product}' 的机器:\n\n"

        for i, machine in enumerate(machines, 1):
            response += f"{i}. {machine['name']}\n"
            response += f"   📍 地域: {machine['region']}\n"
            response += f"   📦 产物: {', '.join(machine['products'])}\n"
            if machine['maintainers']:
                response += f"   👤 维护者: {', '.join(machine['maintainers'])}\n"
            response += f"   🌍 位置: {machine['dimension']} {machine['coordinates']}\n\n"

        # 如果消息太长，分多次发送
        if len(response) > 1000:
            parts = [response[i:i+1000] for i in range(0, len(response), 1000)]
            for part in parts:
                send_group_message(group_id, part)
        else:
            send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"查询机器失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_region_command(event_data):
    """处理 #machine_region 命令，根据地域查询机器"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_region '):
            send_group_message(group_id, "格式错误，请使用: #machine_region <地域名称>")
            return

        region = message_text[16:].strip()
        if not region:
            send_group_message(group_id, "请指定要查询的地域名称")
            return

        machines = machine_manager.search_machines_by_region(region)

        if not machines:
            send_group_message(group_id, f"未找到 '{region}' 地域的机器")
            return

        # 构建回复消息
        response = f"🏭 {region} 地域的机器列表:\n\n"

        for i, machine in enumerate(machines, 1):
            response += f"{i}. {machine['name']}\n"
            response += f"   📦 产物: {', '.join(machine['products'])}\n"
            response += f"   🌍 位置: {machine['dimension']} {machine['coordinates']}\n\n"

        # 如果消息太长，分多次发送
        if len(response) > 1000:
            parts = [response[i:i+1000] for i in range(0, len(response), 1000)]
            for part in parts:
                send_group_message(group_id, part)
        else:
            send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"查询地域机器失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_list_regions_command(event_data):
    """处理 #machine_regions 命令，列出所有地域"""
    try:
        group_id = event_data.get('group_id')
        regions = machine_manager.list_all_regions()

        if not regions:
            send_group_message(group_id, "未找到任何地域信息")
            return

        response = f"🌍 所有可用地域 ({len(regions)} 个):\n\n"
        response += '\n'.join(f"• {region}" for region in regions)

        send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"获取地域列表失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_list_products_command(event_data):
    """处理 #machine_products 命令，列出所有产物"""
    try:
        group_id = event_data.get('group_id')
        products = machine_manager.list_all_products()

        if not products:
            send_group_message(group_id, "未找到任何产物信息")
            return

        response = f"📦 所有可用产物 ({len(products)} 个):\n\n"
        response += '\n'.join(f"• {product}" for product in products)

        send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"获取产物列表失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_detail_command(event_data):
    """处理 #machine_detail 命令，获取机器详细信息"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_detail '):
            send_group_message(group_id, "格式错误，请使用: #machine_detail <机器名称>")
            return

        machine_name = message_text[16:].strip()
        if not machine_name:
            send_group_message(group_id, "请指定要查询的机器名称")
            return

        machine = machine_manager.get_machine_details(machine_name)

        if not machine:
            send_group_message(group_id, f"未找到机器: {machine_name}")
            return

        # 构建详细回复消息
        response = f"📋 机器详细信息: {machine['name']}\n\n"
        response += f"🏭 地域: {machine['region']}\n"
        response += f"📦 产物: {', '.join(machine['products'])}\n"

        if machine['maintainers']:
            response += f"👤 可维护者: {', '.join(machine['maintainers'])}\n"

        response += f"🌍 维度: {machine['dimension']}\n"
        response += f"📍 坐标: {machine['coordinates']}\n"
        response += f"📅 创建时间: {machine['created_time'][:10]}\n"
        response += f"🔄 最后修改: {machine['last_edited_time'][:10]}"

        send_group_message(group_id, response)

    except Exception as e:
        error_msg = f"获取机器详情失败: {str(e)}"
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
    elif message_text.startswith('#machine_search'):
        handle_machine_search_command(event_data)
    elif message_text.startswith('#machine_region'):
        handle_machine_region_command(event_data)
    elif message_text.startswith('#machine_regions'):
        handle_machine_list_regions_command(event_data)
    elif message_text.startswith('#machine_products'):
        handle_machine_list_products_command(event_data)
    elif message_text.startswith('#machine_detail'):
        handle_machine_detail_command(event_data)
    else:
        # 未知命令
        group_id = event_data.get('group_id')
        if group_id:
            help_msg = (
                "📖 Notion 相关命令:\n\n"
                "🗓️ 日记功能:\n"
                "#daily - 查看今日日记内容\n"
                "#add_daily - 创建今日日记页面\n"
                "#update_cover - 更新今日日记封面为Bing壁纸\n\n"
                "🏭 机器查询:\n"
                "#machine_search <产物> - 根据产物查询机器\n"
                "#machine_region <地域> - 根据地域查询机器\n"
                "#machine_regions - 列出所有地域\n"
                "#machine_products - 列出所有产物\n"
                "#machine_detail <机器名> - 获取机器详细信息"
            )
            send_group_message(group_id, help_msg)