import datetime as dt
import json
import logging
import os
import pathlib
import string
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui
from vispy.scene.widgets import widget

import satplot.model.data_models.data_types as data_types
import satplot.util.paths as satplot_paths
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class PrimaryConfig(QtWidgets.QWidget):
	prim_config_dir = 'data/primary_configs/'

	def __init__(self, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)
		# Layout containers
		super_layout = QtWidgets.QVBoxLayout()
		# Need to keep a reference to pane_groupbox so we can update geometry when loading a different config
		self.pane_groupbox = QtWidgets.QGroupBox('Primary Satellite Configuration')
		config_vlayout = QtWidgets.QVBoxLayout()
		config_vlayout.setSpacing(10)

		# Configuration widgets
		dflt_config_file = satplot_paths.prim_cnfg_dir.joinpath('SpIRIT_XYNegZ.json')
		self.tmp_prim_config = None
		self.prim_config_selector = widgets.FilePicker('Configuration File',
															dflt_file=dflt_config_file.name,
															dflt_dir=dflt_config_file.parent,
															save=False)
		self.prim_config_display = widgets.PrimaryConfigDisplay()

		# Place configuration widgets
		config_vlayout.addWidget(self.prim_config_selector)
		config_vlayout.addWidget(self.prim_config_display)
		config_vlayout.addStretch()
		self.pane_groupbox.setLayout(config_vlayout)

		# Scrollable container
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidget(self.pane_groupbox)
		scroll_area.setWidgetResizable(True)

		super_layout.addWidget(scroll_area)
		self.setLayout(super_layout)

		# Set up connections
		self._loadTempConfig(dflt_config_file)
		self.prim_config_selector.add_connect(self._loadTempConfig)

	def _loadTempConfig(self, cnfg_file:pathlib.Path):
		try:
			self.tmp_prim_config = data_types.PrimaryConfig.fromJSON(cnfg_file)
			self.prim_config_display.updateConfig(self.tmp_prim_config)
			self.prim_config_selector.clearError()
		except KeyError as e:
			self.tmp_prim_config = None
			self.prim_config_selector.setError('Not a valid configuration file')
			self.prim_config_display.clearConfig()
		self.pane_groupbox.updateGeometry()

	def getConfig(self) -> data_types.PrimaryConfig:
		if self.tmp_prim_config is None:
			raise ValueError('A Primary Configuration has not been loaded yet.')
		return self.tmp_prim_config

class TimePeriodConfig(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)
		# Layout containers
		super_layout = QtWidgets.QVBoxLayout()
		pane_groupbox = QtWidgets.QGroupBox('Manual Time Period')
		config_vlayout = QtWidgets.QVBoxLayout()
		config_vlayout.setSpacing(10)

		# Configuration Widgets
		self.period_start = widgets.DatetimeEntry("Period Start:", dt.datetime.now(tz=dt.timezone.utc)-dt.timedelta(seconds=1.5*60*60))
		self.period_end = widgets.DatetimeEntry("Period End:", (dt.datetime.now(tz=dt.timezone.utc)+dt.timedelta(seconds=1.5*60*60)))
		self.sampling_period = widgets.PeriodBox("Sampling Period:", 30)

		# Place configuration widgets
		config_vlayout.addWidget(self.period_start)
		config_vlayout.addWidget(self.period_end)
		config_vlayout.addWidget(self.sampling_period)
		pane_groupbox.setLayout(config_vlayout)

		# Scrollable container
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidget(pane_groupbox)
		scroll_area.setWidgetResizable(True)

		super_layout.addWidget(scroll_area)
		self.setLayout(super_layout)

		# Set up connections

	def getPeriodStart(self) -> dt.datetime:
		return self.period_start.datetime

	def getPeriodEnd(self) -> dt.datetime:
		return self.period_end.datetime

	def getSamplingPeriod(self) -> int:
		return self.sampling_period.period

