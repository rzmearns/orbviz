from PyQt5 import QtWidgets, QtCore

from satplot.visualiser.contexts.base import (BaseContext, BaseControls)
import satplot.visualiser.interface.controls as controls
from satplot.visualiser.contexts.canvas_wrappers.base import (BaseCanvas)


class BlankContext(BaseContext):
	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow):
		super().__init__(name)
		self.window = parent_window

		self.canvas_wrapper = None
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

		# Prep config widgets

		# Wrap config widgets in tabs

		# Prep time slider

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])