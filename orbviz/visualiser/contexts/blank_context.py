import pathlib

from PyQt5 import QtCore, QtWidgets

from orbviz.visualiser.contexts.base_context import BaseContext, BaseControls
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import orbviz.visualiser.interface.controls as controls


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
		content_widget = QtWidgets.QWidget() 			# noqa: F841
		content_vlayout = QtWidgets.QVBoxLayout() 		# noqa: F841

	def connectControls(self) -> None:
		pass

	def _configureData(self) -> None:
		pass

	def getTimeSliderIndex(self) -> int|None:
		return None

	def setIndex(self, idx:int) -> None:
		pass

	def _procDataUpdated(self) -> None:
		pass

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass

	def saveGif(self, file:pathlib.Path, loop=True):
		pass

	def setupGIFDialog(self):
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