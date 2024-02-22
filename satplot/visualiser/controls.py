from PyQt5 import QtWidgets, QtCore
import math
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

		self.setLayout(layout)

class TimeSlider(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.range = 2*math.pi
		self.num_ticks = 4
		self.range_per_tick = self.range/self.num_ticks
		self.callback = None
		layout = QtWidgets.QVBoxLayout()
		self.label = QtWidgets.QLabel("Rotation")
		self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slider.setMinimum(0)
		self.slider.setMaximum(self.num_ticks)
		self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
		self.slider.setTickInterval(1)
		layout.addWidget(self.label)
		layout.addWidget(self.slider)
		self.slider.valueChanged.connect(self._run_callback)
		self.setLayout(layout)
		layout.addStretch(1)
		self.setLayout(layout)

	def connect(self, callback):
		self.callback = callback

	def _run_callback(self):
		if self.callback is not None:
			self.callback(self.range_per_tick*self.slider.value())
		else:
			print("Time Slider callback is not set")