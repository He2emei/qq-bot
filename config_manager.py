# config_manager.py - 配置文件管理器
import os
import json
import logging
from typing import Dict, Any, Optional
from utils.file_utils import load_json, dump_json

class ConfigManager:
    """
    配置文件管理器

    用于管理敏感配置文件的创建、加载和更新，避免git冲突。
    敏感配置文件会被排除在git跟踪之外。
    """

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.sensitive_configs = {
            'authenticatorList': 'authenticatorList.json',
            'code': 'code.json',
            'ze_account': 'ze_account.json',
            'memory': 'memory.json'
        }
        self.logger = logging.getLogger(__name__)

    def init_sensitive_config(self, config_type: str, template_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化敏感配置文件

        Args:
            config_type: 配置类型 ('authenticatorList', 'code', 'ze_account', 'memory')
            template_data: 模板数据，如果不提供则使用默认模板

        Returns:
            bool: 是否成功初始化
        """
        if config_type not in self.sensitive_configs:
            self.logger.error(f"未知的配置类型: {config_type}")
            return False

        config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])

        # 检查文件是否已存在
        if os.path.exists(config_path):
            self.logger.info(f"配置文件 {config_path} 已存在，跳过初始化")
            return True

        # 使用模板数据或默认数据
        if template_data:
            config_data = template_data
        else:
            config_data = self._get_default_template(config_type)

        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)

            # 创建配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功创建敏感配置文件: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"创建配置文件失败: {e}")
            return False

    def _get_default_template(self, config_type: str) -> Dict[str, Any]:
        """获取默认配置模板"""
        templates = {
            'authenticatorList': {
                "version": "1.0.0",
                "list": []
            },
            'code': {},
            'ze_account': {},
            'memory': {
                "last_answer_content": [],
                "last_answer_content_v3": []
            }
        }
        return templates.get(config_type, {})

    def load_sensitive_config(self, config_type: str) -> Dict[str, Any]:
        """
        加载敏感配置文件

        Args:
            config_type: 配置类型

        Returns:
            Dict[str, Any]: 配置数据
        """
        if config_type not in self.sensitive_configs:
            self.logger.error(f"未知的配置类型: {config_type}")
            return {}

        config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])

        # 如果文件不存在，尝试初始化
        if not os.path.exists(config_path):
            self.logger.warning(f"配置文件 {config_path} 不存在，尝试创建默认配置")
            if not self.init_sensitive_config(config_type):
                return {}

        try:
            return load_json(config_path)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return {}

    def save_sensitive_config(self, config_type: str, data: Dict[str, Any]) -> bool:
        """
        保存敏感配置文件

        Args:
            config_type: 配置类型
            data: 配置数据

        Returns:
            bool: 是否保存成功
        """
        if config_type not in self.sensitive_configs:
            self.logger.error(f"未知的配置类型: {config_type}")
            return False

        config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])

        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)

            # 保存配置
            dump_json(config_path, data)
            self.logger.info(f"成功保存配置文件: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def backup_config(self, config_type: str, backup_suffix: str = ".backup") -> bool:
        """
        备份配置文件

        Args:
            config_type: 配置类型
            backup_suffix: 备份文件后缀

        Returns:
            bool: 是否备份成功
        """
        if config_type not in self.sensitive_configs:
            return False

        config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])
        backup_path = config_path + backup_suffix

        try:
            if os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, backup_path)
                self.logger.info(f"成功备份配置文件: {backup_path}")
                return True
        except Exception as e:
            self.logger.error(f"备份配置文件失败: {e}")

        return False

    def restore_config(self, config_type: str, backup_suffix: str = ".backup") -> bool:
        """
        恢复配置文件

        Args:
            config_type: 配置类型
            backup_suffix: 备份文件后缀

        Returns:
            bool: 是否恢复成功
        """
        if config_type not in self.sensitive_configs:
            return False

        config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])
        backup_path = config_path + backup_suffix

        try:
            if os.path.exists(backup_path):
                import shutil
                shutil.copy2(backup_path, config_path)
                self.logger.info(f"成功恢复配置文件: {config_path}")
                return True
        except Exception as e:
            self.logger.error(f"恢复配置文件失败: {e}")

        return False

    def list_config_status(self) -> Dict[str, bool]:
        """
        检查所有敏感配置文件的存在状态

        Returns:
            Dict[str, bool]: 配置类型 -> 是否存在的映射
        """
        status = {}
        for config_type in self.sensitive_configs:
            config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])
            status[config_type] = os.path.exists(config_path)
        return status

    def import_qbot_config(self, qbot_path: str, config_type: str) -> bool:
        """
        从QBot文件夹导入配置文件

        Args:
            qbot_path: QBot文件夹路径
            config_type: 配置类型

        Returns:
            bool: 是否导入成功
        """
        if config_type not in self.sensitive_configs:
            self.logger.error(f"未知的配置类型: {config_type}")
            return False

        qbot_config_path = os.path.join(qbot_path, self.sensitive_configs[config_type])
        local_config_path = os.path.join(self.config_dir, self.sensitive_configs[config_type])

        if not os.path.exists(qbot_config_path):
            self.logger.error(f"QBot配置文件不存在: {qbot_config_path}")
            return False

        try:
            # 读取QBot配置
            with open(qbot_config_path, 'r', encoding='utf-8') as f:
                qbot_data = json.load(f)

            # 确保本地目录存在
            os.makedirs(self.config_dir, exist_ok=True)

            # 保存到本地
            with open(local_config_path, 'w', encoding='utf-8') as f:
                json.dump(qbot_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功从QBot导入配置文件: {config_type}")
            return True

        except Exception as e:
            self.logger.error(f"导入QBot配置失败: {e}")
            return False

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def init_all_configs() -> bool:
    """初始化所有敏感配置文件"""
    success = True
    for config_type in config_manager.sensitive_configs:
        if not config_manager.init_sensitive_config(config_type):
            success = False
    return success

def backup_all_configs() -> bool:
    """备份所有敏感配置文件"""
    success = True
    for config_type in config_manager.sensitive_configs:
        if not config_manager.backup_config(config_type):
            success = False
    return success

def import_all_qbot_configs(qbot_path: str = "QBot") -> bool:
    """
    从QBot文件夹导入所有配置文件

    Args:
        qbot_path: QBot文件夹路径，默认为"QBot"

    Returns:
        bool: 是否全部导入成功
    """
    success = True
    for config_type in config_manager.sensitive_configs:
        if not config_manager.import_qbot_config(qbot_path, config_type):
            success = False
    return success

def import_specific_qbot_config(qbot_path: str, config_type: str) -> bool:
    """
    从QBot文件夹导入指定配置文件

    Args:
        qbot_path: QBot文件夹路径
        config_type: 配置类型

    Returns:
        bool: 是否导入成功
    """
    return config_manager.import_qbot_config(qbot_path, config_type)