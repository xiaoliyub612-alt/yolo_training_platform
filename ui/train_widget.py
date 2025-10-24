"""
训练界面
"""
import os

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGroupBox, QLabel, QLineEdit, QComboBox,
                             QSpinBox, QTextEdit, QFileDialog, QMessageBox,
                             QProgressBar, QFormLayout)


class TrainThread(QThread):
    """训练线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, float)  # current_epoch, total_epochs, loss
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = True

    def run(self):
        try:
            from ultralytics import YOLO

            # 加载模型
            self.log_signal.emit(f"正在加载模型: {self.config['model']}...")
            model = YOLO(self.config['model'])

            # 训练参数
            self.log_signal.emit("开始训练...")
            self.log_signal.emit(f"数据集: {self.config['data']}")
            self.log_signal.emit(f"训练轮数: {self.config['epochs']}")
            self.log_signal.emit(f"批次大小: {self.config['batch']}")
            self.log_signal.emit(f"图像尺寸: {self.config['imgsz']}")
            self.log_signal.emit("-" * 50)

            # 开始训练
            results = model.train(
                data=self.config['data'],
                epochs=self.config['epochs'],
                imgsz=self.config['imgsz'],
                batch=self.config['batch'],
                device=self.config['device'],
                workers=self.config['workers'],
                project=self.config['project'],
                name=self.config['name'],
                rect=self.config['rect'],
                cache=self.config['cache'],
                augment=self.config['augment'],
                exist_ok=True,
                patience=50,
                save=True,
                plots=True,
                verbose=True
            )

            if self.is_running:
                save_dir = os.path.join(self.config['project'], self.config['name'])
                self.finished_signal.emit(True, f"训练完成！模型已保存到: {save_dir}")

        except Exception as e:
            self.finished_signal.emit(False, f"训练出错: {str(e)}")

    def stop(self):
        """停止训练"""
        self.is_running = False


class ExportThread(QThread):
    """模型导出线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            from ultralytics import YOLO

            # 加载模型
            self.log_signal.emit(f"正在加载模型: {self.config['model']}...")
            model = YOLO(self.config['model'])

            # 导出模型
            self.log_signal.emit(f"开始导出为 {self.config['format']} 格式...")
            self.log_signal.emit(f"图像尺寸: {self.config['imgsz']}")
            if self.config.get('half'):
                self.log_signal.emit("使用半精度 (FP16)")
            self.log_signal.emit("-" * 50)

            # 执行导出
            export_path = model.export(
                format=self.config['format'],
                imgsz=self.config['imgsz'],
                half=self.config.get('half', False),
                optimize=self.config.get('optimize', False),
                simplify=self.config.get('simplify', False),
                dynamic=self.config.get('dynamic', False)
            )

            self.finished_signal.emit(True, f"导出完成！文件已保存到: {export_path}")

        except Exception as e:
            self.finished_signal.emit(False, f"导出出错: {str(e)}")


