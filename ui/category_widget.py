"""
类别管理界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QLabel, QLineEdit, QTextEdit, QMessageBox,
                             QGroupBox)


class CategoryDialog(QDialog):
    """类别编辑对话框"""

    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.init_ui()

        if category:
            self.name_edit.setText(category['name'])
            self.desc_edit.setPlainText(category.get('description', ''))

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑类别" if self.category else "添加类别")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        # 名称
        name_label = QLabel("类别名称：")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入类别名称")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)

        # 描述
        desc_label = QLabel("类别描述：")
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("请输入类别描述（可选）")
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        """获取数据"""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip()
        }


class CategoryWidget(QWidget):
    """类别管理界面"""

    def __init__(self, category_manager):
        super().__init__()
        self.category_manager = category_manager
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题和说明
        title_group = QGroupBox("类别管理")
        title_layout = QVBoxLayout()

        info_label = QLabel("管理YOLO模型的检测类别，用于标注和训练")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        title_layout.addWidget(info_label)
        title_group.setLayout(title_layout)
        layout.addWidget(title_group)

        # 按钮组
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ 添加类别")
        self.add_btn.clicked.connect(self.add_category)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)

        self.edit_btn = QPushButton("✏️ 编辑类别")
        self.edit_btn.clicked.connect(self.edit_category)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #2ecc71;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #27ae60;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)

        self.delete_btn = QPushButton("🗑️ 删除类别")
        self.delete_btn.clicked.connect(self.delete_category)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.load_categories)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 类别表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['ID', '类别名称', '描述', '创建时间'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                background: white;
                gridline-color: #f1f2f6;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
            }
            QHeaderView::section {
                background: #ecf0f1;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #2c3e50;
            }
        """)

        layout.addWidget(self.table)

        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        layout.addWidget(self.stats_label)

    def load_categories(self):
        """加载类别列表"""
        self.table.setRowCount(0)
        categories = self.category_manager.get_categories()

        for cat in categories:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(cat['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(cat['name']))
            self.table.setItem(row, 2, QTableWidgetItem(cat.get('description', '')))
            self.table.setItem(row, 3, QTableWidgetItem(cat.get('created_at', '')))

        self.stats_label.setText(f"共 {len(categories)} 个类别")

    def on_selection_changed(self):
        """选择变化"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def add_category(self):
        """添加类别"""
        dialog = CategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "类别名称不能为空！")
                return

            if self.category_manager.add_category(data['name'], data['description']):
                QMessageBox.information(self, "成功", "类别添加成功！")
                self.load_categories()
            else:
                QMessageBox.warning(self, "失败", "类别已存在或添加失败！")

    def edit_category(self):
        """编辑类别"""
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        category_id = int(self.table.item(row, 0).text())
        category = self.category_manager.get_category_by_id(category_id)

        if not category:
            return

        dialog = CategoryDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "类别名称不能为空！")
                return

            if self.category_manager.update_category(category_id, data['name'], data['description']):
                QMessageBox.information(self, "成功", "类别更新成功！")
                self.load_categories()
            else:
                QMessageBox.warning(self, "失败", "类别名称已存在或更新失败！")

    def delete_category(self):
        """删除类别"""
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        category_id = int(self.table.item(row, 0).text())
        category_name = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除类别 "{category_name}" 吗？\n注意：这将影响使用该类别的标注数据！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.category_manager.delete_category(category_id):
                QMessageBox.information(self, "成功", "类别删除成功！")
                self.load_categories()
            else:
                QMessageBox.warning(self, "失败", "类别删除失败！")