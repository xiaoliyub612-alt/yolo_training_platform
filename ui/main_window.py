"""
主窗口界面
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QMessageBox)

from business.product_manager import ProductManager
from ui.product_widget import ProductWidget
from ui.label_widget import LabelWidget
from ui.predict_widget import PredictWidget
from ui.train_widget import TrainWidget


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.product_manager = ProductManager()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("YOLO训练平台 v1.0")
        self.setGeometry(100, 100, 1400, 900)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("YOLO目标检测训练平台")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: white;
                border: 1px solid #cccccc;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)

        # 创建各个功能标签页
        self.product_widget = ProductWidget(self.product_manager)
        self.label_widget = LabelWidget(self.product_manager)
        self.train_widget = TrainWidget(self.product_manager)
        self.predict_widget = PredictWidget(self.product_manager)

        self.tab_widget.addTab(self.product_widget, "📦 产品管理")
        self.tab_widget.addTab(self.label_widget, "🏷️ 数据标注")
        self.tab_widget.addTab(self.train_widget, "🎯 模型训练")
        self.tab_widget.addTab(self.predict_widget, "🔍 图像预测")

        main_layout.addWidget(self.tab_widget)

        # 底部状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #ecf0f1;
                color: #2c3e50;
                font-size: 12px;
            }
        """)

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出YOLO训练平台吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()