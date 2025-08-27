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


def handle_machine_add_command(event_data):
    """处理 #machine_add 命令，添加新机器"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_add '):
            send_group_message(group_id, "格式错误，请使用: #machine_add <机器名|地域|维度|坐标|产物|维护者>")
            return

        params_text = message_text[13:].strip()
        if not params_text:
            send_group_message(group_id, "请提供机器信息，格式: 机器名|地域|维度|坐标|产物|维护者")
            return

        # 解析参数
        parts = params_text.split('|')
        if len(parts) < 4:
            send_group_message(group_id, "参数不足，至少需要: 机器名|地域|维度|坐标")
            return

        machine_data = {
            'name': parts[0].strip(),
            'region': parts[1].strip() if len(parts) > 1 else '',
            'dimension': parts[2].strip() if len(parts) > 2 else '',
            'coordinates': parts[3].strip() if len(parts) > 3 else '',
        }

        # 处理产物
        if len(parts) > 4 and parts[4].strip():
            machine_data['products'] = [p.strip() for p in parts[4].split(',') if p.strip()]

        # 处理维护者
        if len(parts) > 5 and parts[5].strip():
            machine_data['maintainers'] = [m.strip() for m in parts[5].split(',') if m.strip()]

        # 添加机器
        success = machine_manager.add_machine(machine_data)

        if success:
            response = f"✅ 机器 '{machine_data['name']}' 添加成功！\n\n"
            response += f"🏭 地域: {machine_data['region']}\n"
            response += f"🌍 位置: {machine_data['dimension']} {machine_data['coordinates']}\n"
            if machine_data.get('products'):
                response += f"📦 产物: {', '.join(machine_data['products'])}\n"
            if machine_data.get('maintainers'):
                response += f"👤 维护者: {', '.join(machine_data['maintainers'])}"
            send_group_message(group_id, response)
        else:
            send_group_message(group_id, f"❌ 添加机器 '{machine_data['name']}' 失败")

    except Exception as e:
        error_msg = f"添加机器失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_update_command(event_data):
    """处理 #machine_update 命令，更新机器信息"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_update '):
            send_group_message(group_id, "格式错误，请使用: #machine_update <机器名|字段:值|字段:值...>")
            return

        params_text = message_text[16:].strip()
        if not params_text:
            send_group_message(group_id, "请提供机器名称和更新信息，格式: 机器名|字段:值|字段:值...")
            return

        # 解析参数
        parts = params_text.split('|')
        if len(parts) < 2:
            send_group_message(group_id, "参数不足，请提供机器名和至少一个更新字段")
            return

        machine_name = parts[0].strip()
        update_data = {}

        for part in parts[1:]:
            if ':' in part:
                field, value = part.split(':', 1)
                field = field.strip()
                value = value.strip()

                if field in ['products', 'maintainers']:
                    update_data[field] = [item.strip() for item in value.split(',') if item.strip()]
                else:
                    update_data[field] = value

        if not update_data:
            send_group_message(group_id, "未找到有效的更新字段")
            return

        # 更新机器
        success = machine_manager.update_machine_by_name(machine_name, update_data)

        if success:
            response = f"✅ 机器 '{machine_name}' 更新成功！\n\n"
            for field, value in update_data.items():
                if isinstance(value, list):
                    response += f"{field}: {', '.join(value)}\n"
                else:
                    response += f"{field}: {value}\n"
            send_group_message(group_id, response)
        else:
            send_group_message(group_id, f"❌ 更新机器 '{machine_name}' 失败，请检查机器名是否正确")

    except Exception as e:
        error_msg = f"更新机器失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_delete_command(event_data):
    """处理 #machine_delete 命令，删除机器"""
    try:
        message_text = event_data.get('message', '')
        group_id = event_data.get('group_id')

        if not message_text.startswith('#machine_delete '):
            send_group_message(group_id, "格式错误，请使用: #machine_delete <机器名>")
            return

        machine_name = message_text[16:].strip()
        if not machine_name:
            send_group_message(group_id, "请指定要删除的机器名称")
            return

        # 确认机器存在
        machine = machine_manager.get_machine_details(machine_name)
        if not machine:
            send_group_message(group_id, f"未找到机器: {machine_name}")
            return

        # 删除机器
        success = machine_manager.delete_machine_by_name(machine_name)

        if success:
            send_group_message(group_id, f"✅ 机器 '{machine_name}' 已删除")
        else:
            send_group_message(group_id, f"❌ 删除机器 '{machine_name}' 失败")

    except Exception as e:
        error_msg = f"删除机器失败: {str(e)}"
        print(error_msg)
        group_id = event_data.get('group_id')
        if group_id:
            send_group_message(group_id, error_msg)


def handle_machine_help_command(event_data):
    """处理 #machine_help 命令，显示机器管理帮助"""
    try:
        group_id = event_data.get('group_id')
        help_msg = (
            "🏭 机器信息管理帮助:\n\n"
            "📊 查询功能:\n"
            "#machine_search <产物> - 根据产物查询机器\n"
            "#machine_region <地域> - 根据地域查询机器\n"
            "#machine_regions - 列出所有地域\n"
            "#machine_products - 列出所有产物\n"
            "#machine_detail <机器名> - 获取机器详细信息\n\n"
            "✏️ 编辑功能:\n"
            "#machine_add <机器名|地域|维度|坐标|产物|维护者> - 添加新机器\n"
            "  例: #machine_add 测试机器|测试区|overworld|100,200|铁,铜|张三,李四\n\n"
            "#machine_update <机器名|字段:值|字段:值...> - 更新机器信息\n"
            "  可更新字段: name, region, dimension, coordinates, products, maintainers\n"
            "  例: #machine_update 测试机器|region:新区|products:金,银\n\n"
            "#machine_delete <机器名> - 删除机器\n"
            "  例: #machine_delete 测试机器\n\n"
            "#machine_help - 显示此帮助信息"
        )
        send_group_message(group_id, help_msg)

    except Exception as e:
        error_msg = f"显示帮助失败: {str(e)}"
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
    elif message_text.startswith('#machine_regions'):
        handle_machine_list_regions_command(event_data)
    elif message_text.startswith('#machine_region'):
        handle_machine_region_command(event_data)
    elif message_text.startswith('#machine_products'):
        handle_machine_list_products_command(event_data)
    elif message_text.startswith('#machine_detail'):
        handle_machine_detail_command(event_data)
    elif message_text.startswith('#machine_add'):
        handle_machine_add_command(event_data)
    elif message_text.startswith('#machine_update'):
        handle_machine_update_command(event_data)
    elif message_text.startswith('#machine_delete'):
        handle_machine_delete_command(event_data)
    elif message_text.startswith('#machine_help'):
        handle_machine_help_command(event_data)
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
                "🏭 机器管理:\n"
                "#machine_search <产物> - 根据产物查询机器\n"
                "#machine_region <地域> - 根据地域查询机器\n"
                "#machine_regions - 列出所有地域\n"
                "#machine_products - 列出所有产物\n"
                "#machine_detail <机器名> - 获取机器详细信息\n"
                "#machine_add <参数> - 添加新机器\n"
                "#machine_update <参数> - 更新机器信息\n"
                "#machine_delete <机器名> - 删除机器\n"
                "#machine_help - 显示机器管理帮助"
            )
            send_group_message(group_id, help_msg)