class TrainWidget(QWidget):
    """训练界面"""

    def __init__(self, product_manager):
        super().__init__()
        self.product_manager = product_manager
        self.train_thread = None
        self.export_thread = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 配置组
        config_group = QGroupBox("训练配置")
        config_layout = QFormLayout()
        config_layout.setSpacing(10)

        # 数据集配置文件
        data_layout = QHBoxLayout()
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("选择数据集配置文件 (data.yaml)")
        data_layout.addWidget(self.data_edit)

        self.data_btn = QPushButton("📁 浏览")
        self.data_btn.clicked.connect(self.select_data_file)
        self.data_btn.setMaximumWidth(80)
        data_layout.addWidget(self.data_btn)
        config_layout.addRow("数据集:", data_layout)

        # 模型选择（合并：可编辑下拉 + 浏览）
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            'yolov8n.pt',
            'yolov8s.pt',
            'yolov8m.pt',
            'yolov8l.pt',
            'yolov8x.pt'
        ])
        self.model_combo.setCurrentIndex(0)
        model_layout.addWidget(self.model_combo)

        self.model_browse_btn = QPushButton("📁 浏览")
        self.model_browse_btn.setMaximumWidth(80)
        self.model_browse_btn.clicked.connect(self.select_model_file)
        model_layout.addWidget(self.model_browse_btn)
        config_layout.addRow("模型:", model_layout)

        # 训练轮数
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(100)
        self.epochs_spin.setSuffix(" 轮")
        config_layout.addRow("训练轮数:", self.epochs_spin)

        # 批次大小
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 128)
        self.batch_spin.setValue(16)
        config_layout.addRow("批次大小:", self.batch_spin)

        # 图像尺寸
        self.imgsz_combo = QComboBox()
        self.imgsz_combo.addItems(['320', '416', '512', '640', '800', '1024'])
        self.imgsz_combo.setCurrentIndex(3)  # 默认640
        config_layout.addRow("图像尺寸:", self.imgsz_combo)

        # 设备选择
        self.device_combo = QComboBox()
        self.device_combo.addItems(['自动选择', 'CPU', 'GPU (cuda:0)', 'GPU (cuda:1)'])
        config_layout.addRow("计算设备:", self.device_combo)

        # 工作线程数
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(0, 16)
        self.workers_spin.setValue(4)
        config_layout.addRow("工作线程:", self.workers_spin)

        # 保存目录
        save_layout = QHBoxLayout()
        self.save_edit = QLineEdit()
        self.save_edit.setText("./runs/train")
        self.save_edit.setPlaceholderText("训练结果保存目录")
        save_layout.addWidget(self.save_edit)

        self.save_btn = QPushButton("📁 浏览")
        self.save_btn.clicked.connect(self.select_save_dir)
        self.save_btn.setMaximumWidth(80)
        save_layout.addWidget(self.save_btn)
        config_layout.addRow("保存目录:", save_layout)

        # 训练名称
        self.name_edit = QLineEdit()
        self.name_edit.setText("exp")
        self.name_edit.setPlaceholderText("训练任务名称")
        config_layout.addRow("任务名称:", self.name_edit)

        # 额外训练参数
        self.rect_combo = QComboBox(); self.rect_combo.addItems(['否', '是'])
        config_layout.addRow("矩形训练(rect):", self.rect_combo)
        self.cache_combo = QComboBox(); self.cache_combo.addItems(['否', 'ram', 'disk'])
        config_layout.addRow("缓存(cache):", self.cache_combo)
        self.augment_combo = QComboBox(); self.augment_combo.addItems(['否', '是'])
        config_layout.addRow("数据增强(augment):", self.augment_combo)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # ========== 新增：模型导出配置组 ==========
        export_group = QGroupBox("模型导出配置")
        export_layout = QFormLayout()
        export_layout.setSpacing(10)

        # 导出模型文件选择
        export_model_layout = QHBoxLayout()
        self.export_model_edit = QLineEdit()
        self.export_model_edit.setPlaceholderText("选择要导出的模型文件 (.pt)")
        export_model_layout.addWidget(self.export_model_edit)

        self.export_model_btn = QPushButton("📁 浏览")
        self.export_model_btn.clicked.connect(self.select_export_model)
        self.export_model_btn.setMaximumWidth(80)
        export_model_layout.addWidget(self.export_model_btn)
        export_layout.addRow("模型文件:", export_model_layout)

        # 导出格式
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([
            'onnx',      # ONNX
            'torchscript',  # TorchScript
            'openvino',  # OpenVINO
            'engine',    # TensorRT
            'coreml',    # CoreML
            'saved_model',  # TensorFlow SavedModel
            'pb',        # TensorFlow GraphDef
            'tflite',    # TensorFlow Lite
            'edgetpu',   # TensorFlow Edge TPU
            'tfjs',      # TensorFlow.js
            'paddle',    # PaddlePaddle
            'ncnn'       # NCNN
        ])
        self.export_format_combo.setCurrentIndex(0)  # 默认ONNX
        export_layout.addRow("导出格式:", self.export_format_combo)

        # 导出图像尺寸
        self.export_imgsz_combo = QComboBox()
        self.export_imgsz_combo.addItems(['320', '416', '512', '640', '800', '1024'])
        self.export_imgsz_combo.setCurrentIndex(3)  # 默认640
        export_layout.addRow("图像尺寸:", self.export_imgsz_combo)

        # 导出选项
        self.export_half_combo = QComboBox()
        self.export_half_combo.addItems(['否', '是'])
        export_layout.addRow("半精度(FP16):", self.export_half_combo)

        self.export_optimize_combo = QComboBox()
        self.export_optimize_combo.addItems(['否', '是'])
        export_layout.addRow("优化移动端:", self.export_optimize_combo)

        self.export_simplify_combo = QComboBox()
        self.export_simplify_combo.addItems(['否', '是'])
        self.export_simplify_combo.setCurrentIndex(1)  # 默认简化
        export_layout.addRow("简化ONNX:", self.export_simplify_combo)

        self.export_dynamic_combo = QComboBox()
        self.export_dynamic_combo.addItems(['否', '是'])
        export_layout.addRow("动态输入:", self.export_dynamic_combo)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # 控制按钮
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("🚀 开始训练")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_training)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ 停止训练")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        # 新增：导出按钮
        self.export_btn = QPushButton("📦 导出模型")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 30px;
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
        self.export_btn.clicked.connect(self.start_export)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 进度条
        progress_group = QGroupBox("训练进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        self.progress_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
        """)
        self.log_text.setMinimumHeight(200)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def select_data_file(self):
        """选择数据集配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据集配置文件",
            os.path.expanduser("~"),
            "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            self.data_edit.setText(file_path)

    def select_save_dir(self):
        """选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择保存目录",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if directory:
            self.save_edit.setText(directory)

    def select_model_file(self):
        """选择模型文件 (.pt/.pth) 并填入合并输入框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件",
            os.path.expanduser("~"),
            "PyTorch Model (*.pt *.pth)"
        )
        if file_path:
            self.model_combo.setEditText(file_path)

    def select_export_model(self):
        """选择要导出的模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要导出的模型文件",
            os.path.expanduser("~"),
            "PyTorch Model (*.pt *.pth)"
        )
        if file_path:
            self.export_model_edit.setText(file_path)

    def start_training(self):
        """开始训练"""
        # 验证配置
        if not self.data_edit.text():
            QMessageBox.warning(self, "警告", "请选择数据集配置文件！")
            return

        if not os.path.exists(self.data_edit.text()):
            QMessageBox.warning(self, "警告", "数据集配置文件不存在！")
            return

        # 确认开始训练
        reply = QMessageBox.question(
            self, '确认训练',
            f'确定要开始训练吗？\n'
            f'训练轮数: {self.epochs_spin.value()}\n'
            f'批次大小: {self.batch_spin.value()}\n'
            f'这可能需要较长时间。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            return

        # 准备配置：模型合并输入（自定义优先）
        model_name = self.model_combo.currentText().strip()

        device_text = self.device_combo.currentText()
        if device_text == '自动选择':
            device = ''
        elif device_text == 'CPU':
            device = 'cpu'
        else:
            device = device_text.split()[-1].strip('()')

        config = {
            'data': self.data_edit.text(),
            'model': model_name,
            'epochs': self.epochs_spin.value(),
            'batch': self.batch_spin.value(),
            'imgsz': int(self.imgsz_combo.currentText()),
            'device': device,
            'workers': self.workers_spin.value(),
            'project': self.save_edit.text(),
            'name': self.name_edit.text(),
            'rect': (self.rect_combo.currentText() == '是'),
            'cache': (self.cache_combo.currentText() if self.cache_combo.currentText() != '否' else False),
            'augment': (self.augment_combo.currentText() == '是')
        }

        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)

        # 禁用开始按钮，启用停止按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)

        # 创建并启动训练线程
        self.train_thread = TrainThread(config)
        self.train_thread.log_signal.connect(self.append_log)
        self.train_thread.progress_signal.connect(self.update_progress)
        self.train_thread.finished_signal.connect(self.on_training_finished)
        self.train_thread.start()

    def stop_training(self):
        """停止训练"""
        if self.train_thread and self.train_thread.isRunning():
            reply = QMessageBox.question(
                self, '确认停止',
                '确定要停止训练吗？\n已训练的进度将会保存。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.append_log("正在停止训练...")
                self.train_thread.stop()
                self.train_thread.wait()
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.export_btn.setEnabled(True)

    def start_export(self):
        """开始导出模型"""
        # 验证配置
        if not self.export_model_edit.text():
            QMessageBox.warning(self, "警告", "请选择要导出的模型文件！")
            return

        if not os.path.exists(self.export_model_edit.text()):
            QMessageBox.warning(self, "警告", "模型文件不存在！")
            return

        # 确认导出
        export_format = self.export_format_combo.currentText()
        reply = QMessageBox.question(
            self, '确认导出',
            f'确定要导出模型吗？\n'
            f'导出格式: {export_format}\n'
            f'图像尺寸: {self.export_imgsz_combo.currentText()}\n'
            f'这可能需要一些时间。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            return

        # 准备导出配置
        config = {
            'model': self.export_model_edit.text(),
            'format': export_format,
            'imgsz': int(self.export_imgsz_combo.currentText()),
            'half': (self.export_half_combo.currentText() == '是'),
            'optimize': (self.export_optimize_combo.currentText() == '是'),
            'simplify': (self.export_simplify_combo.currentText() == '是'),
            'dynamic': (self.export_dynamic_combo.currentText() == '是')
        }

        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在导出模型...")

        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # 创建并启动导出线程
        self.export_thread = ExportThread(config)
        self.export_thread.log_signal.connect(self.append_log)
        self.export_thread.finished_signal.connect(self.on_export_finished)
        self.export_thread.start()

    def append_log(self, text):
        """添加日志"""
        self.log_text.append(text)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, current, total, loss):
        """更新进度"""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(
            f"训练进度: {current}/{total} 轮, 损失: {loss:.4f}"
        )

    def on_training_finished(self, success, message):
        """训练完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.append_log("=" * 50)
            self.append_log("✅ " + message)
            QMessageBox.information(self, "训练完成", message)
        else:
            self.append_log("=" * 50)
            self.append_log("❌ " + message)
            QMessageBox.warning(self, "训练失败", message)

    def on_export_finished(self, success, message):
        """导出完成"""
        self.start_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("就绪")

        if success:
            self.append_log("=" * 50)
            self.append_log("✅ " + message)
            QMessageBox.information(self, "导出完成", message)
        else:
            self.append_log("=" * 50)
            self.append_log("❌ " + message)
            QMessageBox.warning(self, "导出失败", message)