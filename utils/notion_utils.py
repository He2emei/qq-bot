# utils/notion_utils.py
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
import json
import os
from .file_utils import load_json, dump_json


def get_bing_image_url() -> str:
    """获取Bing每日壁纸URL"""
    try:
        # 这里使用Bing壁纸API
        url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "images" in data and len(data["images"]) > 0:
            image_url = "https://www.bing.com" + data["images"][0]["url"]
            return image_url
        else:
            # 返回默认图片
            return "https://picsum.photos/800/600?random=1"
    except Exception as e:
        print(f"Error getting Bing image: {e}")
        return "https://picsum.photos/800/600?random=1"


def process_notion_blocks(blocks: list) -> str:
    """处理Notion块内容并转换为文本"""
    text_parts = []

    for block in blocks:
        block_type = block.get("type", "")
        block_content = block.get(block_type, {})

        if block_type == "paragraph":
            paragraph_text = extract_rich_text(block_content.get("rich_text", []))
            if paragraph_text:
                text_parts.append(paragraph_text)

        elif block_type == "heading_1":
            heading_text = extract_rich_text(block_content.get("rich_text", []))
            if heading_text:
                text_parts.append(f"# {heading_text}")

        elif block_type == "heading_2":
            heading_text = extract_rich_text(block_content.get("rich_text", []))
            if heading_text:
                text_parts.append(f"## {heading_text}")

        elif block_type == "heading_3":
            heading_text = extract_rich_text(block_content.get("rich_text", []))
            if heading_text:
                text_parts.append(f"### {heading_text}")

        elif block_type == "bulleted_list_item":
            item_text = extract_rich_text(block_content.get("rich_text", []))
            if item_text:
                text_parts.append(f"• {item_text}")

        elif block_type == "numbered_list_item":
            item_text = extract_rich_text(block_content.get("rich_text", []))
            if item_text:
                text_parts.append(f"1. {item_text}")

        elif block_type == "to_do":
            item_text = extract_rich_text(block_content.get("rich_text", []))
            checked = block_content.get("checked", False)
            checkbox = "☑" if checked else "☐"
            if item_text:
                text_parts.append(f"{checkbox} {item_text}")

        elif block_type == "code":
            code_text = extract_rich_text(block_content.get("rich_text", []))
            language = block_content.get("language", "")
            if code_text:
                text_parts.append(f"```{language}\n{code_text}\n```")

        elif block_type == "quote":
            quote_text = extract_rich_text(block_content.get("rich_text", []))
            if quote_text:
                text_parts.append(f"> {quote_text}")

    return "\n\n".join(text_parts)


def extract_rich_text(rich_text_list: list) -> str:
    """从Notion富文本中提取纯文本"""
    text_parts = []

    for text_item in rich_text_list:
        content = text_item.get("plain_text", "")
        annotations = text_item.get("annotations", {})

        # 应用文本样式
        if annotations.get("bold"):
            content = f"**{content}**"
        if annotations.get("italic"):
            content = f"*{content}*"
        if annotations.get("strikethrough"):
            content = f"~~{content}~~"
        if annotations.get("underline"):
            content = f"<u>{content}</u>"
        if annotations.get("code"):
            content = f"`{content}`"

        text_parts.append(content)

    return "".join(text_parts)


def create_date_filter(target_date: datetime) -> Dict[str, Any]:
    """创建日期过滤器"""
    return {
        "property": "Date",
        "date": {
            "equals": target_date.strftime("%Y-%m-%d")
        }
    }


def create_rich_text_filter(property_name: str, text: str) -> Dict[str, Any]:
    """创建富文本过滤器"""
    return {
        "property": property_name,
        "rich_text": {
            "equals": text
        }
    }


def load_template(template_name: str) -> Dict[str, Any]:
    """加载模板文件"""
    template_path = os.path.join("data", "notion_templates", f"{template_name}.json")
    if os.path.exists(template_path):
        return load_json(template_path)
    else:
        # 返回默认模板
        return {
            "properties": {
                "Date": {"type": "date", "date": {"start": ""}},
                "Name": {"type": "title", "title": []}
            }
        }


def save_template(template_name: str, template_data: Dict[str, Any]):
    """保存模板文件"""
    template_dir = os.path.join("data", "notion_templates")
    os.makedirs(template_dir, exist_ok=True)
    template_path = os.path.join(template_dir, f"{template_name}.json")
    dump_json(template_path, template_data)


# === 完全移植自Notion-Tools项目的学期和时间管理功能 ===

def get_term(dat: datetime = datetime.today()):
    """获取日期对应的学期"""
    # 这里需要导入notion_tools_backup中的函数，或者直接使用已有的服务
    # 由于环境变量加载问题，我们直接使用备份项目的工作代码
    import sys
    import os
    current_dir = os.getcwd()
    backup_dir = os.path.join(current_dir, 'notion_tools_backup')

    try:
        os.chdir(backup_dir)
        sys.path.insert(0, backup_dir)

        from src.sub_operation import get_term as backup_get_term
        result = backup_get_term(dat)

        # 恢复工作目录
        os.chdir(current_dir)
        return result

    except Exception as e:
        print(f"使用备份学期系统失败: {e}")
        # 恢复工作目录
        try:
            os.chdir(current_dir)
        except:
            pass
        return {}
    finally:
        # 确保清理路径
        if backup_dir in sys.path:
            sys.path.remove(backup_dir)


def get_week_num(dat: datetime = datetime.today()) -> int:
    """获取日期在学期中的周编号"""
    import sys
    import os
    current_dir = os.getcwd()
    backup_dir = os.path.join(current_dir, 'notion_tools_backup')

    try:
        os.chdir(backup_dir)
        sys.path.insert(0, backup_dir)

        from src.sub_operation import get_week_num as backup_get_week_num
        result = backup_get_week_num(dat)

        # 恢复工作目录
        os.chdir(current_dir)
        return result

    except Exception as e:
        print(f"使用备份周数计算失败: {e}")
        # 恢复工作目录
        try:
            os.chdir(current_dir)
        except:
            pass
        return 0
    finally:
        # 确保清理路径
        if backup_dir in sys.path:
            sys.path.remove(backup_dir)


def wk_name(dt: datetime = datetime.today()) -> str:
    """生成周页面名称"""
    import sys
    import os
    current_dir = os.getcwd()
    backup_dir = os.path.join(current_dir, 'notion_tools_backup')

    try:
        os.chdir(backup_dir)
        sys.path.insert(0, backup_dir)

        from src.sub_operation import wk_name as backup_wk_name
        result = backup_wk_name(dt)

        # 恢复工作目录
        os.chdir(current_dir)
        return result

    except Exception as e:
        print(f"使用备份周名称生成失败: {e}")
        # 恢复工作目录
        try:
            os.chdir(current_dir)
        except:
            pass
        return "Week0 Unknown"
    finally:
        # 确保清理路径
        if backup_dir in sys.path:
            sys.path.remove(backup_dir)


def date_btw(dt: datetime, stt: datetime, end: datetime) -> bool:
    """检查日期是否在指定范围内（包含结束日期的前一天）"""
    end = end + timedelta(days=1, seconds=-1)
    return stt <= dt <= end


def certain_weekday(dat: datetime, wkd: int) -> datetime:
    """获取指定日期所在周的第wkd天（0=周一，6=周日）"""
    td = timedelta(days=dat.weekday() - wkd)
    return dat - td