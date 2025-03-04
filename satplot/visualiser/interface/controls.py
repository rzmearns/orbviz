import datetime as dt
import json
import os
import string
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot.model.data_models.data_types as data_types
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.interface.widgets as widgets


class OrbitConfigs(QtWidgets.QWidget):

	prim_config_dir = 'data/primary_configs/'

	def __init__(self, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)
		self.pane_groupbox = QtWidgets.QGroupBox('Orbit Configuration')
		# self.setFixedWidth(400)
		# self.setFixedHeight(500)
		self.pane_layout = QtWidgets.QVBoxLayout()
		self.config_layout = QtWidgets.QVBoxLayout()
		self.pane_layout.setSpacing(10)

		# Add widgets here
		self.period_start = widgets.DatetimeEntry("Period Start:", dt.datetime.now())
		self.period_end = widgets.DatetimeEntry("Period End:", (dt.datetime.now()+dt.timedelta(seconds=1)))
		self.sampling_period = widgets.PeriodBox("Sampling Period:", 1)
		self.button_layout = QtWidgets.QHBoxLayout()
		self.submit_button = QtWidgets.QPushButton('Recalculate')
		self.prim_orbit_selector = widgets.FilePicker('Primary Orbit',
															dflt_file='SpIRIT_XYZ.json',
															dflt_dir='data/primary_configs/',
															save=False)
		self.pointing_file_controls = PointingFileControls()
		
		self.suppl_constellation_selector = ConstellationControls()

		self.pane_layout.addWidget(self.period_start)
		self.pane_layout.addWidget(self.period_end)
		self.pane_layout.addWidget(self.sampling_period)
		self.pane_layout.addWidget(self.prim_orbit_selector)
		self.pane_layout.addWidget(self.pointing_file_controls)

		self.pane_layout.addWidget(self.suppl_constellation_selector)

		self.button_layout.addStretch()
		self.button_layout.addWidget(self.submit_button)
		self.button_layout.addStretch()
		self.pane_layout.addLayout(self.button_layout)

		self.pane_layout.addStretch()
		self.pane_groupbox.setLayout(self.pane_layout)

		self.scroll_area = QtWidgets.QScrollArea()
		self.scroll_area.setWidget(self.pane_groupbox)
		self.scroll_area.setWidgetResizable(True)
		self.suppl_constellation_selector.setContainingScrollWidget(self.scroll_area)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout.setObjectName('Orbit config layout')
		self.config_layout.addWidget(self.scroll_area)

		# self.setLayout(self.config_layout)

	def prepSerialisation(self):
		state = {}
		return state

	def getConfig(self) -> data_types.PrimaryConfig:
		return data_types.PrimaryConfig.fromJSON(self.prim_orbit_selector.path)

