"""
预测界面
"""
import os

import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QLineEdit, QFileDialog, QMessageBox, QSlider, QListWidget, QSplitter, QComboBox)


class PredictThread(QThread):
    """预测线程"""
    result_signal = pyqtSignal(object, str)  # results, image_path
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, model_path, image_paths, conf_threshold, iou_threshold, device, imgsz, max_det):
        super().__init__()
        self.model_path = model_path
        self.image_paths = image_paths
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.imgsz = imgsz
        self.max_det = max_det

    def run(self):
        try:
            from ultralytics import YOLO

            # 加载模型
            model = YOLO(self.model_path)

            # 预测每张图像
            for img_path in self.image_paths:
                results = model.predict(
                    img_path,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    device=self.device,
                    imgsz=self.imgsz,
                    max_det=self.max_det,
                    verbose=False
                )
                self.result_signal.emit(results[0], img_path)

            self.finished_signal.emit(True, f"成功预测 {len(self.image_paths)} 张图像")

        except Exception as e:
            self.finished_signal.emit(False, f"预测出错: {str(e)}")


class PredictWidget(QWidget):
    """预测界面"""

    def __init__(self, product_manager):
        super().__init__()
        self.product_manager = product_manager
        self.predict_thread = None
        self.current_results = None
        self.current_image_path = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：配置和控制
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_widget.setMaximumWidth(400)

        # 模型配置
        model_group = QGroupBox("模型配置")
        model_layout = QVBoxLayout()

        # 模型文件
        model_file_layout = QHBoxLayout()
        model_file_layout.addWidget(QLabel("模型文件:"))
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("选择训练好的模型文件 (.pt)")
        model_file_layout.addWidget(self.model_edit)

        self.model_btn = QPushButton("📁")
        self.model_btn.clicked.connect(self.select_model)
        self.model_btn.setMaximumWidth(40)
        model_file_layout.addWidget(self.model_btn)
        model_layout.addLayout(model_file_layout)

        # 设备
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("设备:"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(['自动选择', 'CPU', 'GPU (cuda:0)', 'GPU (cuda:1)'])
        device_layout.addWidget(self.device_combo)
        model_layout.addLayout(device_layout)

        # 图像尺寸
        imgsz_layout = QHBoxLayout()
        imgsz_layout.addWidget(QLabel("图像尺寸:"))
        self.imgsz_combo = QComboBox(); self.imgsz_combo.addItems(['320','416','512','640','800','1024']); self.imgsz_combo.setCurrentIndex(3)
        imgsz_layout.addWidget(self.imgsz_combo)
        model_layout.addLayout(imgsz_layout)

        # 最大检测数
        maxdet_layout = QHBoxLayout()
        maxdet_layout.addWidget(QLabel("最大检测数:"))
        self.maxdet_combo = QComboBox(); self.maxdet_combo.addItems(['100','300','1000'])
        maxdet_layout.addWidget(self.maxdet_combo)
        model_layout.addLayout(maxdet_layout)

        # 置信度阈值
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度阈值:"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(25)
        self.conf_slider.valueChanged.connect(self.update_conf_label)
        conf_layout.addWidget(self.conf_slider)

        self.conf_label = QLabel("0.25")
        self.conf_label.setMinimumWidth(40)
        conf_layout.addWidget(self.conf_label)
        model_layout.addLayout(conf_layout)

        # IOU阈值
        iou_layout = QHBoxLayout()
        iou_layout.addWidget(QLabel("IOU阈值:"))
        self.iou_slider = QSlider(Qt.Horizontal)
        self.iou_slider.setRange(0, 100)
        self.iou_slider.setValue(45)
        self.iou_slider.valueChanged.connect(self.update_iou_label)
        iou_layout.addWidget(self.iou_slider)

        self.iou_label = QLabel("0.45")
        self.iou_label.setMinimumWidth(40)
        iou_layout.addWidget(self.iou_label)
        model_layout.addLayout(iou_layout)

        model_group.setLayout(model_layout)
        left_layout.addWidget(model_group)

        # 图像选择
        image_group = QGroupBox("图像选择")
        image_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.select_image_btn = QPushButton("📷 选择图像")
        self.select_image_btn.clicked.connect(self.select_images)
        btn_layout.addWidget(self.select_image_btn)

        self.select_folder_btn = QPushButton("📁 选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_folder)
        btn_layout.addWidget(self.select_folder_btn)
        image_layout.addLayout(btn_layout)

        # 图像列表
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_selected)
        image_layout.addWidget(self.image_list)

        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.clicked.connect(self.image_list.clear)
        image_layout.addWidget(clear_btn)

        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)

        # 预测按钮
        self.predict_btn = QPushButton("🔍 开始预测")
        self.predict_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.predict_btn.clicked.connect(self.start_predict)
        left_layout.addWidget(self.predict_btn)

        # 保存结果按钮
        self.save_btn = QPushButton("💾 保存当前结果")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        left_layout.addWidget(self.save_btn)

        left_layout.addStretch()

        # 右侧：图像显示区域（原图+效果图）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # 图像对比显示
        image_group = QGroupBox("图像对比")
        image_layout = QHBoxLayout()

        # 左侧：原图像
        left_image_widget = QWidget()
        left_image_layout = QVBoxLayout(left_image_widget)
        
        left_title = QLabel("原图像")
        left_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        left_title.setAlignment(Qt.AlignCenter)
        left_image_layout.addWidget(left_title)
        
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_label.setStyleSheet("""
            QLabel {
                background: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
                min-height: 300px;
            }
        """)
        self.original_label.setText("原图像将显示在这里")
        self.original_label.setScaledContents(False)
        left_image_layout.addWidget(self.original_label)
        
        image_layout.addWidget(left_image_widget)

        # 右侧：预测结果
        right_image_widget = QWidget()
        right_image_layout = QVBoxLayout(right_image_widget)
        
        right_title = QLabel("预测结果")
        right_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        right_title.setAlignment(Qt.AlignCenter)
        right_image_layout.addWidget(right_title)
        
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            QLabel {
                background: #2c3e50;
                border: 2px solid #34495e;
                border-radius: 8px;
                min-height: 300px;
            }
        """)
        self.result_label.setText("预测结果将显示在这里")
        self.result_label.setScaledContents(False)
        right_image_layout.addWidget(self.result_label)
        
        image_layout.addWidget(right_image_widget)

        image_group.setLayout(image_layout)
        right_layout.addWidget(image_group)

        # 检测统计
        self.stats_label = QLabel("就绪")
        self.stats_label.setStyleSheet("""
            QLabel {
                background: #ecf0f1;
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        right_layout.addWidget(self.stats_label)

        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def update_conf_label(self, value):
        """更新置信度标签"""
        self.conf_label.setText(f"{value / 100:.2f}")

    def update_iou_label(self, value):
        """更新IOU标签"""
        self.iou_label.setText(f"{value / 100:.2f}")

    def select_model(self):
        """选择模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件",
            os.path.expanduser("~"),
            "PyTorch Models (*.pt)"
        )
        if file_path:
            self.model_edit.setText(file_path)

    def select_images(self):
        """选择图像文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图像文件",
            os.path.expanduser("~"),
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        for file_path in file_paths:
            if file_path not in [self.image_list.item(i).text()
                                 for i in range(self.image_list.count())]:
                self.image_list.addItem(file_path)

    def select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择图像文件夹",
            os.path.expanduser("~")
        )
        if folder_path:
            extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            for file_name in os.listdir(folder_path):
                if any(file_name.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(folder_path, file_name)
                    if file_path not in [self.image_list.item(i).text()
                                         for i in range(self.image_list.count())]:
                        self.image_list.addItem(file_path)

    def on_image_selected(self, item):
        """图像被选中"""
        # 可以预览原图
        pass

    def start_predict(self):
        """开始预测"""
        # 验证
        if not self.model_edit.text():
            QMessageBox.warning(self, "警告", "请选择模型文件！")
            return

        if not os.path.exists(self.model_edit.text()):
            QMessageBox.warning(self, "警告", "模型文件不存在！")
            return

        if self.image_list.count() == 0:
            QMessageBox.warning(self, "警告", "请选择要预测的图像！")
            return

        # 获取图像列表
        image_paths = [self.image_list.item(i).text()
                       for i in range(self.image_list.count())]

        # 获取参数
        conf_threshold = self.conf_slider.value() / 100
        iou_threshold = self.iou_slider.value() / 100
        device_text = self.device_combo.currentText()
        if device_text == '自动选择':
            device = ''
        elif device_text == 'CPU':
            device = 'cpu'
        else:
            device = device_text.split()[-1].strip('()')
        imgsz = int(self.imgsz_combo.currentText())
        max_det = int(self.maxdet_combo.currentText())

        # 禁用按钮
        self.predict_btn.setEnabled(False)
        self.stats_label.setText("正在预测...")

        # 创建预测线程
        self.predict_thread = PredictThread(
            self.model_edit.text(),
            image_paths,
            conf_threshold,
            iou_threshold,
            device,
            imgsz,
            max_det
        )
        self.predict_thread.result_signal.connect(self.show_result)
        self.predict_thread.finished_signal.connect(self.on_predict_finished)
        self.predict_thread.start()

    def show_result(self, results, image_path):
        """显示预测结果"""
        self.current_results = results
        self.current_image_path = image_path

        # 显示原图像
        original_img = cv2.imread(image_path)
        if original_img is not None:
            original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
            h, w, ch = original_rgb.shape
            bytes_per_line = ch * w
            original_qt = QImage(original_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            original_pixmap = QPixmap.fromImage(original_qt)
            original_scaled = original_pixmap.scaled(
                self.original_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.original_label.setPixmap(original_scaled)

        # 显示预测结果
        result_img = results.plot()
        result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        h, w, ch = result_rgb.shape
        bytes_per_line = ch * w
        result_qt = QImage(result_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        result_pixmap = QPixmap.fromImage(result_qt)
        result_scaled = result_pixmap.scaled(
            self.result_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.result_label.setPixmap(result_scaled)

        # 统计信息
        boxes = results.boxes
        if boxes is not None and len(boxes) > 0:
            num_detections = len(boxes)
            class_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = results.names[cls_id]
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            stats_text = f"检测到 {num_detections} 个目标\n"
            for cls_name, count in class_counts.items():
                stats_text += f"  • {cls_name}: {count}\n"
            self.stats_label.setText(stats_text)
        else:
            self.stats_label.setText("未检测到目标")

        self.save_btn.setEnabled(True)

    def on_predict_finished(self, success, message):
        """预测完成"""
        self.predict_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "预测完成", message)
        else:
            QMessageBox.warning(self, "预测失败", message)
            self.stats_label.setText("预测失败")

    def save_result(self):
        """保存预测结果"""
        if self.current_results is None:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存预测结果",
            os.path.basename(self.current_image_path),
            "Images (*.jpg *.png)"
        )

        if save_path:
            # 保存结果图像
            img = self.current_results.plot()
            cv2.imwrite(save_path, img)

            # 同时保存检测结果为txt
            txt_path = os.path.splitext(save_path)[0] + '_results.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                boxes = self.current_results.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        cls_name = self.current_results.names[cls_id]
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].cpu().numpy()
                        f.write(f"{cls_name} {conf:.2f} {xyxy[0]:.1f} {xyxy[1]:.1f} {xyxy[2]:.1f} {xyxy[3]:.1f}\n")

            QMessageBox.information(
                self, "保存成功",
                f"结果已保存到:\n{save_path}\n{txt_path}"
            )