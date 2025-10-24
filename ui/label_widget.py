"""
标注界面 - 集成修改后的 labelme，并提供数据集制作入口
"""
import os
import json
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QProgressDialog,
    QLabel,
    QApplication,
    QLineEdit,
    QSlider,
    QDialog,
    QTabWidget,
    QScrollArea,
)


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

            self.progress.emit(10, "正在分析标注文件……")
            success, message = maker.prepare_dataset(self.train_ratio)

            if success:
                self.progress.emit(50, "正在生成 YOLO 格式标注……")
                maker.convert_to_yolo()

                self.progress.emit(80, "正在生成配置文件……")
                maker.create_yaml_config()

                self.progress.emit(100, "数据集制作完成！")
                self.finished.emit(True, f"数据集已保存到：{self.output_dir}")
            else:
                self.finished.emit(False, message)

        except Exception as e:
            self.finished.emit(False, f"制作数据集时出错：{str(e)}")


class LabelWidget(QWidget):
    """标注界面 - 集成 labelme"""

    def __init__(self, product_manager):
        super().__init__()
        self.product_manager = product_manager
        self.labelme_window = None
        self.current_dir = None
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 说明信息（默认隐藏）
        info_group = QGroupBox("标注说明")
        info_layout = QVBoxLayout()
        info_text = QLabel(
            "• 点击“打开标注工具”启动图像标注\n"
            "• 支持矩形、多边形等多种标注方式\n"
            "• 标注完成后可一键制作 YOLO 训练数据集\n"
            "• 数据集将自动划分为训练集和验证集"
        )
        info_text.setStyleSheet("color: #7f8c8d; padding: 10px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        self.info_group = info_group
        self.info_group.setVisible(False)
        self.info_group.setMaximumHeight(140)

        # 标注工具
        label_group = QGroupBox("标注工具")
        label_layout = QVBoxLayout()

        # 打开标注工具按钮
        self.open_labelme_btn = QPushButton("打开标注工具")
        self.open_labelme_btn.setStyleSheet(
            """
            QPushButton {
                background: #3498db;
                color: #ffffff;
                border: none;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
            """
        )
        self.open_labelme_btn.clicked.connect(self.open_labelme)
        label_layout.addWidget(self.open_labelme_btn)

        # 同步类别按钮
        self.sync_labels_btn = QPushButton("从标注同步类别到产品")
        self.sync_labels_btn.setStyleSheet(
            """
            QPushButton {
                background: #f39c12;
                color: #ffffff;
                border: none;
                padding: 10px 14px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #e67e22; }
            """
        )
        self.sync_labels_btn.clicked.connect(self.sync_labels_to_product)
        label_layout.addWidget(self.sync_labels_btn)

        label_group.setLayout(label_layout)
        layout.addWidget(label_group)

        # 顶部帮助开关与对话框按钮
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()

        self.toggle_help_btn = QPushButton("显示帮助")
        self.toggle_help_btn.setStyleSheet(
            """
            QPushButton {
                background: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #d0d7de;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e6ebef; }
            """
        )
        self.toggle_help_btn.setMaximumWidth(120)
        self.toggle_help_btn.clicked.connect(self.toggle_help_sections)
        toggle_layout.addWidget(self.toggle_help_btn)

        self.help_dialog_btn = QPushButton("帮助")
        self.help_dialog_btn.setStyleSheet(
            """
            QPushButton {
                background: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #d0d7de;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e6ebef; }
            """
        )
        self.help_dialog_btn.setMaximumWidth(90)
        self.help_dialog_btn.clicked.connect(self.show_help_dialog)
        toggle_layout.addWidget(self.help_dialog_btn)

        layout.addLayout(toggle_layout)

        # 数据集制作组
        dataset_group = QGroupBox("数据集制作")
        dataset_layout = QVBoxLayout()

        # 标注源目录
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("标注目录:"))
        self.source_dir_edit = QLineEdit()
        self.source_dir_edit.setPlaceholderText("选择包含标注文件的目录")
        self.source_dir_edit.setReadOnly(True)
        source_layout.addWidget(self.source_dir_edit)

        self.select_dir_btn = QPushButton("浏览")
        self.select_dir_btn.setStyleSheet(
            """
            QPushButton {
                background: #9b59b6;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background: #8e44ad; }
            """
        )
        self.select_dir_btn.setMaximumWidth(80)
        self.select_dir_btn.clicked.connect(self.select_source_directory)
        source_layout.addWidget(self.select_dir_btn)
        dataset_layout.addLayout(source_layout)

        # 输出目录
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("数据集输出目录（默认为标注目录的父目录）")
        output_layout.addWidget(self.output_dir_edit)

        # 重置为父目录按钮
        self.reset_parent_btn = QPushButton("设为父目录")
        self.reset_parent_btn.setToolTip("将输出目录重置为标注目录的父目录")
        self.reset_parent_btn.setMaximumWidth(90)
        self.reset_parent_btn.clicked.connect(self.reset_output_to_parent)
        output_layout.addWidget(self.reset_parent_btn)

        self.select_output_btn = QPushButton("浏览")
        self.select_output_btn.setStyleSheet(
            """
            QPushButton {
                background: #9b59b6;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background: #8e44ad; }
            """
        )
        self.select_output_btn.setMaximumWidth(80)
        self.select_output_btn.clicked.connect(self.select_output_directory)
        output_layout.addWidget(self.select_output_btn)
        dataset_layout.addLayout(output_layout)

        # 训练集比例
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("训练集比例:"))
        self.train_ratio_slider = QSlider(Qt.Horizontal)
        self.train_ratio_slider.setRange(50, 95)
        self.train_ratio_slider.setValue(80)
        self.train_ratio_slider.setTickPosition(QSlider.TicksBelow)
        self.train_ratio_slider.setTickInterval(5)
        self.train_ratio_slider.valueChanged.connect(self.update_ratio_label)
        ratio_layout.addWidget(self.train_ratio_slider)

        self.ratio_label = QLabel("80%")
        self.ratio_label.setStyleSheet("font-weight: bold; color: #2c3e50; min-width: 45px;")
        ratio_layout.addWidget(self.ratio_label)
        dataset_layout.addLayout(ratio_layout)

        # 数据集信息
        self.dataset_info_label = QLabel("请先选择包含标注文件的目录")
        self.dataset_info_label.setStyleSheet(
            "color: #7f8c8d; padding: 8px; background: #ecf0f1; border-radius: 4px;"
        )
        self.dataset_info_label.setWordWrap(True)
        dataset_layout.addWidget(self.dataset_info_label)

        # 一键制作数据集按钮
        self.make_dataset_btn = QPushButton("一键制作 YOLO 数据集")
        self.make_dataset_btn.setStyleSheet(
            """
            QPushButton {
                background: #2ecc71;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #27ae60; }
            QPushButton:disabled { background: #bdc3c7; }
            """
        )
        self.make_dataset_btn.clicked.connect(self.make_dataset)
        self.make_dataset_btn.setEnabled(False)
        dataset_layout.addWidget(self.make_dataset_btn)

        dataset_group.setLayout(dataset_layout)
        layout.addWidget(dataset_group)
        # 让数据集区域获得更多空间
        try:
            layout.setStretch(layout.indexOf(dataset_group), 1)
        except Exception:
            pass

        # 帮助信息（默认隐藏）
        self.help_group = QGroupBox("使用提示")
        help_layout = QVBoxLayout()
        help_text = QLabel(
            "<b>标注流程：</b><br>"
            "1. 在产品管理页面添加产品，然后为每个产品添加缺陷类别<br>"
            "2. 点击打开标注工具，选择图像目录开始标注<br>"
            "3. 使用矩形工具框选缺陷，选择对应的缺陷类别<br>"
            "4. 标注完成后，选择标注目录，点击一键制作 YOLO 数据集<br>"
            "5. 数据集将自动生成 YOLO 格式的训练文件和配置"
        )
        help_text.setStyleSheet("color: #34495e; padding: 10px; line-height: 1.6;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        self.help_group.setLayout(help_layout)
        self.help_group.setVisible(False)
        self.help_group.setMaximumHeight(180)
        layout.addWidget(self.help_group)

        layout.addStretch()

    def reset_output_to_parent(self):
        """将输出目录重置为当前标注目录的父目录"""
        if not self.current_dir:
            QMessageBox.information(self, "提示", "请先选择标注目录。")
            return
        parent_dir = os.path.dirname(self.current_dir)
        if not parent_dir:
            QMessageBox.warning(self, "提示", "无法获取父目录。")
            return
        dataset_name = os.path.basename(self.current_dir) + "_yolo_dataset"
        default_output = os.path.join(parent_dir, dataset_name)
        self.output_dir_edit.setText(default_output)

    def toggle_help_sections(self):
        """切换说明/提示显示，默认隐藏以腾出空间给数据集制作"""
        show = not (self.info_group.isVisible() and self.help_group.isVisible())
        self.info_group.setVisible(show)
        self.help_group.setVisible(show)
        self.toggle_help_btn.setText("隐藏帮助" if show else "显示帮助")

    def show_help_dialog(self):
        """以对话框形式展示说明与使用提示，不占主界面空间"""
        dlg = QDialog(self)
        dlg.setWindowTitle("帮助")
        dlg.resize(560, 420)

        vbox = QVBoxLayout(dlg)
        tabs = QTabWidget(dlg)

        # 标注说明页
        info_area = QScrollArea()
        info_area.setWidgetResizable(True)
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_text = QLabel(
            "• 点击“打开标注工具”启动图像标注\n"
            "• 支持矩形、多边形等多种标注方式\n"
            "• 标注完成后可一键制作 YOLO 训练数据集\n"
            "• 数据集将自动划分为训练集和验证集"
        )
        info_text.setStyleSheet("color: #7f8c8d; padding: 8px; line-height: 1.6;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        info_area.setWidget(info_container)
        tabs.addTab(info_area, "标注说明")

        # 使用提示页
        help_area = QScrollArea()
        help_area.setWidgetResizable(True)
        help_container = QWidget()
        help_layout = QVBoxLayout(help_container)
        help_text = QLabel(
            "<b>标注流程：</b><br>"
            "1. 在产品管理页面添加产品，然后为每个产品添加缺陷类别<br>"
            "2. 点击打开标注工具，选择图像目录开始标注<br>"
            "3. 使用矩形工具框选缺陷，选择对应的缺陷类别<br>"
            "4. 标注完成后，选择标注目录，点击一键制作 YOLO 数据集<br>"
            "5. 数据集将自动生成 YOLO 格式的训练文件和配置"
        )
        help_text.setStyleSheet("color: #34495e; padding: 8px; line-height: 1.6;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        help_layout.addStretch()
        help_area.setWidget(help_container)
        tabs.addTab(help_area, "使用提示")

        vbox.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("关闭", dlg)
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_close)
        vbox.addLayout(btn_row)

        dlg.exec_()

    def open_labelme(self):
        """打开 labelme 标注工具"""
        try:
            # 进度提示
            progress = QProgressDialog("正在启动标注工具……", "取消", 0, 0, self)
            progress.setWindowTitle("启动标注工具")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            # 导入修改后的 labelme 窗口
            from labelme_modified.labelme_app import LabelmeMainWindow

            # 获取缺陷类别列表（允许为空）
            labels = self.product_manager.get_category_names()

            # 创建配置（包含 labelme 需要的必需字段，如 shape）
            config = {
                "labels": labels,
                "sort_labels": True,
                "show_label_text_field": True,
                "label_completion": "startswith",
                "fit_to_content": {"column": True, "row": False},
                # 关闭自动保存，在切换图片时弹出“是否保存”的提醒
                "auto_save": False,
                "store_data": False,
                "validate_label": None,
                "label_flags": {},
                "flags": {},
                "shape_color": "auto",
                "shift_auto_shape_color": 0,
                "label_colors": {},
                "default_shape_color": None,
                "display_label_popup": True,
                "file_search": None,
                "keep_prev": False,
                "keep_prev_scale": False,
                "keep_prev_brightness_contrast": False,
                "epsilon": 10.0,
                "canvas": {
                    "double_click": "close",
                    "num_backups": 10,
                    "crosshair": {
                        "polygon": True,
                        "rectangle": True,
                        "circle": True,
                        "line": True,
                        "point": True,
                        "linestrip": True,
                        "ai_polygon": True,
                        "ai_mask": True,
                    },
                    "fill_drawing": False,
                },
                "flag_dock": {"show": False, "closable": True, "floatable": True, "movable": True},
                "label_dock": {"show": True, "closable": True, "floatable": True, "movable": True},
                "shape_dock": {"show": True, "closable": True, "floatable": True, "movable": True},
                "file_dock": {"show": True, "closable": True, "floatable": True, "movable": True},
                "ai": {"default": "Sam2 (balanced)"},
                "shape": {
                    "line_color": [0, 255, 0, 128],
                    "fill_color": [0, 255, 0, 100],
                    "select_line_color": [255, 255, 255, 255],
                    "select_fill_color": [0, 255, 0, 155],
                    "vertex_fill_color": [0, 255, 0, 255],
                    "hvertex_fill_color": [255, 255, 255, 255],
                    "point_size": 8,
                },
                "shortcuts": {
                    "quit": "Ctrl+Q",
                    "open": "Ctrl+O",
                    "open_dir": "Ctrl+D",
                    "open_next": "D",
                    "open_prev": "A",
                    "save": "Ctrl+S",
                    "save_as": "Ctrl+Shift+S",
                    "close": "Ctrl+W",
                    "delete_file": "Ctrl+Delete",
                    "save_to": "",
                    "toggle_keep_prev_mode": "",
                    "create_polygon": "P",
                    "create_rectangle": "R",
                    "create_circle": "",
                    "create_line": "",
                    "create_point": "",
                    "create_linestrip": "",
                    "edit_polygon": "E",
                    "delete_polygon": "Delete",
                    "duplicate_polygon": "Ctrl+D",
                    "copy_polygon": "Ctrl+C",
                    "paste_polygon": "Ctrl+V",
                    "undo_last_point": "Ctrl+Z",
                    "undo": "Ctrl+Z",
                    "remove_selected_point": "Backspace",
                    "hide_all_polygons": "",
                    "show_all_polygons": "",
                    "toggle_all_polygons": "",
                    "zoom_in": "Ctrl++",
                    "zoom_out": "Ctrl+-",
                    "zoom_to_original": "Ctrl+0",
                    "fit_window": "Ctrl+F",
                    "fit_width": "Ctrl+Shift+F",
                    "edit_label": "Ctrl+E",
                },
            }

            progress.setLabelText("正在初始化标注工具……")
            QApplication.processEvents()

            # 使用 labelme 默认保存策略（JSON 与图像同目录）
            self.labelme_window = LabelmeMainWindow(config=config)

            progress.setLabelText("正在显示标注工具……")
            QApplication.processEvents()

            self.labelme_window.show()
            progress.close()

        except ImportError as e:
            progress.close()
            reply = QMessageBox.question(
                self,
                "labelme 未安装",
                f"无法导入 labelme 模块！\n\n是否要安装 labelme？\n\n错误详情：{str(e)}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                self._install_labelme()
        except Exception as e:
            try:
                progress.close()
            except Exception:
                pass
            QMessageBox.critical(self, "错误", f"打开标注工具时出错：\n{str(e)}\n\n请检查 labelme 是否正确安装。")

    def _install_labelme(self):
        """安装 labelme"""
        try:
            import subprocess
            import sys

            progress = QProgressDialog("正在安装 labelme……", "取消", 0, 0, self)
            progress.setWindowTitle("安装 labelme")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()
            QApplication.processEvents()

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "labelme"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            progress.close()

            if result.returncode == 0:
                QMessageBox.information(self, "安装成功", "labelme 安装成功！\n请重新启动应用程序。")
            else:
                QMessageBox.critical(
                    self,
                    "安装失败",
                    f"labelme 安装失败：\n{result.stderr}\n\n请手动安装：\npip install labelme",
                )

        except subprocess.TimeoutExpired:
            try:
                progress.close()
            except Exception:
                pass
            QMessageBox.critical(self, "安装超时", "安装超时，请手动安装：\npip install labelme")
        except Exception as e:
            try:
                progress.close()
            except Exception:
                pass
            QMessageBox.critical(self, "安装错误", f"安装过程中出错：\n{str(e)}\n\n请手动安装：\npip install labelme")

    def update_ratio_label(self, value):
        """更新训练集比例标签"""
        self.ratio_label.setText(f"{value}%")

    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择数据集输出目录", os.path.expanduser("~"), QFileDialog.ShowDirsOnly
        )
        if directory:
            self.output_dir_edit.setText(directory)

    def select_source_directory(self):
        """选择标注源目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择标注目录", os.path.expanduser("~"), QFileDialog.ShowDirsOnly
        )
        if directory:
            self.current_dir = directory
            self.source_dir_edit.setText(directory)

            # 默认输出目录为父目录
            parent_dir = os.path.dirname(directory)
            dataset_name = os.path.basename(directory) + "_yolo_dataset"
            default_output = os.path.join(parent_dir, dataset_name)
            self.output_dir_edit.setText(default_output)

            # 统计标注与图片文件
            json_files = list(Path(directory).glob("*.json"))
            image_files = []
            for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                image_files.extend(list(Path(directory).glob(f"*{ext}")))

            self.dataset_info_label.setText(
                f"找到 {len(image_files)} 张图像，{len(json_files)} 个标注文件"
            )

            # 启用制作数据集按钮
            self.make_dataset_btn.setEnabled(len(json_files) > 0)
            if len(json_files) == 0:
                QMessageBox.warning(self, "提示", "该目录下没有找到标注文件（.json）。")

    def make_dataset(self):
        """制作 YOLO 数据集"""
        if not self.current_dir:
            QMessageBox.warning(self, "提示", "请先选择标注目录。")
            return

        # 检查缺陷类别
        if self.product_manager.get_category_count() == 0:
            QMessageBox.warning(self, "提示", "请先在产品管理页面添加缺陷类别！")
            return

        # 获取输出目录
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请指定输出目录！")
            return

        # 确认覆盖
        if os.path.exists(output_dir) and os.listdir(output_dir):
            reply = QMessageBox.question(
                self,
                "确认",
                "输出目录不为空，是否继续？\n这可能会覆盖现有文件。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        # 获取训练集比例
        train_ratio = self.train_ratio_slider.value() / 100.0

        # 创建进度对话框
        progress = QProgressDialog("正在制作数据集……", "取消", 0, 100, self)
        progress.setWindowTitle("制作数据集")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # 创建线程
        categories = self.product_manager.get_category_names()
        self.maker_thread = DatasetMakerThread(
            self.current_dir, output_dir, categories, train_ratio=train_ratio
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

    def sync_labels_to_product(self):
        """从标注目录扫描类别并同步到产品管理"""
        try:
            if not self.current_dir:
                QMessageBox.information(self, "提示", "请先选择标注目录（上方“浏览”）！")
                return

            products = self.product_manager.get_products()
            if not products:
                QMessageBox.warning(self, "提示", "请先在产品管理中添加产品！")
                return

            # 选择产品
            from PyQt5.QtWidgets import QInputDialog

            product_names = [p["name"] for p in products]
            product_name, ok = QInputDialog.getItem(
                self, "选择产品", "将类别同步到产品：", product_names, 0, False
            )
            if not ok:
                return

            # 找到产品 ID
            product_id = None
            for p in products:
                if p["name"] == product_name:
                    product_id = p["id"]
                    break

            # 扫描 json 标注文件，收集 label
            labels_found = set()
            for json_file in Path(self.current_dir).glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for s in data.get("shapes", []):
                            name = s.get("label")
                            if name:
                                labels_found.add(name)
                except Exception:
                    continue

            if not labels_found:
                QMessageBox.information(self, "提示", "未在标注文件中发现新的类别。")
                return

            # 写入到产品的缺陷类别（去重）
            added = 0
            for name in sorted(labels_found):
                if not self.product_manager.defect_category_exists(product_id, name):
                    if self.product_manager.add_defect_category(product_id, name, ""):
                        added += 1

            QMessageBox.information(self, "同步完成", f"同步完成，共新增 {added} 个缺陷类别。")
        except Exception as e:
            QMessageBox.warning(self, "同步失败", f"同步时出错：{str(e)}")
