"""
修改后的Labelme主窗口 - 中文化并移除品牌标识
这是对原labelme的最小化修改包装
"""
import sys
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer

try:
    from labelme.app import MainWindow as LabelmeMainWindowBase
    LABELME_AVAILABLE = True
except ImportError as e:
    print(f"Warning: labelme not available: {e}")
    LABELME_AVAILABLE = False
    LabelmeMainWindowBase = None


class LabelmeMainWindow(LabelmeMainWindowBase):
    """修改后的Labelme主窗口"""

    def __init__(self, config=None, filename=None, output=None,
                 output_file=None, output_dir=None):
        if not LABELME_AVAILABLE:
            raise ImportError("labelme模块未安装或不可用")
        
        try:
            super().__init__(config, filename, output, output_file, output_dir)
            
            # 修改窗口标题
            self.setWindowTitle("图像标注工具")
            
            # 延迟修改菜单，避免初始化时阻塞
            QTimer.singleShot(100, self._modify_menus)
            
        except Exception as e:
            print(f"Error initializing labelme: {e}")
            raise

    def _modify_menus(self):
        """修改菜单 - 移除about或替换内容"""
        try:
            # 检查必要的属性是否存在
            if not hasattr(self, 'actions') or not hasattr(self, 'menus'):
                print("Warning: actions or menus not available")
                return
                
            # 移除原有的about action
            if hasattr(self.actions, 'about'):
                # 替换about的处理函数
                self.actions.about = self._create_custom_about_action()

                # 重新构建Help菜单
                if hasattr(self.menus, 'help') and self.menus.help:
                    self.menus.help.clear()
                    help_action = self._create_help_action()
                    self.menus.help.addAction(help_action)
                    self.menus.help.addAction(self.actions.about)
        except Exception as e:
            print(f"Error modifying menus: {e}")
            # 不抛出异常，避免影响主程序

    def _create_custom_about_action(self):
        """创建自定义的About动作"""
        try:
            from labelme import utils

            def show_custom_about():
                QMessageBox.about(
                    self,
                    "关于",
                    """
<h3>图像标注工具</h3>
<p>用于目标检测的图像标注工具</p>
<p>支持多种标注形式：矩形、多边形、圆形等</p>
<p>基于开源项目 labelme 修改</p>
"""
                )

            return utils.newAction(
                self,
                text="关于(&A)",
                slot=show_custom_about,
                icon=None,
                tip="关于本软件"
            )
        except Exception as e:
            print(f"Error creating about action: {e}")
            return None

    def _create_help_action(self):
        """创建帮助动作"""
        try:
            from labelme import utils

            def show_help():
                help_text = """
<h3>快捷键说明</h3>
<table>
<tr><td><b>Ctrl+O</b></td><td>打开图像</td></tr>
<tr><td><b>Ctrl+D</b></td><td>打开目录</td></tr>
<tr><td><b>Ctrl+S</b></td><td>保存标注</td></tr>
<tr><td><b>A / D</b></td><td>上一张 / 下一张</td></tr>
<tr><td><b>R</b></td><td>矩形标注模式</td></tr>
<tr><td><b>P</b></td><td>多边形标注模式</td></tr>
<tr><td><b>E</b></td><td>编辑模式</td></tr>
<tr><td><b>Delete</b></td><td>删除选中标注</td></tr>
<tr><td><b>Ctrl+Z</b></td><td>撤销</td></tr>
<tr><td><b>Ctrl+C/V</b></td><td>复制/粘贴标注</td></tr>
</table>

<h3>使用说明</h3>
<p>1. 点击"打开目录"选择图像文件夹</p>
<p>2. 按R键进入矩形标注模式，或按P进入多边形模式</p>
<p>3. 在图像上拖动鼠标绘制标注框</p>
<p>4. 在弹出框中输入或选择类别名称</p>
<p>5. 标注会自动保存为JSON文件</p>
"""
                QMessageBox.about(self, "使用帮助", help_text)

            return utils.newAction(
                self,
                text="帮助(&H)",
                slot=show_help,
                icon="help",
                tip="查看使用帮助"
            )
        except Exception as e:
            print(f"Error creating help action: {e}")
            return None

    def tr(self, text):
        """翻译函数 - 将英文翻译为中文"""
        translations = {
            # 菜单
            "&File": "文件(&F)",
            "&Edit": "编辑(&E)",
            "&View": "视图(&V)",
            "&Help": "帮助(&H)",

            # 文件菜单
            "&Open\n": "打开(&O)\n",
            "Open Dir": "打开目录",
            "&Next Image": "下一张图像(&N)",
            "&Prev Image": "上一张图像(&P)",
            "&Save\n": "保存(&S)\n",
            "&Save As": "另存为(&A)",
            "&Close": "关闭(&C)",
            "&Delete File": "删除文件(&D)",
            "&Quit": "退出(&Q)",
            "Open &Recent": "最近打开(&R)",
            "&Change Output Dir": "更改输出目录(&C)",
            "Save &Automatically": "自动保存(&A)",
            "Save With Image Data": "保存图像数据",

            # 编辑菜单
            "Create Polygons": "创建多边形",
            "Create Rectangle": "创建矩形",
            "Create Circle": "创建圆形",
            "Create Line": "创建直线",
            "Create Point": "创建点",
            "Create LineStrip": "创建线段",
            "Edit Polygons": "编辑多边形",
            "Delete Polygons": "删除多边形",
            "Duplicate Polygons": "复制多边形",
            "Copy Polygons": "复制多边形",
            "Paste Polygons": "粘贴多边形",
            "Undo last point": "撤销上一点",
            "Undo\n": "撤销\n",
            "Remove Selected Point": "删除选中点",
            "&Edit Label": "编辑标签(&E)",
            "Keep Previous Annotation": "保持上一个标注",

            # 视图菜单
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
            "Fill Drawing Polygon": "填充绘制多边形",

            # Dock标题
            "Flags": "标志",
            "Polygon Labels": "多边形标签",
            "Label List": "标签列表",
            "File List": "文件列表",

            # 提示
            "Select label to start annotating for it. Press 'Esc' to deselect.":
                "选择标签开始标注。按Esc取消选择。",
            "Search Filename": "搜索文件名",

            # 状态栏
            "%s started.": "%s 已启动。",

            # 对话框
            "Choose File": "选择文件",
            "Save annotations?": "保存标注？",
            'Save annotations to "{}" before closing?': '关闭前保存标注到"{}"？',
            "Attention": "注意",
            "You are about to permanently delete this label file, proceed anyway?":
                "您即将永久删除此标注文件，是否继续？",
            "You are about to permanently delete {} polygons, proceed anyway?":
                "您即将永久删除{}个多边形，是否继续？",

            # 错误消息
            "Error opening file": "打开文件错误",
            "No such file: <b>%s</b>": "文件不存在: <b>%s</b>",
            "Error reading %s": "读取错误 %s",
            "Invalid label": "无效标签",
            "Invalid label '{}' with validation type '{}'": "标签'{}'不符合验证类型'{}'",

            # 其他
            "Open image or label file": "打开图像或标注文件",
            "Open next (hold Ctl+Shift to copy labels)": "打开下一张(按住Ctrl+Shift复制标签)",
            "Open prev (hold Ctl+Shift to copy labels)": "打开上一张(按住Ctrl+Shift复制标签)",
            "Save labels to file": "保存标注到文件",
            "Save labels to a different file": "另存标注到不同文件",
            "Delete current label file": "删除当前标注文件",
            "Change where annotations are loaded/saved": "更改标注加载/保存位置",
            "Save automatically": "自动保存",
            "Save image data in label file": "在标注文件中保存图像数据",
            "Close current file": "关闭当前文件",
            'Toggle "keep previous annotation" mode': '切换"保持上一标注"模式',
            "Start drawing polygons": "开始绘制多边形",
            "Start drawing rectangles": "开始绘制矩形",
            "Start drawing circles": "开始绘制圆形",
            "Start drawing lines": "开始绘制直线",
            "Start drawing points": "开始绘制点",
            "Start drawing linestrip. Ctrl+LeftClick ends creation.":
                "开始绘制线段。Ctrl+左键结束绘制。",
            "Move and edit the selected polygons": "移动和编辑选中的多边形",
            "Delete the selected polygons": "删除选中的多边形",
            "Create a duplicate of the selected polygons": "创建选中多边形的副本",
            "Copy selected polygons to clipboard": "复制选中多边形到剪贴板",
            "Paste copied polygons": "粘贴已复制的多边形",
            "Undo last drawn point": "撤销最后绘制的点",
            "Undo last add and edit of shape": "撤销上一次添加和编辑",
            "Remove selected point from polygon": "从多边形删除选中点",
            "Hide all polygons": "隐藏所有多边形",
            "Show all polygons": "显示所有多边形",
            "Toggle all polygons": "切换所有多边形",
            "Show tutorial page": "显示教程页面",
            "Zoom in or out of the image. Also accessible with {} and {} from the canvas.":
                "放大或缩小图像。也可以从画布使用{}和{}。",
            "Increase zoom level": "增加缩放级别",
            "Decrease zoom level": "减小缩放级别",
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
            "Image & Label files (%s)": "图像和标注文件 (%s)",
            "%s - Choose Image or Label file": "%s - 选择图像或标注文件",
            "%s - Save/Load Annotations in Directory": "%s - 在目录中保存/加载标注",
            "%s . Annotations will be saved/loaded in %s":
                "%s . 标注将在 %s 中保存/加载",
            "%s - Choose File": "%s - 选择文件",
            "Label files (*%s)": "标注文件 (*%s)",
            "%s - Open Directory": "%s - 打开目录",
            "Zoom": "缩放",
            "Keep Previous Brightness/Contrast": "保持上一亮度/对比度",
            "Create AI-Polygon": "创建AI多边形",
            "Create AI-Mask": "创建AI遮罩",
            "Start drawing ai_polygon. Ctrl+LeftClick ends creation.":
                "开始绘制AI多边形。Ctrl+左键结束绘制。",
            "Start drawing ai_mask. Ctrl+LeftClick ends creation.":
                "开始绘制AI遮罩。Ctrl+左键结束绘制。",
            "AI Mask Model": "AI遮罩模型",
            "&Tutorial": "教程(&T)",
        }

        return translations.get(text, super().tr(text))