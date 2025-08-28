import logging

import typing

from PyQt5 import QtCore, QtWidgets

logger = logging.getLogger(__name__)

class CWContainer(QtWidgets.QWidget):
    entered = QtCore.pyqtSignal()
    left = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.num_widgets = 0
        self.setLayout(self.content_layout)

    def addWidget(self, widget:QtWidgets.QWidget) -> None:
        if self.num_widgets == 0:
            self.content_layout.addWidget(widget)
        else:
            logger.warning('CW Container already has a widget')

    def enterEvent(self, QEvent):
        self.entered.emit()

    def leaveEvent(self, QEvent):
        self.left.emit()
