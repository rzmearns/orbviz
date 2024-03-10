import sys
from PyQt5 import QtWidgets, QtCore
from satplot.visualiser.controls import controls, widgets
from satplot.visualiser import canvaswrapper
import satplot.visualiser.controls.console as console

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self, canvas_wrapper: canvaswrapper.CanvasWrapper,
			  			action_dict=None,
						title="",
						*args, **kwargs):
		super().__init__(*args, **kwargs)
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()

		opt_vsplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
		opt_vsplitter.setObjectName('opt_vsplitter')
		opt_vsplitter.setStyleSheet('''
					QSplitter#opt_vsplitter::handle {
							  	background-color: #DCDCDC;
							}
							  ''')
		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
							  	background-color: #DCDCDC;
							}
							  ''')
		content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()
		window_vsplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
		window_vsplitter.setObjectName('window_vsplitter')
		window_vsplitter.setStyleSheet('''
					QSplitter#window_vsplitter::handle {
							  	background-color: #DCDCDC;
							}
							  ''')

		self.setWindowTitle(title)

		# Prep config area
		self.orbit_controls = controls.OrbitConfigs()
		self._config_controls = controls.OptionConfigs(canvas_wrapper.assets)
		# Build config area layout
		'''
		#
		-
		#
		'''
		opt_vsplitter.addWidget(self.orbit_controls)
		opt_vsplitter.addWidget(self._config_controls)

		# Prep canvas area
		self._canvas_wrapper = canvas_wrapper
		# Build display area layout
		'''
		# | ###
		- | ###
		# | ###
		'''
		disp_hsplitter.addWidget(opt_vsplitter)
		disp_hsplitter.addWidget(self._canvas_wrapper.canvas.native)

		# Prep time slider area
		self._time_slider = widgets.TimeSlider()
		self._time_slider.setFixedHeight(50)
		# Build area down to bottom of time slider
		'''
		# | ###
		- | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addWidget(self._time_slider)
		content_widget.setLayout(content_vlayout)

		# Prep console area
		self._console = console.Console()
		console.consolefp = console.EmittingConsoleStream(textWritten=self._console.writeOutput)
		sys.stderr = console.EmittingConsoleStream(textWritten=self._console.writeErr)
		# Build main layout
		'''
		# | ###
		- | ###
		# | ###
		#######
		-------
		#######
		'''
		window_vsplitter.addWidget(content_widget)
		window_vsplitter.addWidget(self._console)
		# window_vsplitter.setHandleWidth(10)
		main_layout.addWidget(window_vsplitter)
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		# self.toolbar = controls.Toolbar(self, action_dict)

	# 	# Connect desired controls
	# 	self._connectControls()

	# def _connectControls(self):
	# 	# self._config_controls.eq_c_chooser.currentColorChanged.connect(
	# 	# 	self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)
	# 	# self._config_controls.eq_c_chooser.add_connect(self._canvas_wrapper.assets['earth'].visuals['parallels'].setEquatorColour)
	# 	self._time_slider.add_connect(self._canvas_wrapper.assets['earth'].setCurrentECEFRotation)
	# 	self._time_slider.add_connect(self._canvas_wrapper.assets['primary_orbit'].updateIndex)
		
	def printCol(self,val):
		print(val)

	def __del__(self):
		sys.stderr = sys.__stderr__

	def closeEvent(self, event):
		sys.stderr = sys.__stderr__
		self.closing.emit()
		return super().closeEvent(event)