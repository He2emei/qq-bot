# utils/image_utils.py
import os
import requests
import hashlib
import time
import re
from urllib.parse import urlparse
from typing import Optional, List
import config


class ImageManager:
    """图片管理器，负责下载、存储和管理FAQ图片"""

    def __init__(self, storage_dir: str = "data/faq_images"):
        self.storage_dir = storage_dir
        # 确保存储目录存在
        os.makedirs(storage_dir, exist_ok=True)

    def _get_image_hash(self, url: str) -> str:
        """根据URL生成图片的哈希值作为文件名"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_image_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """获取图片的扩展名"""
        # 尝试从URL中提取扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()

        # 常见的图片扩展名
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

        for ext in image_extensions:
            if path.endswith(ext):
                return ext

        # 如果URL中没有扩展名，根据Content-Type判断
        if content_type:
            content_type = content_type.lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                return '.jpg'
            elif 'png' in content_type:
                return '.png'
            elif 'gif' in content_type:
                return '.gif'
            elif 'bmp' in content_type:
                return '.bmp'
            elif 'webp' in content_type:
                return '.webp'

        # 默认使用jpg
        return '.jpg'

    def download_image(self, url: str) -> Optional[str]:
        """下载图片并保存到本地，返回本地文件路径"""
        try:
            # 生成文件名
            url_hash = self._get_image_hash(url)
            filename = f"{url_hash}"

            # 检查文件是否已存在
            existing_files = [f for f in os.listdir(self.storage_dir) if f.startswith(url_hash)]
            if existing_files:
                # 如果文件已存在，直接返回路径
                return os.path.join(self.storage_dir, existing_files[0])

            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()

            # 获取文件扩展名
            content_type = response.headers.get('content-type', '')
            extension = self._get_image_extension(url, content_type)
            filename = f"{url_hash}{extension}"

            # 保存文件
            file_path = os.path.join(self.storage_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"图片已保存: {file_path}")
            return file_path

        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
            return None

    def extract_image_urls(self, content: str) -> List[str]:
        """从内容中提取所有的图片URL"""
        # 匹配CQ码中的图片URL
        cq_pattern = r'\[CQ:image,url=([^\]]+)\]'
        cq_urls = re.findall(cq_pattern, content)

        # 匹配普通图片URL
        url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'
        normal_urls = re.findall(url_pattern, content)

        # 合并并去重
        all_urls = cq_urls + normal_urls
        return list(set(all_urls))

    def process_content_images(self, content: str) -> str:
        """处理内容中的图片，将URL替换为本地路径"""
        # 找到所有的图片URL
        image_urls = self.extract_image_urls(content)

        processed_content = content

        for url in image_urls:
            # 下载图片
            local_path = self.download_image(url)
            if local_path:
                # 将URL替换为本地路径的CQ码
                local_cq_code = f"[CQ:image,file=file://{os.path.abspath(local_path)}]"
                # 替换CQ码格式的URL
                processed_content = processed_content.replace(
                    f"[CQ:image,url={url}]",
                    local_cq_code
                )
                # 替换普通URL
                processed_content = processed_content.replace(url, local_cq_code)

        return processed_content

    def cleanup_old_images(self, days: int = 30):
        """清理旧的图片文件（超过指定天数的）"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)

            cleaned_count = 0
            for filename in os.listdir(self.storage_dir):
                file_path = os.path.join(self.storage_dir, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"清理旧图片: {filename}")

            if cleaned_count > 0:
                print(f"共清理了 {cleaned_count} 个旧图片文件")

        except Exception as e:
            print(f"清理图片失败: {e}")


# 全局图片管理器实例
image_manager = ImageManager()