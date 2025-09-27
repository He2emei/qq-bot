# utils/image_utils.py
import os
import hashlib
import requests
import re
from typing import List, Optional
from datetime import datetime, timedelta
import config

class ImageManager:
    """FAQ图片管理器，负责下载和处理图片"""

    def __init__(self, images_dir: str = None):
        self.images_dir = images_dir or config.FAQ_IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

    def _get_md5_hash(self, url: str) -> str:
        """根据URL生成MD5哈希"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_image_extension(self, url: str) -> str:
        """从URL中提取图片扩展名"""
        # 支持的格式
        supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        url_lower = url.lower()

        for fmt in supported_formats:
            if fmt in url_lower:
                return '.' + fmt

        # 默认使用jpg
        return '.jpg'

    def download_image(self, url: str) -> Optional[str]:
        """下载图片并返回本地文件路径"""
        try:
            # 生成文件名
            md5_hash = self._get_md5_hash(url)
            extension = self._get_image_extension(url)
            filename = md5_hash + extension
            filepath = os.path.join(self.images_dir, filename)

            # 如果文件已存在，直接返回
            if os.path.exists(filepath):
                return filepath

            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 保存到本地
            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filepath

        except Exception as e:
            print(f"下载图片失败: {url} - {e}")
            return None

    def extract_image_urls(self, content: str) -> List[str]:
        """从内容中提取图片URL"""
        # 匹配[CQ:image,url=...]格式
        pattern = r'\[CQ:image,url=([^\]]+)\]'
        matches = re.findall(pattern, content)
        return matches

    def process_content_images(self, content: str) -> str:
        """处理内容中的图片，将URL替换为本地CQ码"""
        image_urls = self.extract_image_urls(content)

        for url in image_urls:
            local_path = self.download_image(url)
            if local_path:
                # 获取相对路径用于CQ码
                rel_path = os.path.relpath(local_path, start=os.getcwd())
                # 替换为本地文件CQ码
                cq_code = f"[CQ:image,file=file:///{rel_path}]"
                content = content.replace(f"[CQ:image,url={url}]", cq_code)

        return content

    def cleanup_old_images(self, days: int = 30):
        """清理旧图片文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            removed_count = 0

            for filename in os.listdir(self.images_dir):
                filepath = os.path.join(self.images_dir, filename)
                if os.path.isfile(filepath):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime < cutoff_date:
                        os.remove(filepath)
                        removed_count += 1

            print(f"清理了 {removed_count} 个旧图片文件")
            return removed_count

        except Exception as e:
            print(f"清理图片失败: {e}")
            return 0

# 全局图片管理器实例
image_manager = ImageManager()