class PointingFileControls(QtWidgets.QWidget):
	def __init__(self, *args, **kwargs):
		super().__init__()
		vlayout = QtWidgets.QVBoxLayout()

		glayout = QtWidgets.QGridLayout()
		glayout.setVerticalSpacing(1)
		self._label_font = QtGui.QFont()
		self._label_font.setWeight(QtGui.QFont.Medium)
		self._label = QtWidgets.QLabel('Pointing File')
		self._label.setFont(self._label_font)
		glayout.addWidget(self._label,0,0,1,-1)
		glayout.setContentsMargins(0,0,0,0)

		self._en_label = QtWidgets.QLabel('Enable:')
		self._enable = QtWidgets.QCheckBox()
		self._enable_list = []
		glayout.addWidget(self._en_label,1,0)
		glayout.addWidget(self._enable,1,2)

		self._pointing_file_selector = widgets.FilePicker(None,
												   			dflt_file='20240801_test_quaternion_X_ECI_parallel_Z_Zenith.csv',
															dflt_dir='data/pointing/',
															save=False,
															margins=[0,0,0,0])
		glayout.addWidget(self._pointing_file_selector,2,0,1,-1)
		
		self.pointing_file_inv_toggle = widgets.Switch()
		self.pointing_file_inv_toggle.setChecked(True)
		self.pointing_file_inv_label = QtWidgets.QLabel('Pointing File frame\ntransform direction')
		self.pointing_file_inv_off_label = QtWidgets.QLabel('BF->ECI')
		self.pointing_file_inv_on_label = QtWidgets.QLabel('ECI->BF')
		glayout.addWidget(self.pointing_file_inv_label,3,0)
		glayout.addWidget(self.pointing_file_inv_off_label,3,6)
		glayout.addWidget(self.pointing_file_inv_toggle,3,7)
		glayout.addWidget(self.pointing_file_inv_on_label,3,8)

		self.use_pointing_period_label = QtWidgets.QLabel('Use pointing file\nto define period')
		self.use_pointing_period = QtWidgets.QCheckBox()
		glayout.addWidget(self.use_pointing_period_label,4,0)
		glayout.addWidget(self.use_pointing_period,4,2)
		
		
		vlayout.addLayout(glayout)
		self.setLayout(vlayout)


		self._enable.toggled.connect(self.enableState)
		self._enable.setChecked(False)

		self.addWidgetToEnable(self._pointing_file_selector)
		self.addWidgetToEnable(self.pointing_file_inv_label)
		self.addWidgetToEnable(self.pointing_file_inv_off_label)
		self.addWidgetToEnable(self.pointing_file_inv_on_label)
		self.addWidgetToEnable(self.pointing_file_inv_toggle)
		self.addWidgetToEnable(self.use_pointing_period_label)
		self.addWidgetToEnable(self.use_pointing_period)
		self.enableState(False)

	def isEnabled(self):
		return self._enable.isChecked()

	def enableState(self, state):
		for widget in self._enable_list:
			widget.setDisabled(not state)

	def addWidgetToEnable(self, widget):
		self._enable_list.append(widget)

	def pointingFileDefinesPeriod(self):
		return self.use_pointing_period.isChecked()

class ConstellationControls(QtWidgets.QWidget):
	c_config_dir = 'data/constellation_configs/'
	c_configs = os.listdir(c_config_dir)
	constellation_options = [c.split('.')[0].replace('_',' ') for c in c_configs]

	def __init__(self, *args, **kwargs):
		super().__init__()		
		vlayout = QtWidgets.QVBoxLayout()

		glayout = QtWidgets.QGridLayout()
		glayout.setVerticalSpacing(1)
		self._label_font = QtGui.QFont()
		self._label_font.setWeight(QtGui.QFont.Medium)
		self._label = QtWidgets.QLabel('Supplementary Constellations')
		self._label.setFont(self._label_font)
		glayout.addWidget(self._label,0,0,1,-1)
		glayout.setContentsMargins(0,0,0,0)

		self._en_label = QtWidgets.QLabel('Enable:')
		self._enable = QtWidgets.QCheckBox()
		self._enable_list = []
		glayout.addWidget(self._en_label,1,0)
		glayout.addWidget(self._enable,1,2)

		self.suppl_constellation_selector = widgets.OptionBox('Supplementary Constellations',
															options_list=self.constellation_options)		
		glayout.addWidget(self.suppl_constellation_selector,2,0,1,-1)

		vlayout.addLayout(glayout)
		self.setLayout(vlayout)

		self._enable.toggled.connect(self.enableState)
		self._enable.setChecked(False)

		self.addWidgetToEnable(self.suppl_constellation_selector)
		self.enableState(False)

	def isEnabled(self):
		return self._enable.isChecked()

	def enableState(self, state):
		for widget in self._enable_list:
			widget.setDisabled(not state)

	def addWidgetToEnable(self, widget):
		self._enable_list.append(widget)

	def setContainingScrollWidget(self, widget):
		self.suppl_constellation_selector.setContainingScrollWidget(widget)

	def getConstellationConfig(self):
		c_index = self.getCurrentIndex()
		if c_index is None:
			return None
		with open(f'{self.c_config_dir}{self.c_configs[c_index]}','r') as fp:
			c_config = json.load(fp)
		return c_config

	def getCurrentIndex(self):
		return self.suppl_constellation_selector.getCurrentIndex()

