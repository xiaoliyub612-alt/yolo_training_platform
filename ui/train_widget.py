"""
训练界面（清理编码问题与压缩问题）
"""
import os

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QFormLayout,
    QSizePolicy,
    QScrollArea,
    QFrame,
)


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

            # 训练参数日志
            self.log_signal.emit("开始训练...")
            self.log_signal.emit(f"数据: {self.config['data']}")
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
                exist_ok=True,
                patience=50,
                save=True,
                plots=True,
                verbose=True,
            )

            if self.is_running:
                save_dir = os.path.join(self.config['project'], self.config['name'])
                self.finished_signal.emit(True, f"训练完成！模型已保存到: {save_dir}")

        except Exception as e:
            self.finished_signal.emit(False, f"训练出错: {str(e)}")

    def stop(self):
        """停止训练"""
        self.is_running = False


class TrainWidget(QWidget):
    """训练界面"""

    def __init__(self, category_manager):
        super().__init__()
        self.category_manager = category_manager
        self.train_thread = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 训练配置
        config_group = QGroupBox("训练配置")
        config_layout = QFormLayout()
        config_layout.setSpacing(10)
        config_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        config_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        config_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 数据集配置文件
        data_layout = QHBoxLayout()
        self.data_edit = QLineEdit()
        self.data_edit.setMinimumWidth(360)
        self.data_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.data_edit.setPlaceholderText("选择数据集配置文件 (data.yaml)")
        data_layout.addWidget(self.data_edit)

        self.data_btn = QPushButton("浏览")
        self.data_btn.clicked.connect(self.select_data_file)
        self.data_btn.setMaximumWidth(80)
        data_layout.addWidget(self.data_btn)
        config_layout.addRow("数据: ", data_layout)

        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(180)
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_combo.addItems([
            'yolov8n.pt (最小)',
            'yolov8s.pt (快速)',
            'yolov8m.pt (平衡)',
            'yolov8l.pt (高精度)',
            'yolov8x.pt (最高精度)'
        ])
        self.model_combo.setCurrentIndex(0)
        config_layout.addRow("预训练模型: ", self.model_combo)

        # 训练轮数
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setMaximumWidth(140)
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(100)
        self.epochs_spin.setSuffix(" 轮")
        config_layout.addRow("训练轮数: ", self.epochs_spin)

        # 批次大小
        self.batch_spin = QSpinBox()
        self.batch_spin.setMaximumWidth(140)
        self.batch_spin.setRange(1, 128)
        self.batch_spin.setValue(16)
        config_layout.addRow("批次大小: ", self.batch_spin)

        # 图像尺寸
        self.imgsz_combo = QComboBox()
        self.imgsz_combo.setMinimumWidth(140)
        self.imgsz_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.imgsz_combo.addItems(['320', '416', '512', '640', '800', '1024'])
        self.imgsz_combo.setCurrentIndex(3)  # 默认640
        config_layout.addRow("图像尺寸: ", self.imgsz_combo)

        # 设备选择
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(180)
        self.device_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.device_combo.addItems(['自动选择', 'CPU', 'GPU (cuda:0)', 'GPU (cuda:1)'])
        config_layout.addRow("计算设备: ", self.device_combo)

        # 工作线程
        self.workers_spin = QSpinBox()
        self.workers_spin.setMaximumWidth(140)
        self.workers_spin.setRange(0, 16)
        self.workers_spin.setValue(4)
        config_layout.addRow("工作线程: ", self.workers_spin)

        # 保存目录
        save_layout = QHBoxLayout()
        self.save_edit = QLineEdit()
        self.save_edit.setMinimumWidth(360)
        self.save_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_edit.setText("./runs/train")
        self.save_edit.setPlaceholderText("训练结果保存目录")
        save_layout.addWidget(self.save_edit)

        self.save_btn = QPushButton("浏览")
        self.save_btn.clicked.connect(self.select_save_dir)
        self.save_btn.setMaximumWidth(80)
        save_layout.addWidget(self.save_btn)
        config_layout.addRow("保存目录: ", save_layout)

        # 训练名称
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumWidth(220)
        self.name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_edit.setText("exp")
        self.name_edit.setPlaceholderText("训练任务名称")
        config_layout.addRow("任务名称: ", self.name_edit)

        config_group.setLayout(config_layout)

        # 滚动容器，避免缩放导致布局过分折叠
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QFrame.NoFrame)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        config_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        config_scroll.setWidget(config_group)
        # 使配置区可完全随父窗口缩放（垂直方向展开/收缩），小窗口时内部滚动
        config_scroll.setMinimumHeight(0)
        config_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(config_scroll)
        try:
            layout.setStretch(layout.indexOf(config_scroll), 1)
        except Exception:
            pass

        # 控制按钮
        btn_layout = QHBoxLayout()

        # 记录按钮文本，便于小屏幕时切换为紧凑模式
        self._btn_normal_style = (
            """
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #27ae60; }
            QPushButton:disabled { background: #bdc3c7; }
            """
        )
        self._btn_compact_style = (
            """
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #27ae60; }
            QPushButton:disabled { background: #bdc3c7; }
            """
        )

        self.start_btn = QPushButton("开始训练")
        self.start_btn.setStyleSheet(self._btn_normal_style)
        self.start_btn.clicked.connect(self.start_training)
        self.start_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_layout.addWidget(self.start_btn)

        self._stop_btn_normal_style = (
            """
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
            QPushButton:disabled { background: #bdc3c7; }
            """
        )
        self._stop_btn_compact_style = (
            """
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
            QPushButton:disabled { background: #bdc3c7; }
            """
        )

        self.stop_btn = QPushButton("停止训练")
        self.stop_btn.setStyleSheet(self._stop_btn_normal_style)
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 初始紧凑模式标记
        self._compact_buttons = False

        # 训练进度
        progress_group = QGroupBox("训练进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar { border: 2px solid #bdc3c7; border-radius: 5px; text-align: center; height: 25px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #2ecc71); }
            """
        )
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        self.progress_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        progress_layout.addWidget(self.progress_label)

        progress_group.setLayout(progress_layout)
        progress_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(progress_group)

        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
            """
        )
        self.log_text.setMinimumHeight(200)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        log_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(log_group)

    def select_data_file(self):
        """选择数据集配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据集配置文件",
            os.path.expanduser("~"),
            "YAML Files (*.yaml *.yml)",
        )
        if file_path:
            self.data_edit.setText(file_path)

    def select_save_dir(self):
        """选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly,
        )
        if directory:
            self.save_edit.setText(directory)

    def start_training(self):
        """开始训练"""
        # 验证配置
        if not self.data_edit.text():
            QMessageBox.warning(self, "警告", "请选择数据集配置文件！")
            return
        if not os.path.exists(self.data_edit.text()):
            QMessageBox.warning(self, "警告", "数据集配置文件不存在！")
            return

        # 确认开始
        reply = QMessageBox.question(
            self,
            '确认训练',
            f'确定要开始训练吗？\n'
            f'训练轮数: {self.epochs_spin.value()}\n'
            f'批次大小: {self.batch_spin.value()}\n'
            f'这可能需要较长时间。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.No:
            return

        # 准备配置
        model_text = self.model_combo.currentText()
        model_name = model_text.split()[0]

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
        }

        # 清空日志并重置进度
        self.log_text.clear()
        self.progress_bar.setValue(0)

        # 禁用开始按钮，启用停止按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

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
                self,
                '确认停止',
                '确定要停止训练吗？\n已训练的进度将会保存。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.append_log("正在停止训练...")
                self.train_thread.stop()
                self.train_thread.wait()
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)

    def append_log(self, text):
        """添加日志"""
        self.log_text.append(text)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, current, total, loss):
        """更新进度"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_label.setText(
                f"训练进度: {current}/{total} 轮, 损失: {loss:.4f}"
            )

    def on_training_finished(self, success, message):
        """训练完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if success:
            self.progress_bar.setValue(100)
            self.append_log("=" * 50)
            self.append_log(message)
            QMessageBox.information(self, "训练完成", message)
        else:
            self.append_log("=" * 50)
            self.append_log(message)
            QMessageBox.warning(self, "训练失败", message)

    def resizeEvent(self, event):
        """根据可用宽度自适应按钮样式与文本"""
        super().resizeEvent(event)
        try:
            available = self.width()
            # 经验阈值：小于 700px 时采用紧凑样式
            compact = available < 700
            if compact != self._compact_buttons:
                self._compact_buttons = compact
                if compact:
                    self.start_btn.setText("开始")
                    self.stop_btn.setText("停止")
                    self.start_btn.setStyleSheet(self._btn_compact_style)
                    self.stop_btn.setStyleSheet(self._stop_btn_compact_style)
                else:
                    self.start_btn.setText("开始训练")
                    self.stop_btn.setText("停止训练")
                    self.start_btn.setStyleSheet(self._btn_normal_style)
                    self.stop_btn.setStyleSheet(self._stop_btn_normal_style)
        except Exception:
            pass
