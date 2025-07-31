import logging
import pathlib
from PyQt5 import QtWidgets, QtCore, QtGui
from typing import Any

import satplot.model.data_models.data_types as data_types
from satplot.model.data_models.history_data import HistoryData
from satplot.model.data_models.earth_raycast_data import (EarthRayCastData)
from satplot.visualiser.contexts.base_context import (BaseContext, BaseControls)
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)
import satplot.visualiser.contexts.canvas_wrappers.sensor_views_cw as sensor_views_cw
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.dialogs as satplot_dialogs
import satplot.visualiser.interface.widgets as widgets


logger = logging.getLogger(__name__)

class SensorViewsContext(BaseContext):
	data_type = [data_types.DataType.HISTORY,
				data_types.DataType.PLANETARYRAYCAST]
	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow, history_data:HistoryData, raycast_data:EarthRayCastData):
		super().__init__(name)
		self.window = parent_window
		self.data: dict[str,Any] = {}
		self.data['history'] = history_data
		self.data['raycast_src'] = raycast_data
		self._validateDataType()

		self.canvas_wrapper = sensor_views_cw.SensorViewsCanvasWrapper()
		self.canvas_wrapper.setModel(self.data['history'], self.data['raycast_src'])
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
		content_vlayout.addWidget(self.controls.time_slider)
		content_widget.setLayout(content_vlayout)

		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def connectControls(self) -> None:
		self.data['history'].data_ready.connect(self._updateDataSources)
		self.data['history'].data_ready.connect(self._updateControls)
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.sensor_view_selectors.selected.connect(self.setViewActiveSensor)
		self.controls.sensor_view_selectors.generate.connect(self.generateSensorFullRes)

	def _validateDataType(self) -> None:
		if self.data['history'] is not None and self.data['history'].getType() not in self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['history'].getType()}")
			console.sendErr(f"\t should be one of: {self.data_type}")
		if self.data['raycast_src'] is not None and self.data['raycast_src'].getType() not in self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['raycast_src'].getType()}")
			console.sendErr(f"\t should be one of: {self.data_type}")

	def _configureData(self) -> None:
		pass

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))
		self.controls.updateSensorViewLists()

	def _updateDataSources(self) -> None:
		self.canvas_wrapper.modelUpdated()
		self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data['history'] is None:
			logger.warning(f"model history data is not set for context {self.config['name']}:{self}")
			ValueError(f"model history data is not set for context {self.config['name']}:{self}")
		self.canvas_wrapper.updateIndex(index)
		self.data['history'].updateIndex(index)
		self.canvas_wrapper.recomputeRedraw()

	def setViewActiveSensor(self, view_id:int, sc_id:int, suite_key:str, sens_key:str) -> None:
		self.canvas_wrapper.selectSensor(view_id, sc_id, suite_key, sens_key)

	def generateSensorFullRes(self, view_id:int, sc_id:int, suite_key:str, sens_key:str) -> None:
		logger.debug(f'Generating Full Res for view {view_id}: {sc_id} - {suite_key} - {sens_key}')
		img_data, mo_data, moConverterFunction, img_metadata = self.canvas_wrapper.generateSensorFullRes(sc_id, suite_key, sens_key)
		img_dialog = satplot_dialogs.fullResSensorImageDialog(img_data, mo_data, moConverterFunction, img_metadata)

	def getIndex(self) -> int|None:
		return self.controls.time_slider.getValue()

	def setIndex(self, idx:int) -> None:
		self.controls.time_slider.setValue(idx)

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass
		
	def setupGIFDialog(self):
		pass

	def saveGif(self, file: pathlib.Path, loop=True, *args, **kwargs):
		pass


class Controls(BaseControls):
	def __init__(self, parent_context:BaseContext, canvas_wrapper: BaseCanvas|None) -> None:
		self.context = parent_context
		self.cw = canvas_wrapper
		super().__init__(self.context.config['name'])
		self.config_tabs = QtWidgets.QTabWidget()
		# Prep config widgets
		self.sensor_view_selectors = controls.SensorViewConfigs()
		self.config_controls = controls.OptionConfigs(self.cw.assets)
		# Wrap config widgets in tabs
		self.config_tabs.addTab(self.sensor_view_selectors, 'Select Linked Sensors')
		self.config_tabs.addTab(self.config_controls, 'Visual Options')
		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])

		self.setHotkeys()

	def setHotkeys(self):
		self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.widget)
		self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
		self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.widget)
		self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
		self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.widget)
		self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
		self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.widget)
		self.shortcuts['End'].activated.connect(self.time_slider.setEnd)

	def updateSensorViewLists(self):
		if self.context.data['history'].getConfigValue('is_pointing_defined'):
			sens_dict = self.context.data['history'].getPrimaryConfig().serialiseAllSensors()
		else:
			sens_dict = {}

		self.sensor_view_selectors.setSelectorLists(sens_dict)

	def rebuildOptions(self):
		self.config_controls.rebuild()