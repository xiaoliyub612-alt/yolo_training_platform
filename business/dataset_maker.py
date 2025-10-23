"""
数据集制作器 - 将labelme标注转换为YOLO格式
"""
import json
import random
import shutil
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np


class DatasetMaker:
    """YOLO数据集制作器"""

    def __init__(self, source_dir: str, output_dir: str, categories: List[str]):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.categories = categories
        self.category_to_id = {cat: idx for idx, cat in enumerate(categories)}

        # 创建目录结构
        self.train_images_dir = self.output_dir / 'images' / 'train'
        self.train_labels_dir = self.output_dir / 'labels' / 'train'
        self.val_images_dir = self.output_dir / 'images' / 'val'
        self.val_labels_dir = self.output_dir / 'labels' / 'val'

    def prepare_dataset(self, train_ratio: float = 0.8) -> Tuple[bool, str]:
        """准备数据集"""
        try:
            # 创建目录
            for dir_path in [self.train_images_dir, self.train_labels_dir,
                             self.val_images_dir, self.val_labels_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)

            # 获取所有标注文件
            json_files = list(self.source_dir.glob("*.json"))
            if not json_files:
                return False, "未找到标注文件"

            # 随机划分训练集和验证集
            random.shuffle(json_files)
            split_idx = int(len(json_files) * train_ratio)
            train_files = json_files[:split_idx]
            val_files = json_files[split_idx:]

            # 处理训练集
            for json_file in train_files:
                self._process_file(json_file, self.train_images_dir, self.train_labels_dir)

            # 处理验证集
            for json_file in val_files:
                self._process_file(json_file, self.val_images_dir, self.val_labels_dir)

            return True, f"成功处理 {len(train_files)} 个训练样本，{len(val_files)} 个验证样本"

        except Exception as e:
            return False, f"准备数据集时出错: {str(e)}"

    def _process_file(self, json_file: Path, image_dir: Path, label_dir: Path):
        """处理单个标注文件"""
        try:
            # 读取JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 查找对应的图像文件
            image_path = json_file.with_suffix('.jpg')
            if not image_path.exists():
                image_path = json_file.with_suffix('.png')
            if not image_path.exists():
                image_path = json_file.with_suffix('.jpeg')
            if not image_path.exists():
                print(f"警告: 找不到图像文件 {json_file.stem}")
                return

            # 复制图像
            shutil.copy(image_path, image_dir / image_path.name)

            # 转换标注
            img_height = data.get('imageHeight', 0)
            img_width = data.get('imageWidth', 0)

            if img_height == 0 or img_width == 0:
                # 尝试从图像文件读取尺寸
                img = cv2.imread(str(image_path))
                if img is not None:
                    img_height, img_width = img.shape[:2]
                else:
                    print(f"警告: 无法获取图像尺寸 {image_path.name}")
                    return

            # 生成YOLO格式标注
            yolo_labels = []
            for shape in data.get('shapes', []):
                label = shape.get('label', '')
                if label not in self.category_to_id:
                    continue

                class_id = self.category_to_id[label]
                shape_type = shape.get('shape_type', 'rectangle')
                points = shape.get('points', [])

                if shape_type == 'rectangle' and len(points) == 2:
                    # 矩形标注
                    x1, y1 = points[0]
                    x2, y2 = points[1]

                    # 转换为YOLO格式 (中心点x, 中心点y, 宽度, 高度)，归一化到0-1
                    x_center = ((x1 + x2) / 2) / img_width
                    y_center = ((y1 + y2) / 2) / img_height
                    width = abs(x2 - x1) / img_width
                    height = abs(y2 - y1) / img_height

                    yolo_labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

                elif shape_type == 'polygon' and len(points) >= 3:
                    # 多边形标注 - 转换为外接矩形
                    points_array = np.array(points)
                    x_min = points_array[:, 0].min()
                    y_min = points_array[:, 1].min()
                    x_max = points_array[:, 0].max()
                    y_max = points_array[:, 1].max()

                    x_center = ((x_min + x_max) / 2) / img_width
                    y_center = ((y_min + y_max) / 2) / img_height
                    width = (x_max - x_min) / img_width
                    height = (y_max - y_min) / img_height

                    yolo_labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            # 保存YOLO标注文件
            label_file = label_dir / f"{image_path.stem}.txt"
            with open(label_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(yolo_labels))

        except Exception as e:
            print(f"处理文件 {json_file.name} 时出错: {str(e)}")

    def convert_to_yolo(self):
        """转换为YOLO格式（已在_process_file中完成）"""
        pass

    def create_yaml_config(self):
        """创建YAML配置文件"""
        yaml_content = f"""# YOLO数据集配置文件
path: {self.output_dir.absolute()}  # 数据集根目录
train: images/train  # 训练集图像目录（相对于path）
val: images/val  # 验证集图像目录（相对于path）

# 类别
nc: {len(self.categories)}  # 类别数量
names: {self.categories}  # 类别名称列表
"""

        yaml_file = self.output_dir / 'data.yaml'
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        print(f"配置文件已保存到: {yaml_file}")