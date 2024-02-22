from PyQt5 import QtWidgets, QtCore
from satplot.visualiser import controls
from satplot.visualiser import canvaswrapper

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self, canvas_wrapper: canvaswrapper.CanvasWrapper, *args, **kwargs):
		super().__init__(*args, **kwargs)
		central_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QHBoxLayout()

		# Prep control area
		self._controls = controls.Controls()
		main_layout.addWidget(self._controls)

		# Prep canvas area
		self._canvas_wrapper = canvas_wrapper
		main_layout.addWidget(self._canvas_wrapper.canvas.native)

		central_widget.setLayout(main_layout)
		self.setCentralWidget(central_widget)

		# Connect desired controls
		self._connectControls()

	def _connectControls(self):
		self._controls.eq_c_chooser.currentTextChanged.connect(
			self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)

	def closeEvent(self, event):
		self.closing.emit()
		return super().closeEvent(event)