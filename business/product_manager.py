"""
产品管理器 - 业务逻辑层
管理产品和缺陷类别，支持两层结构
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class ProductManager:
    """产品管理器 - 管理产品和缺陷类别"""

    def __init__(self, config_file='config/products.json'):
        self.config_file = config_file
        self.products = []  # 产品列表
        self.defect_categories = {}  # 缺陷类别字典 {product_id: [categories]}
        self._ensure_config_dir()
        self.load_data()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def load_data(self):
        """加载数据"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = data.get('products', [])
                    self.defect_categories = data.get('defect_categories', {})
            except Exception as e:
                print(f"加载数据失败: {e}")
                self.products = []
                self.defect_categories = {}
        else:
            self.products = []
            self.defect_categories = {}

    def save_data(self):
        """保存数据"""
        try:
            data = {
                'products': self.products,
                'defect_categories': self.defect_categories,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False

    # 产品管理方法
    def add_product(self, name: str, description: str = '', path: str = '') -> bool:
        """添加产品"""
        if self.product_exists(name):
            return False

        product = {
            'id': len(self.products),
            'name': name,
            'description': description,
            'path': path,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.products.append(product)
        self.defect_categories[product['id']] = []
        return self.save_data()

    def update_product(self, product_id: int, name: str, description: str = '', path: str = None) -> bool:
        """更新产品"""
        for product in self.products:
            if product['id'] == product_id:
                if name != product['name'] and self.product_exists(name):
                    return False
                product['name'] = name
                product['description'] = description
                if path is not None:
                    product['path'] = path
                product['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return self.save_data()
        return False

    def delete_product(self, product_id: int) -> bool:
        """删除产品"""
        self.products = [p for p in self.products if p['id'] != product_id]
        if product_id in self.defect_categories:
            del self.defect_categories[product_id]
        return self.save_data()

    def get_products(self) -> List[Dict]:
        """获取所有产品"""
        return self.products.copy()

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """根据ID获取产品"""
        for product in self.products:
            if product['id'] == product_id:
                return product.copy()
        return None

    def product_exists(self, name: str) -> bool:
        """检查产品是否存在"""
        return any(p['name'] == name for p in self.products)

    def get_product_count(self) -> int:
        """获取产品数量"""
        return len(self.products)

    # 缺陷类别管理方法
    def add_defect_category(self, product_id: int, name: str, description: str = '') -> bool:
        """添加缺陷类别"""
        if product_id not in self.defect_categories:
            self.defect_categories[product_id] = []

        if self.defect_category_exists(product_id, name):
            return False

        category = {
            'id': len(self.defect_categories[product_id]),
            'name': name,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.defect_categories[product_id].append(category)
        return self.save_data()

    def update_defect_category(self, product_id: int, category_id: int, name: str, description: str = '') -> bool:
        """更新缺陷类别"""
        if product_id not in self.defect_categories:
            return False

        for cat in self.defect_categories[product_id]:
            if cat['id'] == category_id:
                if name != cat['name'] and self.defect_category_exists(product_id, name):
                    return False
                cat['name'] = name
                cat['description'] = description
                cat['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return self.save_data()
        return False

    def delete_defect_category(self, product_id: int, category_id: int) -> bool:
        """删除缺陷类别"""
        if product_id not in self.defect_categories:
            return False

        self.defect_categories[product_id] = [
            cat for cat in self.defect_categories[product_id] if cat['id'] != category_id
        ]
        return self.save_data()

    def get_defect_categories(self, product_id: int) -> List[Dict]:
        """获取产品的缺陷类别"""
        return self.defect_categories.get(product_id, []).copy()

    def get_defect_category_names(self, product_id: int) -> List[str]:
        """获取产品的缺陷类别名称"""
        return [cat['name'] for cat in self.defect_categories.get(product_id, [])]

    def defect_category_exists(self, product_id: int, name: str) -> bool:
        """检查缺陷类别是否存在"""
        if product_id not in self.defect_categories:
            return False
        return any(cat['name'] == name for cat in self.defect_categories[product_id])

    def get_defect_category_count(self, product_id: int) -> int:
        """获取产品的缺陷类别数量"""
        return len(self.defect_categories.get(product_id, []))

    # 兼容性方法 - 用于标注工具
    def get_category_names(self) -> List[str]:
        """获取所有缺陷类别名称（用于标注工具）"""
        all_categories = []
        for product_id in self.defect_categories:
            all_categories.extend(self.get_defect_category_names(product_id))
        return all_categories

    def get_category_count(self) -> int:
        """获取所有缺陷类别数量（用于标注工具）"""
        total = 0
        for product_id in self.defect_categories:
            total += len(self.defect_categories[product_id])
        return total

    # 获取产品-缺陷类别映射
    def get_product_defect_mapping(self) -> Dict[str, List[str]]:
        """获取产品-缺陷类别映射"""
        mapping = {}
        for product in self.products:
            product_name = product['name']
            defect_names = self.get_defect_category_names(product['id'])
            mapping[product_name] = defect_names
        return mapping

