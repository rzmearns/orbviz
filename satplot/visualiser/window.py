from PyQt5 import QtWidgets, QtCore
from satplot.visualiser import controls
from satplot.visualiser import canvaswrapper

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self, canvas_wrapper: canvaswrapper.CanvasWrapper, *args, **kwargs):
		super().__init__(*args, **kwargs)
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		disp_layout = QtWidgets.QHBoxLayout()

		# Prep config area
		self._config_controls = controls.Controls()
		disp_layout.addWidget(self._config_controls)

		# Prep canvas area
		self._canvas_wrapper = canvas_wrapper
		disp_layout.addWidget(self._canvas_wrapper.canvas.native)
		
		main_layout.addLayout(disp_layout)
		# Prep time slider area
		self._time_slider = controls.TimeSlider()
		main_layout.addWidget(self._time_slider)

		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		# Connect desired controls
		self._connectControls()

	def _connectControls(self):
		self._config_controls.eq_c_chooser.currentTextChanged.connect(
			self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)
		

	def closeEvent(self, event):
		self.closing.emit()
		return super().closeEvent(event)