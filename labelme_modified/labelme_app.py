"""
SLDMV wrapper for labelme MainWindow with:
- 完整中文映射（tr 覆盖常见菜单/动作/提示，未覆盖项回退）
- 可选 YOLO (.pt) 自动标注：1) 当前图片 2) 整个目录
- 保持 UTF-8 干净，避免乱码
"""
import os
from typing import Optional, List

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QMessageBox,
    QProgressDialog,
    QApplication,
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QDoubleSpinBox,
    QFileDialog,
    QLabel,
    QToolButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
)

try:
    from labelme.app import MainWindow as LabelmeMainWindowBase  # type: ignore
    LABELME_AVAILABLE = True
except Exception as e:  # pragma: no cover
    print(f"Warning: labelme not available: {e}")
    LABELME_AVAILABLE = False
    LabelmeMainWindowBase = object  # fallback 防止类型检查报错


class LabelmeMainWindow(LabelmeMainWindowBase):
    def __init__(
        self,
        config: Optional[dict] = None,
        filename: Optional[str] = None,
        output: Optional[str] = None,
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        if not LABELME_AVAILABLE:
            raise ImportError("labelme 模块不可用")

        if output_dir:
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)

        super().__init__(
            filename=filename,
            output=output,
            output_file=output_file,
            config=config,
            output_dir=output_dir,
        )

        # 标题（ASCII 也可，中文在 UTF-8 下正常）
        self.setWindowTitle("SLDMV图像标注工具")

        # AI 配置（延迟加载）
        self._ai_model_path: Optional[str] = None
        self._ai_conf: float = 0.25
        try:
            if isinstance(config, dict):
                self._ai_model_path = (
                    config.get("ai_model") or os.environ.get("SLDMV_YOLO_MODEL")
                )
                if "ai_conf" in config:
                    self._ai_conf = float(config.get("ai_conf") or 0.25)
            else:
                self._ai_model_path = os.environ.get("SLDMV_YOLO_MODEL")
        except Exception:
            self._ai_model_path = os.environ.get("SLDMV_YOLO_MODEL")

        # 延迟挂菜单与左侧 AI 面板
        QTimer.singleShot(100, self._modify_menus)
        QTimer.singleShot(150, self._init_ai_dock)

    # -------------------- 菜单挂载 --------------------
    def _modify_menus(self) -> None:
        """保留原菜单，不再把自动标注动作放在编辑/工具菜单中。"""
        try:
            if not hasattr(self, "actions") or not hasattr(self, "menus"):
                return
            # 不做改动，自动标注入口改为左侧 Dock
            return
        except Exception:
            pass

    def _init_ai_dock(self) -> None:
        """初始化左侧 AI 标注侧栏（按钮展开，支持缩放滚动）。"""
        try:
            dock = QDockWidget("AI 标注", self)
            dock.setObjectName("ai_dock")
            dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

            # 外层滚动，避免窄屏拥挤
            scroller = QScrollArea(dock)
            scroller.setWidgetResizable(True)
            scroller.setFrameShape(QFrame.NoFrame)

            panel = QWidget()
            scroller.setWidget(panel)

            vbox = QVBoxLayout(panel)
            vbox.setContentsMargins(8, 8, 8, 8)
            vbox.setSpacing(10)

            # 顶部：按钮一键展开配置
            self.ai_toggle_btn = QToolButton(panel)
            self.ai_toggle_btn.setText("AI 自动标注")
            self.ai_toggle_btn.setCheckable(True)
            self.ai_toggle_btn.setChecked(False)
            self.ai_toggle_btn.setArrowType(Qt.RightArrow)

            vbox.addWidget(self.ai_toggle_btn)

            # 简要显示当前权重（折叠时隐藏）
            brief_text = self._ai_model_path or os.environ.get("SLDMV_YOLO_MODEL") or "未选择权重"
            show_name = os.path.basename(brief_text) if os.path.isabs(brief_text) else brief_text
            self.ai_model_brief = QLabel(f"当前权重: {show_name}", panel)
            self.ai_model_brief.setToolTip(brief_text)
            self.ai_model_brief.setStyleSheet("color:#555; font-size:12px;")
            self.ai_model_brief.setVisible(False)
            vbox.addWidget(self.ai_model_brief)

            # 折叠配置区（默认隐藏）
            self.ai_config_frame = QFrame(panel)
            self.ai_config_frame.setFrameShape(QFrame.StyledPanel)
            self.ai_config_frame.setVisible(False)
            cfg = QVBoxLayout(self.ai_config_frame)
            cfg.setContentsMargins(6, 6, 6, 6)
            cfg.setSpacing(8)

            # 模型路径
            cfg.addWidget(QLabel("权重路径(.pt):"))
            row_model = QHBoxLayout()
            self.ai_model_edit = QLineEdit(self.ai_config_frame)
            self.ai_model_edit.setPlaceholderText("选择 YOLO 权重文件 (.pt)")
            if self._ai_model_path:
                self.ai_model_edit.setText(self._ai_model_path)
            self.ai_model_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn_browse = QPushButton("浏览", self.ai_config_frame)
            btn_browse.setMaximumWidth(72)

            def on_browse():
                path, _ = QFileDialog.getOpenFileName(
                    self, "选择权重文件", os.path.expanduser("~"), "Model (*.pt);;All (*.*)"
                )
                if path:
                    self.ai_model_edit.setText(path)
                    self.ai_model_brief.setText(f"当前权重: {os.path.basename(path)}")
                    self.ai_model_brief.setToolTip(path)
                    self._ai_model_path = path
                    if hasattr(self, "_ai_model"):
                        self._ai_model = None

            btn_browse.clicked.connect(on_browse)
            row_model.addWidget(self.ai_model_edit)
            row_model.addWidget(btn_browse)
            cfg.addLayout(row_model)

            # 置信度阈值
            row_conf = QHBoxLayout()
            row_conf.addWidget(QLabel("置信度阈值:"))
            self.ai_conf_spin = QDoubleSpinBox(self.ai_config_frame)
            self.ai_conf_spin.setRange(0.0, 1.0)
            self.ai_conf_spin.setSingleStep(0.01)
            self.ai_conf_spin.setDecimals(2)
            self.ai_conf_spin.setValue(float(getattr(self, "_ai_conf", 0.25)))

            def on_conf_changed(val: float):
                try:
                    self._ai_conf = float(val)
                except Exception:
                    self._ai_conf = 0.25

            self.ai_conf_spin.valueChanged.connect(on_conf_changed)
            row_conf.addWidget(self.ai_conf_spin, 1)
            cfg.addLayout(row_conf)

            vbox.addWidget(self.ai_config_frame)

            # 动作按钮：始终可见
            btn_row = QHBoxLayout()
            btn_one = QPushButton("自动标注当前", panel)
            btn_dir = QPushButton("自动标注目录", panel)
            btn_row.addWidget(btn_one, 1)
            btn_row.addWidget(btn_dir, 1)
            vbox.addLayout(btn_row)

            # 事件绑定
            def on_toggle(checked: bool):
                self.ai_config_frame.setVisible(checked)
                self.ai_model_brief.setVisible(checked)
                self.ai_toggle_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
                self.ai_toggle_btn.setText("收起 AI 配置" if checked else "AI 自动标注")
                if checked:
                    dock.setMinimumHeight(220)
                    dock.setMaximumHeight(360)
                else:
                    dock.setMinimumHeight(60)
                    dock.setMaximumHeight(120)

            on_toggle(False)

            self.ai_toggle_btn.toggled.connect(on_toggle)

            def run_one():
                try:
                    path = self.ai_model_edit.text().strip() if hasattr(self, 'ai_model_edit') else ''
                    if path:
                        self._ai_model_path = path
                        if hasattr(self, "_ai_model"):
                            self._ai_model = None
                    self._auto_annotate_current()
                except Exception as e:
                    QMessageBox.warning(self, "自动标注失败", f"执行自动标注时出错:\n{e}")

            def run_dir():
                try:
                    path = self.ai_model_edit.text().strip() if hasattr(self, 'ai_model_edit') else ''
                    if path:
                        self._ai_model_path = path
                        if hasattr(self, "_ai_model"):
                            self._ai_model = None
                    self._auto_annotate_directory()
                except Exception as e:
                    QMessageBox.warning(self, "自动标注失败", f"执行目录自动标注时出错:\n{e}")

            btn_one.clicked.connect(run_one)
            btn_dir.clicked.connect(run_dir)

            # 放入 Dock 并放置在 Flags 之上
            dock.setWidget(scroller)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
            try:
                # 允许在同一侧嵌套分割
                if hasattr(self, "flagDock") and self.flagDock:
                    self.setDockNestingEnabled(True)
                    # 以 AI Dock 作为 first，Flags 作为 second，垂直拆分：Flags 显示在 AI 之下
                    self.splitDockWidget(dock, self.flagDock, Qt.Vertical)
                    # 调整两者相对高度，确保 AI 面板不占整列
                    try:
                        self.resizeDocks([dock, self.flagDock], [220, 480], Qt.Vertical)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    # -------------------- 中文翻译映射 --------------------
    def tr(self, text: str) -> str:  # type: ignore[override]
        translations = {
            # 菜单
            "&File": "文件(&F)",
            "&Edit": "编辑(&E)",
            "&View": "视图(&V)",
            "&Help": "帮助(&H)",

            # 文件菜单/动作
            "&Open": "打开(&O)",
            "&Open\n": "打开(&O)\n",
            "Open Dir": "打开目录",
            "&Next Image": "下一张(&N)",
            "&Prev Image": "上一张(&P)",
            "&Save": "保存(&S)",
            "&Save\n": "保存(&S)\n",
            "&Save As": "另存为(&A)",
            "&Close": "关闭(&C)",
            "&Delete File": "删除文件(&D)",
            "&Quit": "退出(&Q)",
            "Open &Recent": "最近打开(&R)",
            "&Change Output Dir": "更改输出目录(&C)",
            "Save &Automatically": "自动保存(&A)",
            "Save With Image Data": "保存图像数据",
            "Save automatically": "自动保存",
            "Save image data in label file": "在标注文件中保存图像数据",

            # 编辑动作
            "Create Polygons": "创建多边形",
            "Create Rectangle": "创建矩形",
            "Create Circle": "创建圆形",
            "Create Line": "创建直线",
            "Create Point": "创建点",
            "Create LineStrip": "创建线段",
            "Edit Polygons": "编辑多边形",
            "Delete Polygons": "删除多边形",
            "Duplicate Polygons": "复制多边形",
            "Copy Polygons": "复制多边形到剪贴板",
            "Paste Polygons": "粘贴多边形",
            "Undo last point": "撤销上一点",
            "Undo\n": "撤销\n",
            "Remove Selected Point": "删除选中点",
            "&Edit Label": "编辑标签(&E)",
            "Keep Previous Annotation": "保持上一个标注",

            # 视图动作
            "&Hide\nPolygons": "隐藏多边形(&H)\n",
            "&Show\nPolygons": "显示多边形(&S)\n",
            "&Toggle\nPolygons": "切换多边形(&T)\n",
            "Zoom &In": "放大(&I)",
            "&Zoom Out": "缩小(&O)",
            "&Original size": "原始大小(&O)",
            "&Keep Previous Scale": "保持上一缩放(&K)",
            "&Fit Window": "适应窗口(&F)",
            "Fit &Width": "适应宽度(&W)",
            "&Brightness Contrast": "亮度对比度(&B)",
            "Fill Drawing Polygon": "绘制时填充多边形",

            # Dock 标题
            "Flags": "标志",
            "Polygon Labels": "多边形标签",
            "Label List": "标签列表",
            "File List": "文件列表",

            # 提示与状态
            "Select label to start annotating for it. Press 'Esc' to deselect.":
                "选择标签开始标注，按 Esc 取消选择。",
            "Search Filename": "搜索文件名",
            "%s started.": "%s 已启动",

            # 对话
            "Choose File": "选择文件",
            "Save annotations?": "保存标注？",
            'Save annotations to "{}" before closing?': '关闭前保存标注到“{}”？',
            "Attention": "注意",
            "You are about to permanently delete this label file, proceed anyway?":
                "您即将永久删除此标注文件，是否继续？",
            "You are about to permanently delete {} polygons, proceed anyway?":
                "您即将永久删除 {} 个多边形，是否继续？",

            # 错误
            "Error opening file": "打开文件错误",
            "No such file: <b>%s</b>": "文件不存在：<b>%s</b>",
            "Error reading %s": "读取错误 %s",
            "Invalid label": "无效标签",
            "Invalid label '{}' with validation type '{}'": "标签“{}”不符合验证类型“{}”",

            # 其他/文件对话
            "Open image or label file": "打开图像或标注文件",
            "Open next (hold Ctl+Shift to copy labels)": "打开下一张（按住 Ctrl+Shift 复制标签）",
            "Open prev (hold Ctl+Shift to copy labels)": "打开上一张（按住 Ctrl+Shift 复制标签）",
            "Save labels to file": "保存标注到文件",
            "Save labels to a different file": "另存标注到不同文件",
            "Delete current label file": "删除当前标注文件",
            "Change where annotations are loaded/saved": "更改标注加载/保存位置",
            "Save automatically": "自动保存",
            "Close current file": "关闭当前文件",
            'Toggle "keep previous annotation" mode': '切换“保持上一个标注”模式',
            "Start drawing polygons": "开始绘制多边形",
            "Start drawing rectangles": "开始绘制矩形",
            "Start drawing circles": "开始绘制圆形",
            "Start drawing lines": "开始绘制直线",
            "Start drawing points": "开始绘制点",
            "Start drawing linestrip. Ctrl+LeftClick ends creation.":
                "开始绘制线段，Ctrl+左键结束绘制。",
            "Move and edit the selected polygons": "移动和编辑选中的多边形",
            "Delete the selected polygons": "删除选中的多边形",
            "Create a duplicate of the selected polygons": "创建选中多边形的副本",
            "Copy selected polygons to clipboard": "复制选中多边形到剪贴板",
            "Paste copied polygons": "粘贴已复制的多边形",
            "Undo last drawn point": "撤销最后绘制的点",
            "Undo last add and edit of shape": "撤销上一次添加或编辑",
            "Remove selected point from polygon": "从多边形中删除选中点",
            "Hide all polygons": "隐藏所有多边形",
            "Show all polygons": "显示所有多边形",
            "Toggle all polygons": "切换所有多边形",
            "Show tutorial page": "显示教程页面",
            "Zoom in or out of the image. Also accessible with {} and {} from the canvas.":
                "放大或缩小图像，也可在画布通过 {} 和 {} 操作。",
            "Increase zoom level": "增加缩放级别",
            "Decrease zoom level": "降低缩放级别",
            "Zoom to original size": "缩放到原始大小",
            "Keep previous zoom scale": "保持上一缩放比例",
            "Zoom follows window size": "缩放跟随窗口大小",
            "Zoom follows window width": "缩放跟随窗口宽度",
            "Adjust brightness and contrast": "调整亮度和对比度",
            "Modify the label of the selected polygon": "修改选中多边形的标签",
            "Fill polygon while drawing": "绘制时填充多边形",
            "Quit application": "退出应用程序",
            "Loading %s...": "正在加载 %s...",
            "Loaded %s": "已加载 %s",
            "Image & Label files (%s)": "图像和标注文件（%s）",
            "%s - Choose Image or Label file": "%s - 选择图像或标注文件",
            "%s - Save/Load Annotations in Directory": "%s - 在目录中保存/加载标注",
            "%s . Annotations will be saved/loaded in %s": "%s。标注将在 %s 中保存/加载",
            "%s - Choose File": "%s - 选择文件",
            "Label files (*%s)": "标注文件（*%s）",
            "%s - Open Directory": "%s - 打开目录",
            "Zoom": "缩放",
            "Keep Previous Brightness/Contrast": "保持上一亮度/对比度",
            # AI 扩展
            "Create AI-Polygon": "创建 AI 多边形",
            "Create AI-Mask": "创建 AI 遮罩",
            "Start drawing ai_polygon. Ctrl+LeftClick ends creation.": "开始绘制 AI 多边形，Ctrl+左键结束。",
            "Start drawing ai_mask. Ctrl+LeftClick ends creation.": "开始绘制 AI 遮罩，Ctrl+左键结束。",
            "AI Mask Model": "AI 遮罩模型",
            "&Tutorial": "教程(&T)",
        }
        try:
            return translations.get(text, super().tr(text))
        except Exception:
            return translations.get(text, text)

    # -------------------- 自动标注动作 --------------------
    def _create_auto_annotate_action(self):
        try:
            from labelme import utils  # type: ignore

            def run_auto():
                try:
                    self._auto_annotate_current()
                except Exception as e:
                    QMessageBox.warning(self, "自动标注失败", f"执行自动标注时出错:\n{e}")

            return utils.newAction(
                self,
                text="自动标注当前图片",
                slot=run_auto,
                icon=None,
                tip="使用预加载模型对当前图片进行自动标注",
            )
        except Exception:
            return None

    def _create_auto_annotate_dir_action(self):
        try:
            from labelme import utils  # type: ignore

            def run_auto_dir():
                try:
                    self._auto_annotate_directory()
                except Exception as e:
                    QMessageBox.warning(self, "自动标注失败", f"执行目录自动标注时出错:\n{e}")

            return utils.newAction(
                self,
                text="自动标注整个目录",
                slot=run_auto_dir,
                icon=None,
                tip="使用预加载模型对当前目录的所有图片进行自动标注",
            )
        except Exception:
            return None

    # -------------------- 工具函数 --------------------
    def _get_current_image_path(self) -> Optional[str]:
        # 常见属性尝试
        for attr in ("filename", "imagePath", "current_filename"):
            p = getattr(self, attr, None)
            if isinstance(p, str) and p:
                return os.path.abspath(p)
        # 列表 + 当前行
        try:
            image_list: List[str] = getattr(self, "imageList", None)
            list_widget = getattr(self, "imageListWidget", None)
            if image_list and list_widget is not None:
                row = list_widget.currentRow()
                if 0 <= row < len(image_list):
                    return os.path.abspath(image_list[row])
        except Exception:
            pass
        return None

    def _get_current_directory(self) -> Optional[str]:
        p = self._get_current_image_path()
        if p:
            return os.path.dirname(p)
        try:
            image_list: List[str] = getattr(self, "imageList", None)
            if image_list:
                return os.path.dirname(os.path.abspath(image_list[0]))
        except Exception:
            pass
        return None

    def _ensure_ai_loaded(self) -> None:
        if getattr(self, "_ai_model", None) is not None:
            return
        if not self._ai_model_path:
            raise RuntimeError(
                "未配置AI模型路径（config['ai_model'] 或 环境变量 SLDMV_YOLO_MODEL）"
            )
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as e:
            raise RuntimeError(f"未安装 ultralytics 库: {e}")
        self._ai_model = YOLO(self._ai_model_path)

    def _predict_to_shapes(self, result) -> List[dict]:
        shapes: List[dict] = []
        names = getattr(self._ai_model, "names", None) or {}
        if hasattr(result, "boxes") and result.boxes is not None:
            xyxy = result.boxes.xyxy.cpu().numpy().astype(float)
            cls = result.boxes.cls.cpu().numpy().astype(int)
            for i in range(xyxy.shape[0]):
                x1, y1, x2, y2 = xyxy[i].tolist()
                label = str(names.get(int(cls[i]), int(cls[i])))
                shapes.append(
                    {
                        "label": label,
                        "points": [[float(x1), float(y1)], [float(x2), float(y2)]],
                        "group_id": None,
                        "shape_type": "rectangle",
                        "flags": {},
                    }
                )
        return shapes

    # -------------------- 自动标注逻辑 --------------------
    def _auto_annotate_current(self) -> None:
        img_path = self._get_current_image_path()
        if not img_path or not os.path.exists(img_path):
            raise RuntimeError("未找到当前图片，请先打开图片或目录")

        self._ensure_ai_loaded()
        results = self._ai_model.predict(
            img_path, conf=float(getattr(self, "_ai_conf", 0.25)), verbose=False
        )
        if not results:
            raise RuntimeError("模型无返回结果")
        shapes = self._predict_to_shapes(results[0])

        from PIL import Image
        with Image.open(img_path) as im:
            width, height = im.size

        data = {
            "version": "5.0.1",
            "flags": {},
            "shapes": shapes,
            "imagePath": os.path.basename(img_path),
            "imageData": None,
            "imageHeight": int(height),
            "imageWidth": int(width),
        }
        json_path = os.path.splitext(img_path)[0] + ".json"
        import json
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        try:
            if hasattr(self, "loadFile") and callable(getattr(self, "loadFile")):
                self.loadFile(img_path)
            elif hasattr(self, "openFile") and callable(getattr(self, "openFile")):
                self.openFile(img_path)
        except Exception:
            pass

        QMessageBox.information(self, "自动标注完成", f"已生成标注: {json_path}")

    def _auto_annotate_directory(self) -> None:
        dir_path = self._get_current_directory()
        if not dir_path or not os.path.isdir(dir_path):
            raise RuntimeError("未找到当前目录，请先打开目录或图片")

        images: List[str] = []
        try:
            image_list: List[str] = getattr(self, "imageList", None) or []
            images = [os.path.abspath(p) for p in image_list if os.path.isfile(p)]
        except Exception:
            images = []
        if not images:
            valid_ext = {".jpg", ".jpeg", ".png", ".bmp"}
            for name in sorted(os.listdir(dir_path)):
                p = os.path.join(dir_path, name)
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in valid_ext:
                    images.append(os.path.abspath(p))
        if not images:
            raise RuntimeError("目录中未找到可用图片")

        resp = QMessageBox.question(
            self,
            "确认目录自动标注",
            f"将对目录中 {len(images)} 张图片执行自动标注，继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resp != QMessageBox.Yes:
            return

        progress = QProgressDialog("正在自动标注目录...", "取消", 0, len(images), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(True)
        progress.show()
        QApplication.processEvents()

        self._ensure_ai_loaded()

        import json
        from PIL import Image

        for i, img_path in enumerate(images, start=1):
            if progress.wasCanceled():
                break
            progress.setValue(i - 1)
            progress.setLabelText(f"处理 {os.path.basename(img_path)} ({i}/{len(images)})")
            QApplication.processEvents()
            try:
                results = self._ai_model.predict(
                    img_path, conf=float(getattr(self, "_ai_conf", 0.25)), verbose=False
                )
                if not results:
                    continue
                shapes = self._predict_to_shapes(results[0])
                with Image.open(img_path) as im:
                    width, height = im.size
                data = {
                    "version": "5.0.1",
                    "flags": {},
                    "shapes": shapes,
                    "imagePath": os.path.basename(img_path),
                    "imageData": None,
                    "imageHeight": int(height),
                    "imageWidth": int(width),
                }
                json_path = os.path.splitext(img_path)[0] + ".json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                continue

        progress.setValue(len(images))
        cur = self._get_current_image_path()
        if cur:
            try:
                if hasattr(self, "loadFile") and callable(getattr(self, "loadFile")):
                    self.loadFile(cur)
                elif hasattr(self, "openFile") and callable(getattr(self, "openFile")):
                    self.openFile(cur)
            except Exception:
                pass
        QMessageBox.information(self, "目录自动标注", "目录自动标注已完成。")

    # ========== 修复后的中文映射（覆盖上方旧版） ==========
    def tr(self, text: str) -> str:  # type: ignore[override]
        translations = {
            # 顶部菜单
            "&File": "文件(&F)",
            "&Edit": "编辑(&E)",
            "&View": "视图(&V)",
            "&Help": "帮助(&H)",

            # 文件/导航
            "&Open": "打开(&O)",
            "&Open\n": "打开(&O)\n",
            "Open Dir\n": "打开目录(&O)",
            "Open Directory": "打开目录",
            "&Open Directory": "打开目录(&O)",
            "Open\nDir": "打开\n目录",
            "&Open\nDir": "打开(&O)\n目录",
            "Brightness Contrast": "亮度/对比度",
            "Brightness\nContrast": "亮度\n对比度",
            "&Brightness\nContrast": "亮度(&B)\n对比度",
            "Open Dir...": "打开目录...",
            "Open Directory...": "打开目录...",
            "Open &Recent": "打开最近(&R)",
            "&Next Image": "下一张(&N)",
            "&Prev Image": "上一张(&P)",
            "&Save": "保存(&S)",
            "&Save\n": "保存(&S)\n",
            "&Save As": "另存为(&A)",
            "&Close": "关闭(&C)",
            "&Delete File": "删除文件(&D)",
            "&Quit": "退出(&Q)",
            "&Change Output Dir": "更改输出目录(&C)",
            "Change Output Dir": "更改输出目录",
            "Save &Automatically": "自动保存(&A)",
            "Save With Image Data": "在标注文件中保存图像数据",
            "Save automatically": "自动保存",
            "Save image data in label file": "在标注文件中保存图像数据",

            # 绘制/编辑工具
            "Create Polygons": "创建多边形",
            "Create Rectangle": "创建矩形",
            "Create Circle": "创建圆形",
            "Create Line": "创建直线",
            "Create Point": "创建点",
            "Create LineStrip": "创建折线",
            "Edit Polygons": "编辑多边形",
            "Delete Polygons": "删除多边形",
            "Duplicate Polygons": "复制多边形",
            "Copy Polygons": "复制多边形到剪贴板",
            "Paste Polygons": "粘贴多边形",
            "Undo last point": "撤销上一个点",
            "Undo\n": "撤销\n",
            "Remove Selected Point": "删除选中点",
            "&Edit Label": "编辑标签(&E)",
            "Keep Previous Annotation": "保持上一张标注",

            # 视图/缩放/显示
            "&Hide\nPolygons": "隐藏多边形(&H)\n",
            "&Show\nPolygons": "显示多边形(&S)\n",
            "&Toggle\nPolygons": "切换多边形(&T)\n",
            "Zoom &In": "放大(&I)",
            "&Zoom Out": "缩小(&O)",
            "&Original size": "原始大小(&O)",
            "&Keep Previous Scale": "保持上次缩放(&K)",
            "&Fit Window": "适应窗口(&F)",
            "Fit &Width": "适应宽度(&W)",
            "&Brightness Contrast": "亮度/对比度(&B)",
            "Fill Drawing Polygon": "绘制时填充多边形",
            "Zoom": "缩放",
            "Increase zoom level": "放大",
            "Decrease zoom level": "缩小",
            "Zoom to original size": "原始大小",
            "Keep Previous Brightness/Contrast": "保持上次亮度/对比度",
            "Zoom follows window size": "随窗口大小缩放",
            "Zoom follows window width": "随窗口宽度缩放",

            # Dock / 面板
            "Flags": "标志",
            "Polygon Labels": "多边形标签",
            "Label List": "标签列表",
            "File List": "文件列表",

            # 状态/提示
            "Select label to start annotating for it. Press 'Esc' to deselect.":
                "选择标签以开始标注，按 Esc 取消选择。",
            "Search Filename": "搜索文件名",
            "%s started.": "%s 已启动。",

            # 对话框与文件选择
            "Open image or label file": "打开图像或标注文件",
            "Open next (hold Ctl+Shift to copy labels)": "打开下一张（按住 Ctrl+Shift 复制标签）",
            "Open prev (hold Ctl+Shift to copy labels)": "打开上一张（按住 Ctrl+Shift 复制标签）",
            "Save labels to file": "保存标注到文件",
            "Save labels to a different file": "保存标注为其他文件",
            "Delete current label file": "删除当前标注文件",
            "Change where annotations are loaded/saved": "更改标注的加载/保存位置",
            "Close current file": "关闭当前文件",
            'Toggle "keep previous annotation" mode': '切换“保持上一张标注”模式',
            "Start drawing polygons": "开始绘制多边形",
            "Start drawing rectangles": "开始绘制矩形",
            "Start drawing circles": "开始绘制圆形",
            "Start drawing lines": "开始绘制直线",
            "Start drawing points": "开始绘制点",
            "Start drawing linestrip. Ctrl+LeftClick ends creation.":
                "开始绘制折线，Ctrl+左键结束创建。",
            "Move and edit the selected polygons": "移动并编辑已选多边形",
            "Delete the selected polygons": "删除已选多边形",
            "Create a duplicate of the selected polygons": "创建已选多边形的副本",
            "Copy selected polygons to clipboard": "复制已选多边形到剪贴板",
            "Paste copied polygons": "粘贴已复制的多边形",
            "Undo last drawn point": "撤销上一绘制点",
            "Undo last add and edit of shape": "撤销上次添加/编辑形状",
            "Remove selected point from polygon": "从多边形移除选中点",
            "Hide all polygons": "隐藏所有多边形",
            "Show all polygons": "显示所有多边形",
            "Toggle all polygons": "切换显示所有多边形",
            "Show tutorial page": "显示教程页面",
            "Adjust brightness and contrast": "调整亮度和对比度",
            "Modify the label of the selected polygon": "修改所选多边形的标签",
            "Fill polygon while drawing": "绘制时填充多边形",
            "Quit application": "退出程序",

            # I/O 提示
            "Loading %s...": "正在加载 %s...",
            "Loaded %s": "已加载 %s",
            "Image & Label files (%s)": "图像与标注文件（%s）",
            "%s - Choose Image or Label file": "%s - 选择图像或标注文件",
            "%s - Save/Load Annotations in Directory": "%s - 在目录中保存/加载标注",
            "%s . Annotations will be saved/loaded in %s": "%s。标注将保存/加载于 %s",
            "%s - Choose File": "%s - 选择文件",
            "Label files (*%s)": "标注文件(*%s)",
            "%s - Open Directory": "%s - 打开目录",
            "%s - Open Dir": "%s - 打开目录",

            # 错误与确认
            "Error opening file": "打开文件错误",
            "No such file: <b>%s</b>": "文件不存在：<b>%s</b>",
            "Error reading %s": "读取错误 %s",
            "Invalid label": "无效标签",
            "Invalid label '{}' with validation type '{}'": "标签“{}”与校验类型“{}”不匹配",
            "Choose File": "选择文件",
            "Save annotations?": "保存标注？",
            'Save annotations to "{}" before closing?': '关闭前将标注保存到“{}”？',
            "Attention": "注意",
            "You are about to permanently delete this label file, proceed anyway?":
                "即将永久删除该标注文件，是否继续？",
            "You are about to permanently delete {} polygons, proceed anyway?":
                "即将永久删除 {} 个多边形，是否继续？",

            # AI 扩展（若被 labelme 暴露）
            "Create AI-Polygon": "创建 AI 多边形",
            "Create AI-Mask": "创建 AI 掩膜",
            "Start drawing ai_polygon. Ctrl+LeftClick ends creation.": "开始绘制 AI 多边形，Ctrl+左键结束。",
            "Start drawing ai_mask. Ctrl+LeftClick ends creation.": "开始绘制 AI 掩膜，Ctrl+左键结束。",
            "AI Mask Model": "AI 掩膜模型",
            "&Tutorial": "教程(&T)",
        }
        # 补充常见未覆盖的变体键
        translations.update({
            "Open\nDir": "打开\n目录",
            "&Open\nDir": "打开(&O)\n目录",
            "Brightness Contrast": "亮度/对比度",
            "Brightness\nContrast": "亮度\n对比度",
            "&Brightness\nContrast": "亮度(&B)\n对比度",
            "Undo": "撤销",
            "&Undo": "撤销(&U)",
        })
        try:
            return translations.get(text, super().tr(text))
        except Exception:
            return translations.get(text, text)
