import logging
import pathlib
import sys
from typing import Any
from PyQt5 import QtWidgets, QtCore, QtGui

import satplot.model.data_models.data_types as data_types
from satplot.model.data_models.history_data import HistoryData
from satplot.visualiser.contexts.base_context import (BaseContext, BaseControls)
import satplot.visualiser.interface.controls as controls
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)

import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class HistoryConfigurationContext(BaseContext):
	data_type = data_types.DataType.HISTORY

	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow, history_data:HistoryData):
		super().__init__(name)
		self.window = parent_window
		self.data: dict[str,Any] = {}
		self.data['history'] = history_data

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

		# Build config area layout
		'''
		## | ##
		## | ##
		## | ##
		'''
		disp_hsplitter.addWidget(self.controls.left_config_tabs)
		disp_hsplitter.addWidget(self.controls.right_config_tabs)
		# disp_hsplitter.addWidget()
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addLayout(self.controls.btn_hlayout)
		content_vlayout.addWidget(self.controls.time_slider)
		content_widget.setLayout(content_vlayout)

		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def _validateDataType(self) -> None:
		if self.data is not None and self.data['history'].getType() != self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['history'].getType()}")
			console.sendErr(f"\t should be: {self.data_type}")

	def connectControls(self) -> None:
		logger.info(f"Connecting controls of {self.config['name']}")
		self.controls.submit_button.clicked.connect(self._configureData)
		if self.data is None:
			logger.warning(f'Context History3D: {self} does not have a data model.')
			raise AttributeError(f'Context History3D: {self} does not have a data model.')
		self.data['history'].data_ready.connect(self._updateDataSources)
		self.data['history'].data_ready.connect(self._updateControls)
		self.data['history'].data_err.connect(self._resetControls)
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)

	def _configureData(self) -> None:
		logger.info(f'Setting up data configuration for context: {self}')
		console.send('Setting up data configuration')
		# Timespan configuration
		if self.data is None:
			logger.warning(f"model data is not set for context {self.config['name']}:{self}")
			raise ValueError(f"model data is not set for context {self.config['name']}:{self}")

		self.data['history'].updateConfig('timespan_period_start', self.controls.time_period_config.getPeriodStart())
		self.data['history'].updateConfig('timespan_period_end', self.controls.time_period_config.getPeriodEnd())
		self.data['history'].updateConfig('sampling_period', self.controls.time_period_config.getSamplingPeriod())
		# Primary orbits configuration
		try:
			self.data['history'].setPrimaryConfig(self.controls.prim_config.getConfig())
		except ValueError:
			console.sendErr("Primary Configuration not selected: Please select a configuration.")
			return

		# Supplemental configuration
		has_supplemental_constellation = self.controls.use_constellation_switch.isChecked()
		if has_supplemental_constellation:
			try:
				c_config = self.controls.constellation_config.getConfig()
			except ValueError:
				console.sendErr("Supplementary constellation enabled: Please select a constellation.")
				return

			self.data['history'].setSupplementalConstellation(c_config)
		else:
			self.data['history'].clearSupplementalConstellation()

		# Historical pointing
		if self.controls.pnting_defines_period_switch.isChecked():
			logger.info(f'Pointing defined. Setting pointing configuration for {self}')
			self.data['history'].updateConfig('is_pointing_defined', True)
			pointing_file_path = self.controls.pointing_config.getPointingConfig()
			if pointing_file_path is None or \
				pointing_file_path == '':
				console.sendErr("Displaying spacecraft pointing requires a pointing file.")
				return
			self.data['history'].updateConfig('pointing_defines_timespan', self.controls.pnting_defines_period_switch.isChecked())
			self.data['history'].updateConfig('pointing_file', pointing_file_path)
			self.data['history'].updateConfig('pointing_invert_transform', self.controls.pointing_config.isPointingTransformInverse())
		else:
			logger.info(f'Pointing not defined. Clearing pointing configuration for {self}')
			self.data['history'].updateConfig('is_pointing_defined', False)
			self.data['history'].updateConfig('pointing_defines_timespan', False)
			self.data['history'].updateConfig('pointing_file', None)
			self.data['history'].updateConfig('pointing_invert_transform', False)

		try:
			self.controls.submit_button.setEnabled(False)
			self.data['history'].process()
		except Exception as e:
			logger.warning(f"Error in configuring data for history3D: {e}")
			console.sendErr(f"Error in configuring data for history3D: {e}")
			self.controls.submit_button.setEnabled(True)
			raise e

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_period_config.period_start.setDatetime(self.data['history'].getConfigValue('timespan_period_start'))
		self.controls.time_period_config.period_end.setDatetime(self.data['history'].getConfigValue('timespan_period_end'))
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data['history'].getTimespan().start)
		self.controls.submit_button.setEnabled(True)
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))

	def _resetControls(self) -> None:
		self.controls.submit_button.setEnabled(True)

	def _updateDataSources(self) -> None:
		pass

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data['history'] is None:
			logger.warning(f"model history data is not set for context {self.config['name']}:{self}")
			ValueError(f"model history data is not set for context {self.config['name']}:{self}")
		self.data['history'].updateIndex(index)

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
		self.cw = None
		super().__init__(self.context.config['name'])

		# Prep config widgets
		self.prim_config = controls.PrimaryConfig()
		self.time_period_config = controls.TimePeriodConfig()
		self.pointing_config = controls.HistoricalPointingConfig()
		self.constellation_config = controls.ConstellationControls()
		dflt_time_dfntn_state = False
		self.pnting_defines_period_switch = widgets.LabelledSwitch(labels=('Use Manual Time Period','Use Pointing Data Defined Period'),dflt_state=dflt_time_dfntn_state)
		dflt_constellation_state = False
		self.use_constellation_switch = widgets.LabelledSwitch(labels=('','Use Supplemental Constellation'),dflt_state=dflt_constellation_state)
		self.submit_button = QtWidgets.QPushButton('Recalculate')

		# add config interconnects
		self.pnting_defines_period_switch.toggle.connect(self.toggleTimePeriodDefinitionMethod)
		self.toggleTimePeriodDefinitionMethod(dflt_time_dfntn_state)
		self.use_constellation_switch.toggle.connect(self.constellation_config.setEnabled)
		self.use_constellation_switch.toggle.connect(self._reloadConstellation)
		self.constellation_config.setEnabled(dflt_constellation_state)


		tp_selection_widget = QtWidgets.QWidget()
		tp_selection_vlayout = QtWidgets.QVBoxLayout()
		tp_selection_vlayout.addWidget(self.pnting_defines_period_switch)
		tp_selection_vlayout.addWidget(self.time_period_config)
		tp_selection_vlayout.addWidget(self.pointing_config)
		tp_selection_vlayout.addStretch()
		tp_selection_widget.setLayout(tp_selection_vlayout)

		const_selection_widget = QtWidgets.QWidget()
		const_selection_vlayout = QtWidgets.QVBoxLayout()
		const_selection_vlayout.addWidget(self.use_constellation_switch)
		const_selection_vlayout.addWidget(self.constellation_config)
		const_selection_vlayout.addStretch()
		const_selection_widget.setLayout(const_selection_vlayout)

		self.btn_hlayout = QtWidgets.QHBoxLayout()
		self.btn_hlayout.addStretch()
		self.btn_hlayout.addWidget(self.submit_button)
		self.btn_hlayout.addStretch()

		# Wrap config widgets in tabs
		self.left_config_tabs = QtWidgets.QTabWidget()
		self.left_config_tabs.addTab(self.prim_config, 'Primary Configuration')
		self.left_config_tabs.addTab(const_selection_widget, 'Constellation Configuration')

		self.right_config_tabs = QtWidgets.QTabWidget()
		self.right_config_tabs.addTab(tp_selection_widget, 'Time Period Configuration')

		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])

		self.setHotkeys()

	def toggleTimePeriodDefinitionMethod(self, new_state):
		self.time_period_config.setEnabled(not new_state)
		self.pointing_config.setEnabled(new_state)

	def setHotkeys(self):
		self.shortcuts={}
		self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.widget)
		self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
		self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.widget)
		self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
		self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.widget)
		self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
		self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.widget)
		self.shortcuts['End'].activated.connect(self.time_slider.setEnd)

	def _reloadConstellation(self, use_constellation_state:bool):
		if use_constellation_state:
			self.constellation_config.refresh()

	def prepSerialisation(self):
		state = {}
		# state['orbit_controls'] = self.orbit_controls.prepSerialisation()
		state['time_slider'] = self.time_slider.prepSerialisation()
		# add serialisation state variable tracking if using manual time or pointing time
		# add serialisation state variable tracking if using constellation
		return state

	def deSerialise(self, state):
		# self.orbit_controls.deSerialise(state['orbit_controls'])
		self.time_slider.deSerialise(state['time_slider'])