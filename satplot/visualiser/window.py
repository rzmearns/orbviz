import sys
from PyQt5 import QtWidgets, QtCore
import satplot
from satplot.visualiser.controls import controls, widgets
from satplot.visualiser import canvaswrappers
import satplot.visualiser.controls.console as console

class MainWindow(QtWidgets.QMainWindow):
	closing = QtCore.pyqtSignal()

	def __init__(self, canvas_wrapper: canvaswrappers.History3D,
						title="",
			  			action_dict=None,
						*args, **kwargs):
		super().__init__(*args, **kwargs)
		print(f"{action_dict=}")
		main_widget = QtWidgets.QWidget()
		main_layout = QtWidgets.QVBoxLayout()
		self.toolbars = {}
		self.menubars = {}
		self.context_stack = QtWidgets.QTabWidget()
	
		self.toolbars['3D-history'] = controls.Toolbar(self, action_dict, context='3D-history')		
		self.menubars['3D-history'] = controls.Menubar(self, action_dict, context='3D-history')
		self.history3D = History3DContext(canvas_wrapper)
		self.context_stack.addTab(self.history3D.widget, '3D History')

		self.toolbars['blank'] = controls.Toolbar(self, action_dict, context='blank')
		self.menubars['blank'] = controls.Menubar(self, action_dict, context='blank')
		self.context_stack.addTab(QtWidgets.QWidget(), 'Blank')

		# check toolbar/menubar indices are the same
		for ii, key in enumerate(self.toolbars.keys()):
			if list(self.menubars.keys())[ii] != key:
				raise ValueError('Toolbars and Menubars indices do not match')
				# Should probably exit here

		self.context_stack.currentChanged.connect(self._changeToolbarsToContext)

		self.setWindowTitle(title)

		main_layout.addWidget(self.context_stack)
		main_widget.setLayout(main_layout)
		self.setCentralWidget(main_widget)

		self._changeToolbarsToContext(0)


	def embedIntoHBoxLayout(w, margin=5):
		"""Embed a widget into a layout to give it a frame"""
		result = QtWidgets.QWidget()
		layout = QtWidgets.QHBoxLayout(result)
		layout.setContentsMargins(margin, margin, margin, margin)
		layout.addWidget(w)
		return result

	def _changeToolbarsToContext(self, new_context_index):
		new_context_key = list(self.toolbars.keys())[new_context_index]
		console.send(f'Changing context to {new_context_key}')
		# process deselects first, need to clear parent pointer to menubar, otherwise menubar gets deleted
		for context_key in self.toolbars.keys():
			if context_key != new_context_key:
				self.toolbars[context_key].setActiveState(False)
				self.menubars[context_key].setActiveState(False)
		
		for context_key in self.toolbars.keys():
			if context_key == new_context_key:
				self.toolbars[context_key].setActiveState(True)
				self.menubars[context_key].setActiveState(True)

	def changeToMainContext(self):		
		self._changeToolbarsToContext(1)

	def changeTo3DHistoryContext(self):
		self._changeToolbarsToContext(0)

	def printCol(self,val):
		print(val)

	def __del__(self):
		sys.stderr = sys.__stderr__

	def closeEvent(self, event):
		sys.stderr = sys.__stderr__
		self.closing.emit()
		return super().closeEvent(event)
	
class History3DContext(QtWidgets.QWidget):
	def __init__(self, canvas_wrapper):
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
			if not satplot.debug:
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

			self.widget = QtWidgets.QWidget()
			self.layout = QtWidgets.QHBoxLayout(self.widget)
			self.layout.setContentsMargins(0, 0, 0, 0)
			self.layout.addWidget(window_vsplitter)