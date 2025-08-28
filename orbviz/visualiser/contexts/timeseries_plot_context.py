import pathlib

from typing import Any

from PyQt5 import QtCore, QtWidgets

from orbviz.model.data_models.groundstation_data import GroundStationCollection
from orbviz.model.data_models.history_data import HistoryData
from orbviz.visualiser.contexts.base_context import BaseContext, BaseControls
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
from orbviz.visualiser.contexts.figure_wrappers import timeseries_plot_fw
import orbviz.visualiser.interface.controls as controls
import orbviz.visualiser.interface.widgets as widgets


class TimeSeriesContext(BaseContext):
	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow,
					history_data:HistoryData,
					groundstation_data:GroundStationCollection):
		super().__init__(name)
		self.window = parent_window

		self.data: dict[str, Any] = {}
		self.data['history'] = history_data
		self.data['groundstations'] = groundstation_data

		self.canvas_wrapper = timeseries_plot_fw.TimeSeriesPlotFigureWrapper()
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

		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		disp_hsplitter.addWidget(self.canvas_wrapper.getCanvas())

		# Build area down to bottom of time slider
		'''
		# | ###
		# | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addWidget(self.controls.time_slider)
		content_widget.setLayout(content_vlayout)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def connectControls(self) -> None:
		pass

	def _configureData(self) -> None:
		pass

	def getTimeSliderIndex(self) -> int|None:
		return None

	def setIndex(self, idx:int) -> None:
		pass

	def getIndex(self) -> int:
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
		self.config_controls = controls.OptionConfigs({})

		self.config_tabs = QtWidgets.QTabWidget()
		self.config_tabs.addTab(self.config_controls, 'Visual Options')

		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])