class HistoricalPointingConfig(QtWidgets.QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__()
		# Layout containers
		super_layout = QtWidgets.QVBoxLayout()
		pane_groupbox = QtWidgets.QGroupBox('Historical Pointing Data')
		config_vlayout = QtWidgets.QVBoxLayout()
		config_vlayout.setSpacing(10)
		inv_switch_vlayout = QtWidgets.QVBoxLayout()
		inv_switch_vlayout.setSpacing(0)

		# Configuration widgets
		dflt_config_file = satplot_paths.pnt_dir.joinpath('20240108_test_quaternion_X_ECI_parallel_Z_Zenith.csv')
		self._pointing_file_selector = widgets.FilePicker('Pointing File',
												   			dflt_file=dflt_config_file.name,
															dflt_dir=dflt_config_file.parent,
															save=False,
															margins=[0,0,0,0])
		self.pointing_file_inv_toggle = widgets.LabelledSwitch(labels=('BF->ECI','ECI->BF'), dflt_state=True)
		_label_font = QtGui.QFont()
		_label_font.setWeight(QtGui.QFont.Medium)
		pointing_file_inv_label = QtWidgets.QLabel('Pointing File frame transform direction:')
		pointing_file_inv_label.setFont(_label_font)

		# Place configuration widgets
		config_vlayout.addWidget(self._pointing_file_selector)
		inv_switch_vlayout.addWidget(pointing_file_inv_label)
		inv_switch_vlayout.addWidget(self.pointing_file_inv_toggle)
		config_vlayout.addLayout(inv_switch_vlayout)
		pane_groupbox.setLayout(config_vlayout)

		# Scrollable container
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidget(pane_groupbox)
		scroll_area.setWidgetResizable(True)

		super_layout.addWidget(scroll_area)
		self.setLayout(super_layout)

	def getPointingConfig(self) -> pathlib.Path:
		return self._pointing_file_selector.path

	def isPointingTransformInverse(self) -> bool:
		return self.pointing_file_inv_toggle.isChecked()

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['use_pointing_period'] = {}
		state['pointing_file'] = self._pointing_file_selector.prepSerialisation()
		state['frame_inv'] = self.pointing_file_inv_toggle.prepSerialisation()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		self._pointing_file_selector.deSerialise(state['pointing_file'])
		self.pointing_file_inv_toggle.deSerialise(state['frame_inv'])

class ConstellationControls(QtWidgets.QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__()
		# Layout containers
		super_layout = QtWidgets.QVBoxLayout()
		# Need to keep a reference to pane_groupbox so we can update geometry when loading a different config
		self.pane_groupbox = QtWidgets.QGroupBox('Supplementary Constellation Configuration')
		config_vlayout = QtWidgets.QVBoxLayout()
		config_vlayout.setSpacing(10)

		# Configuration Widgets
		dflt_config_file = satplot_paths.constellation_dir.joinpath('Iridium_SMALL.json')
		self.tmp_const_config = None
		self.const_config_selector = widgets.FilePicker('Configuration File',
															dflt_file=dflt_config_file.name,
															dflt_dir=dflt_config_file.parent,
															save=False)
		self.const_config_display = widgets.ConstellationConfigDisplay()

		# Place configuration widgets
		config_vlayout.addWidget(self.const_config_selector)
		config_vlayout.addWidget(self.const_config_display)
		config_vlayout.addStretch()
		self.pane_groupbox.setLayout(config_vlayout)

		# Scrollable container
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidget(self.pane_groupbox)
		scroll_area.setWidgetResizable(True)


		super_layout.addWidget(scroll_area)
		self.setLayout(super_layout)

		# Set up connections
		self.const_config_selector.add_connect(self._loadTempConfig)

	def _loadTempConfig(self, cnfg_file:pathlib.Path):
		try:
			self.tmp_const_config = data_types.ConstellationConfig.fromJSON(cnfg_file)
			self.const_config_display.updateConfig(self.tmp_const_config)
			self.const_config_selector.clearError()
		except KeyError as e:
			self.tmp_const_config = None
			self.const_config_selector.setError('Not a valid configuration file')
			self.const_config_display.clearConfig()
		self.pane_groupbox.updateGeometry()

	def refresh(self):
		self._loadTempConfig(self.const_config_selector.getPath())

	def getConfig(self) -> data_types.ConstellationConfig:
		if self.tmp_const_config is None:
			raise ValueError('A Constellation Configuration has not been loaded yet.')
		return self.tmp_const_config

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		# state['constellation'] = self.suppl_constellation_selector.prepSerialisation()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		# self.suppl_constellation_selector.deSerialise(state['constellation'])
		# self._enable.setChecked(state['enabled']['value'])
		pass

class OptionConfigs(QtWidgets.QWidget):
	def __init__(self, asset_dict, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)

		self.la_dict = asset_dict

		self.pane_groupbox = QtWidgets.QGroupBox('Visual Options')
		# self.setFixedWidth(400)
		self.pane_layout = QtWidgets.QVBoxLayout()
		self.config_layout = QtWidgets.QVBoxLayout()

		self.opt_sections = {}

		self.buildWidgetPane(self.la_dict, self.pane_layout)
		self.pane_layout.addStretch()
		self.pane_groupbox.setLayout(self.pane_layout)

		self.scroll_area = QtWidgets.QScrollArea()
		self.scroll_area.setWidget(self.pane_groupbox)
		self.scroll_area.setWidgetResizable(True)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout.addWidget(self.scroll_area)


		self.setLayout(self.config_layout)

	def rebuild(self):
		self.buildWidgetPane(self.la_dict, self.pane_layout)

	def buildWidgetPane(self, cw_assets, root_layout):
		# For each of the canvas wrapper root assets
		for root_asset_key, root_asset in cw_assets.items():
			opt_section_title = f"{root_asset_key.capitalize()} Options"

			# Don't create a new section object if already created
			if opt_section_title not in self.opt_sections.keys():
				self.opt_sections[opt_section_title] = {}
				self.opt_sections[opt_section_title]['added_to_layout'] = False
				self.opt_sections[opt_section_title]['opts'] = {}
				cb = widgets.CollapsibleSection(title=opt_section_title)
				logger.debug(f'Creating collapsible section {cb} for asset {root_asset}')
				self.opt_sections[opt_section_title]['cb'] = cb

				root_layout.addWidget(self.opt_sections[opt_section_title]['cb'])

			# remove old defunct options
			self._recursiveRemoveDefunctOptions(self.opt_sections[opt_section_title]['opts'])

			# build all option widgets for this asset
			root_asset_w_dict = self.recursiveBuildOptionWidgets(root_asset, self.opt_sections[opt_section_title]['cb'])
			self.opt_sections[opt_section_title]['opts'] = root_asset_w_dict
			# add all widgets to its parent
			self._recursivePopulateSections(root_asset_w_dict)

	def _recursiveRemoveDefunctOptions(self, asset_w_dict:dict) -> dict:
		orig_dict = asset_w_dict.copy()
		for w_key, w_dict in orig_dict.items():
			if w_dict['widget_data']['mark_for_removal']:
				logger.debug(f'Deleting option widget: {w_key}')
				w_dict['widget_data']['widget'].setParent(None)
				del asset_w_dict[w_key]
				continue

			if w_dict['sub_widgets'] is not None:
				w_dict['sub_widgets'] = self._recursiveRemoveDefunctOptions(w_dict['sub_widgets'])
				if len(w_dict['sub_widgets'].values()) == 0:
					logger.debug(f'Deleting collapsible option container: {w_key}')
					w_dict['widget_data']['widget'].setParent(None)
					del asset_w_dict[w_key]

		return asset_w_dict

	def _recursivePopulateSections(self, widget_dict:dict) -> None:
		for w_key, widget in widget_dict.items():
			if not widget['widget_data']['added_to_layout']:
				logger.debug(f"Adding {widget['widget_data']['widget']}:{w_key} to {widget['parent_layout']}")
				widget['parent_layout'].addWidget(widget['widget_data']['widget'])
				widget['widget_data']['added_to_layout'] = True
			else:
				logger.debug(f"{widget['widget_data']['widget']}:{w_key} already added to {widget['parent_layout']}")

			if widget['sub_widgets'] is not None:
				self._recursivePopulateSections(widget['sub_widgets'])

	def recursiveBuildOptionWidgets(self, curr_asset, parent_section) -> dict:
		w_dict = {}
		# create widget dict for this asset's options:
		logger.debug(f'Building widgets for {curr_asset} options')
		for opt_key, opt_cnfg in curr_asset.opts.items():
			if opt_cnfg['widget_data'] is not None and opt_cnfg['static']:
				# widget has previously been added
				logger.debug(f'Widget for {curr_asset}:{opt_key} has been previously added')
				continue

			opt_widget = self._buildOptionWidget(opt_key, opt_cnfg)
			if opt_widget is not None:
				# Create widget key for this option
				w_key_els = opt_key.split('_')
				# prepend '_' to plot toggle options, to ensure they appear before other relevant options
				if len(w_key_els) > 0:
					if w_key_els[0] == 'plot':
						w_key = '_'.join(w_key_els[1:])
					else:
						w_key = '_'.join(w_key_els)
				else:
					w_key = '_unknown_option'

				w_dict[w_key] = {}
				w_dict[w_key]['widget_data'] = {}
				w_dict[w_key]['widget_data']['widget'] = opt_widget
				w_dict[w_key]['widget_data']['mark_for_removal'] = False
				w_dict[w_key]['widget_data']['added_to_layout'] = False
				w_dict[w_key]['sub_widgets'] = None
				w_dict[w_key]['parent_layout'] = parent_section
				# tie back to asset
				opt_cnfg['widget_data'] = w_dict[w_key]['widget_data']


		if hasattr(curr_asset, 'assets'):
			logger.debug(f'Processing sub assets for {curr_asset}')
			for sub_asset_key, sub_asset in curr_asset.assets.items():
				logger.debug(f'Creating collapsible section for sub asset {sub_asset} belonging to {curr_asset}')
				section_title = f"{sub_asset_key.capitalize()} Options"
				cb = widgets.CollapsibleSection(title=section_title)
				sub_w_dict = self.recursiveBuildOptionWidgets(sub_asset, cb)

				# only add collapsible section if sub asset actually had any options.
				if sub_w_dict and len(sub_w_dict.keys()) > 0:
					w_dict[f'{sub_asset_key}_cb'] = {}
					w_dict[f'{sub_asset_key}_cb']['widget_data'] = {}
					w_dict[f'{sub_asset_key}_cb']['widget_data']['widget'] = cb
					w_dict[f'{sub_asset_key}_cb']['widget_data']['mark_for_removal'] = False
					w_dict[f'{sub_asset_key}_cb']['widget_data']['added_to_layout'] = False
					w_dict[f'{sub_asset_key}_cb']['sub_widgets'] = sub_w_dict
					w_dict[f'{sub_asset_key}_cb']['parent_layout'] = parent_section

		# sort w_dict
		logger.debug(f'Sorting w_dict for {curr_asset}')
		w_dict = dict(sorted(w_dict.items()))
		return w_dict

	def _buildOptionWidget(self, opt_key:str, opt_cnfg:dict) -> QtWidgets.QWidget:
		label_str = string.capwords(' '.join(opt_key.split('_')))
		widget = None
		if opt_cnfg['type'] == 'boolean':
			try:
				widget = widgets.ToggleBox(label_str,
											opt_cnfg['value'])
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		elif opt_cnfg['type'] == 'colour':
			try:
				widget = widgets.ColourPicker(label_str,
											opt_cnfg['value'])
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		elif opt_cnfg['type'] == 'integer' or opt_cnfg['type'] == 'number':
			try:
				widget = widgets.ValueSpinner(label_str,
							  				opt_cnfg['value'])
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		elif opt_cnfg['type'] == 'float':
			try:
				widget = widgets.ValueSpinner(label_str,
							  				opt_cnfg['value'],
											integer=False)
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		elif opt_cnfg['type'] == 'fraction':
			try:
				widget = widgets.ValueSpinner(label_str,
							  				opt_cnfg['value'],
											fraction=True)
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		elif opt_cnfg['type'] == 'option':
			try:
				widget = widgets.BasicOptionBox(label_str,
											dflt_option=opt_cnfg['value'],
											options_list=opt_cnfg['options'])
				widget.add_connect(opt_cnfg['callback'])
				logger.debug(f"Adding option callback {opt_cnfg['callback']} to {opt_key}")
			except:
				logger.warning(f"Can't make widget {label_str} for asset {opt_key}")
				raise ValueError
		else:
			logger.warning(f"Can't find widget type for {label_str}:{opt_cnfg['type']}")
			raise TypeError

		return widget

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}

		for opt_section_title, opt_section in self.opt_sections.items():
			state[opt_section_title] = {}
			for opt_key, opt in opt_section['opts'].items():
				if not isinstance(opt_section['widget'],widgets.CollapsibleSection):
					state[opt_section_title][opt_key] = opt['widget_data']['widget'].prepSerialisation()

		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		for opt_section_title, opt_section in state.items():
			if opt_section_title not in self.opt_sections.keys():
				logger.warning(f'{opt_section_title} not a recognised context configuration section')
				continue
			for opt_key, opt_serialisation in opt_section.items():
				if opt_key not in self.opt_sections[opt_section_title]['opts'].keys():
					logger.warning(f'{opt_key} not a recognised option for context configuration section {opt_section_title}')
					continue
				self.opt_sections[opt_section_title]['opts'][opt_key]['widget_data']['widget'].deSerialise(opt_serialisation)

class SensorViewConfigs(QtWidgets.QWidget):

	valid_sensor_types = [data_types.SensorTypes.FPA]
	# selected & generate signals have signal arguments of [int, int|None, str|None, str|None]
	selected = QtCore.pyqtSignal(int, object, object, object)
	generate = QtCore.pyqtSignal(int, object, object, object)

	def __init__(self, num_views:int =4, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__()
		vlayout = QtWidgets.QVBoxLayout()

		glayout = QtWidgets.QGridLayout()
		glayout.setVerticalSpacing(1)
		self._label_font = QtGui.QFont()
		self._label_font.setWeight(QtGui.QFont.Medium)
		self._label = QtWidgets.QLabel('Linked Sensor Views')
		self._label.setFont(self._label_font)
		self._num_views = num_views
		glayout.addWidget(self._label,0,0)
		glayout.setContentsMargins(0,0,0,0)

		self.view_spacecraft_selectors = []
		self.view_sensor_selectors = []
		self.view_full_res_generator = []

		for ii in range(self._num_views):
			self.view_spacecraft_selectors.append(widgets.OptionBox(f'View {ii+1} Spacecraft:',
																options_list=[]))
			self.view_sensor_selectors.append(widgets.OptionBox(f'View {ii+1} Sensor:',
																options_list=[]))
			self.view_full_res_generator.append(widgets.Button(f'Full Resolution Image','Generate'))
			glayout.addWidget(self.view_spacecraft_selectors[-1],ii+1,0)
			glayout.addWidget(self.view_sensor_selectors[-1],ii+1,1)
			glayout.addWidget(self.view_full_res_generator[-1],ii+1,2)

		selector_links = [self.createSelectorLink(ii) for ii in range(self._num_views)]
		for ii in range(self._num_views):
			self.view_spacecraft_selectors[ii].add_connect(selector_links[ii])

		selection_links = [self.createSelectionLink(ii) for ii in range(self._num_views)]
		for ii in range(self._num_views):
			self.view_sensor_selectors[ii].add_connect(selection_links[ii])

		generator_links = [self.createGeneratorLink(ii) for ii in range(self._num_views)]
		for ii in range(self._num_views):
			self.view_full_res_generator[ii].add_connect(generator_links[ii])

		vlayout.addLayout(glayout)
		vlayout.addStretch()
		self.setLayout(vlayout)

	def createSelectorLink(self, selector_idx):
		def _function(sc_list_idx):
			self.setSensList(selector_idx, sc_list_idx)
		return _function

	def createSelectionLink(self, selector_idx):
		def _function(sens_list_idx):
			self.onSensorSelection(selector_idx, sens_list_idx)
		return _function

	def createGeneratorLink(self, selector_idx):
		def _function():
			self.onGenerateSelection(selector_idx)
		return _function

	def setSelectorLists(self, sens_dict):
		self._sens_dict = {}
		self._sc_dict = {0:(None,None)}
		sc_num = 1
		logger.info(f'Creating list of sensors for all spacecraft')
		for scid, sc_config in sens_dict.items():
			self._sc_dict[sc_num] = (scid, sc_config[0])
			sc_num += 1
			self._sens_dict[scid] = {0:(None,None)}
			sens_num = 1
			for suite_name, suite in sc_config[1].items():
				for sens_name, sens_config in suite.items():
					if sens_config['shape'] in self.valid_sensor_types:
						self._sens_dict[scid][sens_num] = (suite_name, sens_name)
						sens_num += 1

		logger.info(f'Populating drop down menus with spacecraft')
		for ii in range(self._num_views):
			self.view_spacecraft_selectors[ii].clear()
			sc_items_list = [f'{v[0]}: {v[1]}' for v in self._sc_dict.values()]
			sc_items_list[0] = ''
			self.view_spacecraft_selectors[ii].addItems(sc_items_list)

	def setSensList(self, view_id, sc_list_id):
		logger.info(f'Clearing sensors from drop down menus')
		self.view_sensor_selectors[view_id].clear()
		sc_id = self._sc_dict[sc_list_id][0]
		if sc_id is None:
			self.onSensorSelection(view_id, None)
			return
		sens_list = [f'{v[0]}: {v[1]}' for v in self._sens_dict[sc_id].values()]
		sens_list[0] = ''
		logger.info(f'Populating drop down menus with sensors')
		self.view_sensor_selectors[view_id].addItems(sens_list)

	def onGenerateSelection(self, view_id):
		if self.view_spacecraft_selectors[view_id].getCurrentIndex() is None or \
			self.view_sensor_selectors[view_id].getCurrentIndex() is None:
			return
		else:
			sens_list_idx = self.view_sensor_selectors[view_id].getCurrentIndex()+1
			sc_id = self._sc_dict[self.view_spacecraft_selectors[view_id].getCurrentIndex()+1][0]
			suite_key = self._sens_dict[sc_id][sens_list_idx][0]
			sens_key = self._sens_dict[sc_id][sens_list_idx][1]
			self.generate.emit(view_id, sc_id, suite_key, sens_key)

	def onSensorSelection(self, view_id, sens_list_idx):
		if self.view_spacecraft_selectors[view_id].getCurrentIndex() is None:
			self.selected.emit(view_id, None, None, None)
		else:
			# OptionBox getCurrentIndex ignores empty first entry in index counting
			sc_id = self._sc_dict[self.view_spacecraft_selectors[view_id].getCurrentIndex()+1][0]
			suite_key = self._sens_dict[sc_id][sens_list_idx][0]
			sens_key = self._sens_dict[sc_id][sens_list_idx][1]
			self.selected.emit(view_id, sc_id, suite_key, sens_key)

class Toolbar(QtWidgets.QWidget):
	# TODO: this should be in widgets, not controls
	def __init__(self, parent_window:QtWidgets.QMainWindow|None, action_dict, context_name=None):
		super().__init__()
		self.parent_window = parent_window
		self.action_dict = action_dict
		self.context_name = context_name
		if self.context_name is None:
			self.context_name = 'main-window'
		self.toolbar = QtWidgets.QToolBar("Toolbar")

		self.toolbar.setIconSize(QtCore.QSize(16,16))

		self.button_dict = {}

		self.addToWindow()

	def addButtons(self):
		# Process 'all' actions first
		old_containing = None
		for key, action in self.action_dict.items():
			action_context_list = [ac.lower() for ac in action['contexts']]
			if 'all'.lower() in action_context_list and action['button_icon'] is not None:
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['tooltip'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])
				old_containing = action['containing_menu']
				self.toolbar.addAction(self.button_dict[key])

		self.toolbar.addSeparator()

		old_containing = None

		for key, action in self.action_dict.items():
			action_context_list = [ac.lower() for ac in action['contexts']]
			if self.context_name.lower() in action_context_list and 'all' not in action_context_list and action['button_icon'] is not None:
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['tooltip'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])
				old_containing = action['containing_menu']
				self.toolbar.addAction(self.button_dict[key])

	def addToWindow(self):
		if self.parent_window is not None:
			self.parent_window.addToolBar(self.toolbar)
		else:
			logger.error("Can't add toolbar to window, context {context_name} doesn't have a window yet.")
			raise ValueError("Can't add toolbar to window, context {context_name} doesn't have a window yet.")

	def setActiveState(self, state):
		if self.toolbar.toggleViewAction() is not None:
			self.toolbar.toggleViewAction().setChecked(not state) # type:ignore
			self.toolbar.toggleViewAction().trigger()					# type:ignore
		else:
			logger.error("Can't add toolbar to window, context {context_name} doesn't have a window yet.")
			raise ValueError("Can't set toolbar active state for {context_name}")

