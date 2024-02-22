from PyQt5 import QtWidgets, QtCore

COLOUR_CHOICES = ['red', 'blue', 'green']

class Controls(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		layout = QtWidgets.QVBoxLayout()

		self.eq_c_label = QtWidgets.QLabel("Equator Colour:")
		layout.addWidget(self.eq_c_label)
		self.eq_c_chooser = QtWidgets.QComboBox()
		self.eq_c_chooser.addItems(COLOUR_CHOICES)
		layout.addWidget(self.eq_c_chooser)

		self.setLayout(layout)
	
		layout.addStretch(1)
		self.setLayout(layout)