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