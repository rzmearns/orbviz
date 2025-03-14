from PyQt5 import QtWidgets, QtCore

from satplot.visualiser.contexts.base_context import (BaseContext, BaseControls)
import satplot.visualiser.interface.controls as controls
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)
import satplot.visualiser.contexts.canvas_wrappers.sensor_view3d_cw as sensor_view_cw


class SensorView3DContext(BaseContext):
	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow):
		super().__init__(name)
		self.window = parent_window

		self.canvas_wrapper = sensor_view_cw.SensorView3DCanvasWrapper()
		self.controls = Controls(self, self.canvas_wrapper)

		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
								background-color: #DCDCDC;
							}
							''')
		content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()

		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		disp_hsplitter.addWidget(self.canvas_wrapper.getCanvas().native)

		# Build area down to console
		'''
		# | ###
		# | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_widget.setLayout(content_vlayout)

		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def connectControls(self) -> None:
		pass

	def _configureData(self) -> None:
		pass

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass
		
class Controls(BaseControls):
	def __init__(self, parent_context:BaseContext, canvas_wrapper: BaseCanvas|None) -> None:
		self.context = parent_context
		super().__init__(self.context.config['name'])
		self.config_tabs = QtWidgets.QTabWidget()
		# Prep config widgets
		self.sensor_view_selectors = controls.SensorViewConfigs()
		# Wrap config widgets in tabs
		self.config_tabs.addTab(self.sensor_view_selectors, 'Select Linked Sensors')
		# Prep time slider

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])