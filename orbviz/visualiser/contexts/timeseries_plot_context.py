import logging
import pathlib

from typing import Any

from PyQt5 import QtCore, QtWidgets

from orbviz.model.data_models.groundstation_data import GroundStationCollection
from orbviz.model.data_models.history_data import HistoryData
from orbviz.model.data_models.timeseries import TimeSeries
from orbviz.visualiser.contexts.base_context import BaseContext, BaseControls
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
from orbviz.visualiser.contexts.figure_wrappers import timeseries_plot_fw
import orbviz.visualiser.interface.controls as controls
import orbviz.visualiser.interface.dialogs as dialogs
import orbviz.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class TimeSeriesContext(BaseContext):
	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow,
					history_data:HistoryData,
					timeseries_data:dict[str,TimeSeries]):
		super().__init__(name)
		self.window = parent_window

		self.data: dict[str, Any] = {}
		self.data['history'] = history_data
		self.data['timeseries'] = timeseries_data
		self.controls = Controls(self, self.canvas_wrapper)
		self.canvas_wrapper = timeseries_plot_fw.TimeSeriesPlotFigureWrapper()

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
		disp_hsplitter.addWidget(self.canvas_wrapper.widget)


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

		self.controls.axes_controls.build_axes.connect(self.canvas_wrapper.addAxes)
		self.controls.axes_controls.buildConfig()

		self.controls.axes_controls.add_series.connect(self.selectTimeSeries)

	def connectControls(self) -> None:
		logger.info("Connecting controls of %s", self.config['name'])
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)

	def setIndex(self, idx:int) -> None:
		self.controls.time_slider.setValue(idx)

	def getIndex(self) -> int:
		return self.controls.time_slider.getValue()

	def _updateDisplayedIndex(self, index:int) -> None:
		# self.canvas_wrapper.updateIndex(index)
		# self.canvas_wrapper.recomputeRedraw()
		pass

	def _updateDataSources(self) -> None:
		for ts in self.data['timeseries'].values():
			ts.update()
		self.canvas_wrapper.modelUpdated()
		# self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.blockSignals(True)
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data['history'].getTimespan().start)
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))
		self.controls.time_slider.blockSignals(False)

	def _procDataUpdated(self) -> None:
		self._updateControls()
		self._updateDataSources()

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass

	def saveGif(self, file:pathlib.Path, loop=True):
		pass

	def setupGIFDialog(self):
		pass

	def selectTimeSeries(self, ax_idx):
		enabled_timeseries = {}
		available_timeseries = self.data['timeseries'].copy()
		ax = self.canvas_wrapper.getAxes(ax_idx)
		for ts_key,ts in self.data['timeseries'].items():
			if ts.hasArtistForAxes(ax):
				enabled_timeseries[ts_key] = ts
				del available_timeseries[ts_key]

		d = dialogs.AddSeriesDialog(available_timeseries, enabled_timeseries)
		new_enabled = d.getNewEnabled()
		new_disabled = d.getNewDisabled()
		for ts_key in new_enabled:
			ts = self.data['timeseries'][ts_key]
			ts.addArtist(ax, self.canvas_wrapper.addTimeSeries(ax_idx, ts))

		for ts_key in new_disabled:
			ts = self.data['timeseries'][ts_key]
			handle = ts.popArtist(ax)
			if handle is not None:
				self.canvas_wrapper.removeTimeSeries(ax_idx,handle)

class Controls(BaseControls):
	def __init__(self, parent_context:BaseContext, canvas_wrapper: BaseCanvas|None) -> None:
		self.context = parent_context
		super().__init__(self.context.config['name'])

		# Prep config widgets
		self.config_controls = controls.OptionConfigs({})
		self.axes_controls = controls.TimeSeriesControls()
		self.config_tabs = QtWidgets.QTabWidget()
		self.config_tabs.addTab(self.axes_controls, 'Axes Options')
		self.config_tabs.addTab(self.config_controls, 'Visual Options')

		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])