"""
界面层
"""
from .category_widget import CategoryWidget
from .label_widget import LabelWidget
from .main_window import MainWindow
from .predict_widget import PredictWidget
from .train_widget import TrainWidget

__all__ = [
    'MainWindow',
    'CategoryWidget',
    'LabelWidget',
    'TrainWidget',
    'PredictWidget'
]