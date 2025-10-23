"""
标注界面 - 集成修改后的labelme
"""
import os
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QMessageBox, QFileDialog, QProgressDialog,
                             QLabel)


class DatasetMakerThread(QThread):
    """数据集制作线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_dir, output_dir, categories, train_ratio=0.8):
        super().__init__()
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.categories = categories
        self.train_ratio = train_ratio

    def run(self):
        try:
            from business.dataset_maker import DatasetMaker
            maker = DatasetMaker(self.source_dir, self.output_dir, self.categories)

            self.progress.emit(10, "正在分析标注文件...")
            success, message = maker.prepare_dataset(self.train_ratio)

            if success:
                self.progress.emit(50, "正在生成YOLO格式标注...")
                maker.convert_to_yolo()

                self.progress.emit(80, "正在生成配置文件...")
                maker.create_yaml_config()

                self.progress.emit(100, "数据集制作完成！")
                self.finished.emit(True, f"数据集已保存到: {self.output_dir}")
            else:
                self.finished.emit(False, message)

        except Exception as e:
            self.finished.emit(False, f"制作数据集时出错: {str(e)}")


class LabelWidget(QWidget):
    """标注界面 - 集成labelme"""

    def __init__(self, category_manager):
        super().__init__()
        self.category_manager = category_manager
        self.labelme_window = None
        self.current_dir = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明信息
        info_group = QGroupBox("标注说明")
        info_layout = QVBoxLayout()
        info_text = QLabel(
            "• 点击"
        "打开标注工具"
        "启动图像标注工具\n"
        "• 支持矩形、多边形等多种标注方式\n"
        "• 标注完成后可一键制作YOLO训练数据集\n"
        "• 数据集将自动划分为训练集和验证集"
        )
        info_text.setStyleSheet("color: #7f8c8d; padding: 10px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 标注工具组
        label_group = QGroupBox("标注工具")
        label_layout = QVBoxLayout()

        # 打开标注工具按钮
        self.open_labelme_btn = QPushButton("🏷️ 打开标注工具")
        self.open_labelme_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.open_labelme_btn.clicked.connect(self.open_labelme)
        label_layout.addWidget(self.open_labelme_btn)

        # 当前目录显示
        self.current_dir_label = QLabel("未选择目录")
        self.current_dir_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        label_layout.addWidget(self.current_dir_label)

        label_group.setLayout(label_layout)
        layout.addWidget(label_group)

        # 数据集制作组
        dataset_group = QGroupBox("数据集制作")
        dataset_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()

        # 一键制作数据集按钮
        self.make_dataset_btn = QPushButton("🎯 一键制作YOLO数据集")
        self.make_dataset_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.make_dataset_btn.clicked.connect(self.make_dataset)
        self.make_dataset_btn.setEnabled(False)
        btn_layout.addWidget(self.make_dataset_btn)

        # 选择源目录按钮
        self.select_dir_btn = QPushButton("📁 选择标注目录")
        self.select_dir_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        self.select_dir_btn.clicked.connect(self.select_source_directory)
        btn_layout.addWidget(self.select_dir_btn)

        dataset_layout.addLayout(btn_layout)

        # 数据集信息
        self.dataset_info_label = QLabel("请先选择包含标注文件的目录")
        self.dataset_info_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        self.dataset_info_label.setWordWrap(True)
        dataset_layout.addWidget(self.dataset_info_label)

        dataset_group.setLayout(dataset_layout)
        layout.addWidget(dataset_group)

        # 帮助信息
        help_group = QGroupBox("使用提示")
        help_layout = QVBoxLayout()
        help_text = QLabel(
            "<b>标注流程：</b><br>"
            "1. 在"
        '类别管理'
        "页面添加需要检测的目标类别<br>"
        "2. 点击"
       '打开标注工具'
        "，选择图像目录开始标注<br>"
        "3. 使用矩形工具框选目标，选择对应类别<br>"
        "4. 标注完成后，选择标注目录，点击"
        '一键制作YOLO数据集'
        "<br>"
        "5. 数据集将自动生成YOLO格式的训练文件和配置"
        )
        help_text.setStyleSheet("color: #34495e; padding: 10px; line-height: 1.6;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)

        layout.addStretch()

    def open_labelme(self):
        """打开labelme标注工具"""
        try:
            # 检查是否有类别
            if self.category_manager.get_category_count() == 0:
                QMessageBox.warning(
                    self, "警告",
                    "请先在"
                '类别管理'
                "页面添加至少一个类别！"
                )
                return

            # 导入修改后的labelme
            from labelme_modified.labelme_app import LabelmeMainWindow

            # 获取类别列表
            labels = self.category_manager.get_category_names()

            # 创建labelme窗口
            if self.labelme_window is None or not self.labelme_window.isVisible():
                # 创建配置
                config = {
                    'labels': labels,
                    'sort_labels': True,
                    'show_label_text_field': True,
                    'label_completion': 'startswith',
                    'fit_to_content': {'column': True, 'row': False},
                    'label_flags': {},
                    'flags': {},
                    'epsilon': 10.0,
                    'canvas': {
                        'double_click': 'close',
                        'num_backups': 10,
                        'crosshair': True,
                        'fill_drawing': False
                    },
                    'keep_prev': False,
                    'keep_prev_scale': False,
                    'keep_prev_brightness_contrast': False,
                    'auto_save': True,
                    'store_data': False,
                    'validate_label': None,
                    'shape_color': 'auto',
                    'shift_auto_shape_color': 0,
                    'label_colors': {},
                    'default_shape_color': None,
                    'display_label_popup': True,
                    'file_search': None,
                    'shortcuts': {
                        'quit': 'Ctrl+Q',
                        'open': 'Ctrl+O',
                        'open_dir': 'Ctrl+D',
                        'open_next': 'D',
                        'open_prev': 'A',
                        'save': 'Ctrl+S',
                        'save_as': 'Ctrl+Shift+S',
                        'close': 'Ctrl+W',
                        'delete_file': 'Ctrl+Delete',
                        'save_to': '',
                        'toggle_keep_prev_mode': '',
                        'create_polygon': 'P',
                        'create_rectangle': 'R',
                        'create_circle': '',
                        'create_line': '',
                        'create_point': '',
                        'create_linestrip': '',
                        'edit_polygon': 'E',
                        'delete_polygon': 'Delete',
                        'duplicate_polygon': 'Ctrl+D',
                        'copy_polygon': 'Ctrl+C',
                        'paste_polygon': 'Ctrl+V',
                        'undo_last_point': 'Ctrl+Z',
                        'undo': 'Ctrl+Z',
                        'remove_selected_point': 'Backspace',
                        'hide_all_polygons': '',
                        'show_all_polygons': '',
                        'toggle_all_polygons': '',
                        'zoom_in': 'Ctrl++',
                        'zoom_out': 'Ctrl+-',
                        'zoom_to_original': 'Ctrl+0',
                        'fit_window': 'Ctrl+F',
                        'fit_width': 'Ctrl+Shift+F',
                        'edit_label': 'Ctrl+E'
                    },
                    'shape': {
                        'line_color': [0, 255, 0, 128],
                        'fill_color': [0, 255, 0, 100],
                        'select_line_color': [255, 255, 255, 255],
                        'select_fill_color': [0, 255, 0, 155],
                        'vertex_fill_color': [0, 255, 0, 255],
                        'hvertex_fill_color': [255, 255, 255, 255],
                        'point_size': 8
                    },
                    'flag_dock': {
                        'show': False,
                        'closable': True,
                        'floatable': True,
                        'movable': True
                    },
                    'label_dock': {
                        'show': True,
                        'closable': True,
                        'floatable': True,
                        'movable': True
                    },
                    'shape_dock': {
                        'show': True,
                        'closable': True,
                        'floatable': True,
                        'movable': True
                    },
                    'file_dock': {
                        'show': True,
                        'closable': True,
                        'floatable': True,
                        'movable': True
                    },
                    'ai': {
                        'default': 'Sam2 (balanced)'
                    }
                }

                self.labelme_window = LabelmeMainWindow(config=config)
                self.labelme_window.show()
            else:
                self.labelme_window.raise_()
                self.labelme_window.activateWindow()

        except ImportError:
            QMessageBox.critical(
                self, "错误",
                "无法导入labelme模块！\n请确保已安装labelme：\npip install labelme"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"打开标注工具时出错：\n{str(e)}"
            )

    def select_source_directory(self):
        """选择标注源目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择标注目录",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.current_dir = directory
            self.current_dir_label.setText(f"当前目录: {directory}")

            # 统计标注文件
            json_files = list(Path(directory).glob("*.json"))
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                image_files.extend(list(Path(directory).glob(f"*{ext}")))

            self.dataset_info_label.setText(
                f"找到 {len(image_files)} 张图像，{len(json_files)} 个标注文件"
            )

            # 启用制作数据集按钮
            if len(json_files) > 0:
                self.make_dataset_btn.setEnabled(True)
            else:
                self.make_dataset_btn.setEnabled(False)
                QMessageBox.warning(
                    self, "警告",
                    "该目录下没有找到标注文件(.json)！"
                )

    def make_dataset(self):
        """制作YOLO数据集"""
        if not self.current_dir:
            self.select_source_directory()
            if not self.current_dir:
                return

        # 检查类别
        if self.category_manager.get_category_count() == 0:
            QMessageBox.warning(
                self, "警告",
                "请先在"
            '类别管理'
            "页面添加类别！"
            )
            return

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择数据集输出目录",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )

        if not output_dir:
            return

        # 确认覆盖
        if os.path.exists(output_dir) and os.listdir(output_dir):
            reply = QMessageBox.question(
                self, '确认',
                '输出目录不为空，是否继续？\n这可能会覆盖现有文件。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # 创建进度对话框
        progress = QProgressDialog("正在制作数据集...", "取消", 0, 100, self)
        progress.setWindowTitle("制作数据集")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 创建线程
        categories = self.category_manager.get_category_names()
        self.maker_thread = DatasetMakerThread(
            self.current_dir, output_dir, categories, train_ratio=0.8
        )

        # 连接信号
        self.maker_thread.progress.connect(
            lambda val, msg: (progress.setValue(val), progress.setLabelText(msg))
        )
        self.maker_thread.finished.connect(
            lambda success, msg: self.on_dataset_finished(success, msg, progress)
        )

        # 启动线程
        self.maker_thread.start()

    def on_dataset_finished(self, success, message, progress):
        """数据集制作完成"""
        progress.close()

        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "失败", message)