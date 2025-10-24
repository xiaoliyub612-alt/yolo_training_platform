"""
Main window for SLDMVDeepLearningPlatForm (clean UTF-8, ASCII-only labels).
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QMessageBox,
    QDesktopWidget,
    QSizePolicy,
)

from business.product_manager import ProductManager
from ui.product_widget import ProductWidget
from ui.label_widget import LabelWidget
from ui.predict_widget import PredictWidget
from ui.train_widget import TrainWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.product_manager = ProductManager()
        self.init_ui()

    def init_ui(self):
        """Initialize UI layout and widgets."""
        self.setWindowTitle("SLDMVDeepLearningPlatForm v1.0")

        # Initial and minimum size
        self.setMinimumSize(1000, 700)

        # Set to 80% of screen size and center
        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)
        self.center_on_screen()

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Header title
        title_label = QLabel("SLDMVDeepLearningPlatForm")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border-radius: 4px;
            }
            """
        )
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(50)
        main_layout.addWidget(title_label)

        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
                padding: 5px;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 13px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: white;
                border: 1px solid #bdc3c7;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
            """
        )
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Feature tabs
        self.product_widget = ProductWidget(self.product_manager)
        self.label_widget = LabelWidget(self.product_manager)
        self.train_widget = TrainWidget(self.product_manager)
        self.predict_widget = PredictWidget(self.product_manager)

        # ASCII-only tab titles to avoid font/encoding issues
        self.tab_widget.addTab(self.product_widget, "产品管理")
        self.tab_widget.addTab(self.label_widget, "数据标注")
        self.tab_widget.addTab(self.train_widget, "模型训练")
        self.tab_widget.addTab(self.predict_widget, "图像预测")

        main_layout.addWidget(self.tab_widget, 1)

        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(
            """
            QStatusBar {
                background: #ecf0f1;
                color: #2c3e50;
                font-size: 12px;
                padding: 2px;
            }
            """
        )

    def center_on_screen(self):
        """Center the window on the primary screen."""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def resizeEvent(self, event):
        """Ensure children update on resize."""
        super().resizeEvent(event)
        if hasattr(self, "tab_widget"):
            self.tab_widget.update()

    def closeEvent(self, event):
        """Confirm before closing."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Exit SLDMVDeepLearningPlatForm?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
