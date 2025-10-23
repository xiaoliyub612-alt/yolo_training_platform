"""
产品管理界面 - 支持产品和缺陷类别的两层管理
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QLabel, QLineEdit, QTextEdit, QMessageBox,
                             QGroupBox, QComboBox, QSplitter, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt


class ProductDialog(QDialog):
    """产品编辑对话框"""

    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.init_ui()

        if product:
            self.name_edit.setText(product['name'])
            self.desc_edit.setPlainText(product.get('description', ''))

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑产品" if self.product else "添加产品")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        # 名称
        name_label = QLabel("产品名称：")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入产品名称")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)

        # 描述
        desc_label = QLabel("产品描述：")
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("请输入产品描述（可选）")
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_edit)

        # 路径
        path_label = QLabel("产品路径：")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择该产品的标注主目录（可选）")
        path_layout.addWidget(self.path_edit)
        path_btn = QPushButton("📁 浏览")
        path_btn.setMaximumWidth(80)
        path_btn.clicked.connect(self._select_path)
        path_layout.addWidget(path_btn)
        layout.addWidget(path_label)
        layout.addLayout(path_layout)

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
            'description': self.desc_edit.toPlainText().strip(),
            'path': self.path_edit.text().strip()
        }

    def _select_path(self):
        from PyQt5.QtWidgets import QFileDialog
        import os
        directory = QFileDialog.getExistingDirectory(
            self, "选择产品路径",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if directory:
            self.path_edit.setText(directory)


class DefectCategoryDialog(QDialog):
    """缺陷类别编辑对话框"""

    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.init_ui()

        if category:
            self.name_edit.setText(category['name'])
            self.desc_edit.setPlainText(category.get('description', ''))

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("编辑缺陷类别" if self.category else "添加缺陷类别")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        # 名称
        name_label = QLabel("缺陷类别名称：")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入缺陷类别名称")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)

        # 描述
        desc_label = QLabel("缺陷类别描述：")
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("请输入缺陷类别描述（可选）")
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


class ProductWidget(QWidget):
    """产品管理界面"""

    def __init__(self, product_manager):
        super().__init__()
        self.product_manager = product_manager
        self.current_product_id = None
        self.init_ui()
        self.load_products()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部说明已移除，界面更紧凑

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左侧：产品列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 产品管理按钮
        product_btn_layout = QHBoxLayout()
        self.add_product_btn = QPushButton("➕ 添加产品")
        self.add_product_btn.clicked.connect(self.add_product)
        self.add_product_btn.setStyleSheet("""
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

        self.edit_product_btn = QPushButton("✏️ 编辑产品")
        self.edit_product_btn.clicked.connect(self.edit_product)
        self.edit_product_btn.setEnabled(False)
        self.edit_product_btn.setStyleSheet("""
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

        self.delete_product_btn = QPushButton("🗑️ 删除产品")
        self.delete_product_btn.clicked.connect(self.delete_product)
        self.delete_product_btn.setEnabled(False)
        self.delete_product_btn.setStyleSheet("""
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

        product_btn_layout.addWidget(self.add_product_btn)
        product_btn_layout.addWidget(self.edit_product_btn)
        product_btn_layout.addWidget(self.delete_product_btn)
        product_btn_layout.addStretch()

        left_layout.addLayout(product_btn_layout)

        # 产品列表
        self.product_list = QListWidget()
        self.product_list.itemClicked.connect(self.on_product_selected)
        self.product_list.itemSelectionChanged.connect(self.on_product_selection_changed)
        self.product_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                background: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f2f6;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        left_layout.addWidget(self.product_list)

        # 产品统计
        self.product_stats_label = QLabel("共 0 个产品")
        self.product_stats_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        left_layout.addWidget(self.product_stats_label)

        splitter.addWidget(left_widget)

        # 右侧：缺陷类别管理
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 当前产品标签
        self.current_product_label = QLabel("请先选择一个产品")
        self.current_product_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        right_layout.addWidget(self.current_product_label)

        # 产品详情区
        detail_group = QGroupBox("产品详情")
        detail_layout = QVBoxLayout()
        self.detail_name = QLabel("名称：-")
        self.detail_desc = QLabel("描述：-")
        self.detail_desc.setWordWrap(True)
        self.detail_path = QLabel("路径：-")
        self.detail_defects = QLabel("缺陷类别数：0")
        for w in (self.detail_name, self.detail_desc, self.detail_path, self.detail_defects):
            w.setStyleSheet("color: #34495e;")
            detail_layout.addWidget(w)
        detail_group.setLayout(detail_layout)
        right_layout.addWidget(detail_group)

        # 缺陷类别管理按钮
        defect_btn_layout = QHBoxLayout()
        self.add_defect_btn = QPushButton("➕ 添加缺陷类别")
        self.add_defect_btn.clicked.connect(self.add_defect_category)
        self.add_defect_btn.setEnabled(False)
        self.add_defect_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)

        self.edit_defect_btn = QPushButton("✏️ 编辑缺陷类别")
        self.edit_defect_btn.clicked.connect(self.edit_defect_category)
        self.edit_defect_btn.setEnabled(False)
        self.edit_defect_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e67e22;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)

        self.delete_defect_btn = QPushButton("🗑️ 删除缺陷类别")
        self.delete_defect_btn.clicked.connect(self.delete_defect_category)
        self.delete_defect_btn.setEnabled(False)
        self.delete_defect_btn.setStyleSheet("""
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

        defect_btn_layout.addWidget(self.add_defect_btn)
        defect_btn_layout.addWidget(self.edit_defect_btn)
        defect_btn_layout.addWidget(self.delete_defect_btn)
        defect_btn_layout.addStretch()

        right_layout.addLayout(defect_btn_layout)

        # 缺陷类别表格
        self.defect_table = QTableWidget()
        self.defect_table.setColumnCount(3)
        self.defect_table.setHorizontalHeaderLabels(['ID', '缺陷类别名称', '描述'])
        self.defect_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.defect_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.defect_table.setSelectionMode(QTableWidget.SingleSelection)
        self.defect_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.defect_table.itemSelectionChanged.connect(self.on_defect_selection_changed)

        self.defect_table.setStyleSheet("""
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

        right_layout.addWidget(self.defect_table)

        # 缺陷类别统计
        self.defect_stats_label = QLabel("共 0 个缺陷类别")
        self.defect_stats_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 5px;")
        right_layout.addWidget(self.defect_stats_label)

        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setSizes([300, 500])

    def load_products(self):
        """加载产品列表"""
        self.product_list.clear()
        products = self.product_manager.get_products()

        for product in products:
            item = QListWidgetItem(product['name'])
            item.setData(Qt.UserRole, product['id'])
            self.product_list.addItem(item)

        self.product_stats_label.setText(f"共 {len(products)} 个产品")
        # 若存在产品且未选择，默认选中新添加或第一个
        if self.product_list.count() > 0 and self.current_product_id is None:
            self.product_list.setCurrentRow(self.product_list.count() - 1)
            current_item = self.product_list.currentItem()
            if current_item:
                self.on_product_selected(current_item)

    def on_product_selected(self, item):
        """产品选择变化"""
        self.current_product_id = item.data(Qt.UserRole)
        product = self.product_manager.get_product_by_id(self.current_product_id)
        
        if product:
            self.current_product_label.setText(f"当前产品: {product['name']}")
            # 更新详情
            self.detail_name.setText(f"名称：{product['name']}")
            desc = product.get('description', '') or '-'
            self.detail_desc.setText(f"描述：{desc}")
            defect_count = self.product_manager.get_defect_category_count(self.current_product_id)
            self.detail_defects.setText(f"缺陷类别数：{defect_count}")
            # 路径
            path = product.get('path', '') or '-'
            if not hasattr(self, 'detail_path'):
                # 首次创建路径项
                self.detail_path = QLabel()
                self.detail_path.setStyleSheet("color: #34495e;")
                # 将其插入到详情组后
                # 简化处理：追加显示
                self.detail_path.setText(f"路径：{path}")
            else:
                self.detail_path.setText(f"路径：{path}")
            self.add_defect_btn.setEnabled(True)
            self.load_defect_categories()
        else:
            self.current_product_label.setText("请先选择一个产品")
            self.detail_name.setText("名称：-")
            self.detail_desc.setText("描述：-")
            self.detail_defects.setText("缺陷类别数：0")
            self.add_defect_btn.setEnabled(False)

    def on_product_selection_changed(self):
        """产品选择变化（用于按钮状态）"""
        has_selection = len(self.product_list.selectedItems()) > 0
        self.edit_product_btn.setEnabled(has_selection)
        self.delete_product_btn.setEnabled(has_selection)

    def load_defect_categories(self):
        """加载缺陷类别列表"""
        if self.current_product_id is None:
            return

        self.defect_table.setRowCount(0)
        categories = self.product_manager.get_defect_categories(self.current_product_id)

        for cat in categories:
            row = self.defect_table.rowCount()
            self.defect_table.insertRow(row)

            self.defect_table.setItem(row, 0, QTableWidgetItem(str(cat['id'])))
            self.defect_table.setItem(row, 1, QTableWidgetItem(cat['name']))
            self.defect_table.setItem(row, 2, QTableWidgetItem(cat.get('description', '')))

        self.defect_stats_label.setText(f"共 {len(categories)} 个缺陷类别")

    def on_defect_selection_changed(self):
        """缺陷类别选择变化"""
        has_selection = len(self.defect_table.selectedItems()) > 0
        self.edit_defect_btn.setEnabled(has_selection)
        self.delete_defect_btn.setEnabled(has_selection)

    def add_product(self):
        """添加产品"""
        dialog = ProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "产品名称不能为空！")
                return

            if self.product_manager.add_product(data['name'], data['description'], data.get('path','')):
                QMessageBox.information(self, "成功", "产品添加成功！")
                # 重新加载并选中新产品
                self.load_products()
                if self.product_list.count() > 0:
                    self.product_list.setCurrentRow(self.product_list.count() - 1)
                    cur = self.product_list.currentItem()
                    if cur:
                        self.on_product_selected(cur)
            else:
                QMessageBox.warning(self, "失败", "产品已存在或添加失败！")

    def edit_product(self):
        """编辑产品"""
        current_item = self.product_list.currentItem()
        if not current_item:
            return

        product_id = current_item.data(Qt.UserRole)
        product = self.product_manager.get_product_by_id(product_id)

        if not product:
            return

        dialog = ProductDialog(self, product)
        # 预填充路径
        dialog.path_edit.setText(product.get('path',''))
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "产品名称不能为空！")
                return

            if self.product_manager.update_product(product_id, data['name'], data['description'], data.get('path','')):
                QMessageBox.information(self, "成功", "产品更新成功！")
                self.load_products()
                # 如果编辑的是当前产品，更新显示
                if product_id == self.current_product_id:
                    self.current_product_label.setText(f"当前产品: {data['name']}")
            else:
                QMessageBox.warning(self, "失败", "产品名称已存在或更新失败！")

    def delete_product(self):
        """删除产品"""
        current_item = self.product_list.currentItem()
        if not current_item:
            return

        product_id = current_item.data(Qt.UserRole)
        product_name = current_item.text()

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除产品 "{product_name}" 吗？\n注意：这将同时删除该产品的所有缺陷类别！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.product_manager.delete_product(product_id):
                QMessageBox.information(self, "成功", "产品删除成功！")
                self.load_products()
                # 清空右侧显示
                self.current_product_id = None
                self.current_product_label.setText("请先选择一个产品")
                self.add_defect_btn.setEnabled(False)
                self.defect_table.setRowCount(0)
                self.defect_stats_label.setText("共 0 个缺陷类别")
            else:
                QMessageBox.warning(self, "失败", "产品删除失败！")

    def add_defect_category(self):
        """添加缺陷类别"""
        if self.current_product_id is None:
            return

        dialog = DefectCategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "缺陷类别名称不能为空！")
                return

            if self.product_manager.add_defect_category(self.current_product_id, data['name'], data['description']):
                QMessageBox.information(self, "成功", "缺陷类别添加成功！")
                self.load_defect_categories()
            else:
                QMessageBox.warning(self, "失败", "缺陷类别已存在或添加失败！")

    def edit_defect_category(self):
        """编辑缺陷类别"""
        if self.current_product_id is None:
            return

        selected = self.defect_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        category_id = int(self.defect_table.item(row, 0).text())

        # 获取缺陷类别信息
        categories = self.product_manager.get_defect_categories(self.current_product_id)
        category = None
        for cat in categories:
            if cat['id'] == category_id:
                category = cat
                break

        if not category:
            return

        dialog = DefectCategoryDialog(self, category)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "缺陷类别名称不能为空！")
                return

            if self.product_manager.update_defect_category(self.current_product_id, category_id, data['name'], data['description']):
                QMessageBox.information(self, "成功", "缺陷类别更新成功！")
                self.load_defect_categories()
            else:
                QMessageBox.warning(self, "失败", "缺陷类别名称已存在或更新失败！")

    def delete_defect_category(self):
        """删除缺陷类别"""
        if self.current_product_id is None:
            return

        selected = self.defect_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        category_id = int(self.defect_table.item(row, 0).text())
        category_name = self.defect_table.item(row, 1).text()

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除缺陷类别 "{category_name}" 吗？\n注意：这将影响使用该类别的标注数据！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.product_manager.delete_defect_category(self.current_product_id, category_id):
                QMessageBox.information(self, "成功", "缺陷类别删除成功！")
                self.load_defect_categories()
            else:
                QMessageBox.warning(self, "失败", "缺陷类别删除失败！")