class Menubar(QtWidgets.QWidget):
	# TODO: this should be in widgets, not controls
	def __init__(self, parent_window, action_dict, context_name=None):
		super().__init__()
		self.parent_window = parent_window
		self.action_dict = action_dict
		self.context_name = context_name
		if self.context_name is None:
			self.context_name = 'main-window'
		self.menubar = QtWidgets.QMenuBar()
		self.menus = {}
		self.button_dict = {}

	def addMenuItems(self):
		# Process 'all' actions first
		for key, action in self.action_dict.items():
			action_context_list = [ac.lower() for ac in action['contexts']]
			if 'all'.lower() in action_context_list:
				if action['containing_menu'] not in self.menus.keys():
					self.menus[action['containing_menu']] = self.menubar.addMenu(action['containing_menu'].capitalize())
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['menu_item'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])
				self.menus[action['containing_menu']].addAction(self.button_dict[key])

		# Process context specific actions
		for key, action in self.action_dict.items():
			action_context_list = [ac.lower() for ac in action['contexts']]
			if self.context_name.lower() in action_context_list:
				if action['containing_menu'] not in self.menus.keys():
					self.menus[action['containing_menu']] = self.menubar.addMenu(action['containing_menu'].capitalize())
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['menu_item'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])
				self.menus[action['containing_menu']].addAction(self.button_dict[key])

	def setActiveState(self, state):
		if state:
			self.parent_window.setMenuBar(self.menubar)
		else:
			self.menubar.setParent(None)

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))