class OptionConfigs(QtWidgets.QWidget):
	def __init__(self, asset_dict, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)

		self.la_dict = asset_dict
		
		self.pane_groupbox = QtWidgets.QGroupBox('Visual Options')
		# self.setFixedWidth(400)
		self.pane_layout = QtWidgets.QVBoxLayout()
		self.config_layout = QtWidgets.QVBoxLayout()

		self.sections = {}

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

	def buildWidgetPane(self, root_dict, root_layout):
		for section_key, asset in root_dict.items():
			section_title = f"{section_key.capitalize()} Options"
			if section_title not in self.sections.keys():
				self.sections[section_title] = {}
				self.sections[section_title]['added_to_layout'] = False
				self.sections[section_title]['opts'] = {}
				self.sections[section_title]['cb'] = widgets.CollapsibleSection(title=section_title)

			for opt_key in list(self.sections[section_title]['opts'].keys()):
				widget_struct = self.sections[section_title]['opts'][opt_key]
				if widget_struct['mark_for_removal']:
					print(f'deleting {opt_key}')
					widget_struct['widget'].setParent(None)
					del(self.sections[section_title]['opts'][opt_key])


			w_dict = self._buildNestedOptionWidgetDict(asset, asset_key=section_key)

			for opt_key, widget_struct in dict(sorted(w_dict.items())).items():
				if opt_key not in self.sections[section_title]['opts']:
					print(f'Option collapsible section {section_title}, adding: {opt_key}')
					print(f'{section_title=}')
					print(f'{opt_key=}')
					self.sections[section_title]['opts'][opt_key] = widget_struct
					# won't be in alphabetical order second time round
					self.sections[section_title]['cb'].addWidget(widget_struct['widget'])

			if not self.sections[section_title]['added_to_layout']:
				root_layout.addWidget(self.sections[section_title]['cb'])
				self.sections[section_title]['added_to_layout'] = True

		# for section_title, section in self.sections.items():
		# 	print(f'{section_title}:')
		# 	print(f"\tadded_to_layout:{section['added_to_layout']}")
		# 	print(f"\topts:")
		# 	for k,v in section['opts'].items():
		# 		print(f"\t\t{k}:{v}")


	def _buildNestedOptionWidgetDict(self, asset, asset_key=''):
		# returns unsorted_dict
		w_dict = {}
		if not isinstance(asset, base_assets.AbstractAsset) and not isinstance(asset, base_assets.AbstractSimpleAsset):
			# no options or nested assets with options
			return w_dict
		
		if hasattr(asset, 'opts') and asset.opts is not None:
			w_opt_dict = self._buildOptionWidgetDict(asset.opts)
		else:
			w_opt_dict = None

		w_dict.update(w_opt_dict) 	# type:ignore

		if hasattr(asset, 'assets'):
			if asset is not type(base_assets.AbstractSimpleAsset):
				for sub_key, sub_asset in asset.assets.items():  # type:ignore
					if not isinstance(sub_asset, base_assets.AbstractAsset) and not isinstance(sub_asset, base_assets.AbstractSimpleAsset):
						continue
					sub_w_dict = self._buildNestedOptionWidgetDict(sub_asset, asset_key=sub_key)
					cb = widgets.CollapsibleSection(title=f"{sub_key.capitalize()} Options")
					for sub_w_key, widget in dict(sorted(sub_w_dict.items())).items():
						cb.addWidget(widget['widget'])
					if sub_key not in w_dict.keys():
						w_dict[sub_key] = {}
						w_dict[sub_key]['widget'] = cb
						w_dict[sub_key]['mark_for_removal'] = False
					else:
						w_dict[f"{sub_key}_"] = {}
						w_dict[f"{sub_key}_"]['widget'] = cb
						w_dict[f"{sub_key}_"]['mark_for_removal'] = False

		return w_dict

	def _buildOptionWidgetDict(self, opts):
		w_dict = {}
		for opt_key, opt_dict in opts.items():
			if opt_dict['widget'] is not None and opt_dict['static']:
					continue

			w_str = string.capwords(' '.join(opt_key.split('_')))
			if opt_dict['type'] == 'boolean':
				try:
					widget = widgets.ToggleBox(w_str,
												opt_dict['value'])
					# opt_dict['widget'] = widget
					widget.add_connect(opt_dict['callback'])
					print(f"Adding option callback {opt_dict['callback']} to {opt_key}")
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			elif opt_dict['type'] == 'colour':
				try:
					widget = widgets.ColourPicker(w_str,
												opt_dict['value'])
					# opt_dict['widget'] = widget
					widget.add_connect(opt_dict['callback'])
					print(f"Adding option callback {opt_dict['callback']} to {opt_key}")
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			elif opt_dict['type'] == 'integer' or opt_dict['type'] == 'number':
				try:
					widget = widgets.ValueSpinner(w_str,
								  				opt_dict['value'])
					# opt_dict['widget'] = widget
					widget.add_connect(opt_dict['callback'])
					print(f"Adding option callback {opt_dict['callback']} to {opt_key}")
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			elif opt_dict['type'] == 'float':
				try:
					widget = widgets.ValueSpinner(w_str,
								  				opt_dict['value'],
												integer=False)
					# opt_dict['widget'] = widget
					widget.add_connect(opt_dict['callback'])
					print(f"Adding option callback {opt_dict['callback']} to {opt_key}")
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			elif opt_dict['type'] == 'fraction':
				try:
					widget = widgets.ValueSpinner(w_str,
								  				opt_dict['value'],
												fraction=True)
					# opt_dict['widget'] = widget
					widget.add_connect(opt_dict['callback'])
					print(f"Adding option callback {opt_dict['callback']} to {opt_key}")
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			else:
				print(f"Can't find widget type for {w_str}:{opt_dict['type']}")
				continue

			w_key = opt_key.split('_')
			if len(w_key) > 0:
				if w_key[0] == 'plot':
					w_key = '_'.join(w_key[1:])
				else:
					w_key = '_'.join(w_key)
			try:
				w_dict[w_key] = {}
				w_dict[w_key]['widget'] = widget 				# type:ignore
				w_dict[w_key]['mark_for_removal'] = False
				opt_dict['widget'] = w_dict[w_key]
			except UnboundLocalError:
				print(f"UnboundLocalError when generating options widget for {w_key}")
				raise UnboundLocalError


		return w_dict

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}

		for section_title, section in self.sections.items():
			state[section_title] = {}
			for opt_key, opt in section['opts'].items():
				if not isinstance(opt['widget'],widgets.CollapsibleSection):
					state[section_title][opt_key] = opt['widget'].prepSerialisation()

		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		print('Deserialising Config Options:')
		for section_title, section in state.items():
			print(f'\t{section_title}')
			if section_title not in self.sections.keys():
				print(f'{section_title} not a recognised context configuration section')
				continue
			for opt_key, opt_serialisation in section.items():
				print(f'\t\t{opt_key}')
				if opt_key not in self.sections[section_title]['opts'].keys():
					print(f'{opt_key} not a recognised option for context configuration section {section_title}')
					continue
				self.sections[section_title]['opts'][opt_key]['widget'].deSerialise(opt_serialisation)

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
		for key, action in self.action_dict.items():
			if 'all' in action['contexts'] and action['button_icon'] is not None:
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['tooltip'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])

				self.toolbar.addAction(self.button_dict[key])

		self.toolbar.addSeparator()

		for key, action in self.action_dict.items():
			if self.context_name in action['contexts'] and 'all' not in action['contexts'] and action['button_icon'] is not None:
				self.button_dict[key] = QtWidgets.QAction(QtGui.QIcon(action['button_icon']), action['tooltip'], self)
				self.button_dict[key].setStatusTip(action['tooltip'])
				self.button_dict[key].setCheckable(action['toggleable'])
				if action['callback'] is not None:
					self.button_dict[key].triggered.connect(action['callback'])

				self.toolbar.addAction(self.button_dict[key])

	def addToWindow(self):
		if self.parent_window is not None:
			self.parent_window.addToolBar(self.toolbar)
		else:
			raise ValueError("Can't add toolbar to window, context {context_name} doesn't have a window yet.")

	def setActiveState(self, state):
		if self.toolbar.toggleViewAction() is not None:
			self.toolbar.toggleViewAction().setChecked(not state) # type:ignore
			self.toolbar.toggleViewAction().trigger()					# type:ignore
		else:
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
			if 'all' in action['contexts']:
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
			if self.context_name in action['contexts']:
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