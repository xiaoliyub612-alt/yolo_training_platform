"""
类别管理器 - 业务逻辑层
管理产品类别，支持本地JSON存储
"""
import json
import os
from datetime import datetime
from typing import List, Dict


class CategoryManager:
    """类别管理器"""

    def __init__(self, config_file='config/categories.json'):
        self.config_file = config_file
        self.categories = []
        self._ensure_config_dir()
        self.load_categories()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def load_categories(self):
        """加载类别"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', [])
            except Exception as e:
                print(f"加载类别失败: {e}")
                self.categories = []
        else:
            self.categories = []

    def save_categories(self):
        """保存类别"""
        try:
            data = {
                'categories': self.categories,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存类别失败: {e}")
            return False

    def add_category(self, name: str, description: str = '') -> bool:
        """添加类别"""
        if self.category_exists(name):
            return False

        category = {
            'id': len(self.categories),
            'name': name,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.categories.append(category)
        return self.save_categories()

    def update_category(self, category_id: int, name: str, description: str = '') -> bool:
        """更新类别"""
        for cat in self.categories:
            if cat['id'] == category_id:
                # 检查新名称是否与其他类别重复
                if name != cat['name'] and self.category_exists(name):
                    return False
                cat['name'] = name
                cat['description'] = description
                cat['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return self.save_categories()
        return False

    def delete_category(self, category_id: int) -> bool:
        """删除类别"""
        self.categories = [cat for cat in self.categories if cat['id'] != category_id]
        return self.save_categories()

    def get_categories(self) -> List[Dict]:
        """获取所有类别"""
        return self.categories.copy()

    def get_category_names(self) -> List[str]:
        """获取所有类别名称"""
        return [cat['name'] for cat in self.categories]

    def category_exists(self, name: str) -> bool:
        """检查类别是否存在"""
        return any(cat['name'] == name for cat in self.categories)

    def get_category_by_id(self, category_id: int) -> Dict:
        """根据ID获取类别"""
        for cat in self.categories:
            if cat['id'] == category_id:
                return cat.copy()
        return None

    def get_category_count(self) -> int:
        """获取类别数量"""
        return len(self.categories)