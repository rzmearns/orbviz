from PyQt5 import QtWidgets, QtCore
from satplot.visualiser.controls import controls, widgets
from satplot.visualiser import canvaswrapper

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self, canvas_wrapper: canvaswrapper.CanvasWrapper, title="", *args, **kwargs):
		super().__init__(*args, **kwargs)
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		disp_layout = QtWidgets.QHBoxLayout()
		opt_layout = QtWidgets.QVBoxLayout()

		self.setWindowTitle(title)

		# Prep config area
		self._orbit_controls = controls.OrbitConfigs()
		self._config_controls = controls.OptionConfigs(canvas_wrapper.assets)
		opt_layout.addWidget(self._orbit_controls)
		opt_layout.addWidget(self._config_controls)
		disp_layout.addLayout(opt_layout)

		# Prep canvas area
		self._canvas_wrapper = canvas_wrapper
		disp_layout.addWidget(self._canvas_wrapper.canvas.native)
		
		main_layout.addLayout(disp_layout)
		# Prep time slider area
		self._time_slider = widgets.TimeSlider()
		self._time_slider.setFixedHeight(50)
		main_layout.addWidget(self._time_slider)

		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		# Connect desired controls
		self._connectControls()

	def _connectControls(self):
		# self._config_controls.eq_c_chooser.currentColorChanged.connect(
		# 	self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)
		# self._config_controls.eq_c_chooser.add_connect(self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)
		self._time_slider.add_connect(self._canvas_wrapper.assets['earth'].setCurrentECEFRotation)
		
	def printCol(self,val):
		print(val)

	def closeEvent(self, event):
		self.closing.emit()
		return super().closeEvent(event)