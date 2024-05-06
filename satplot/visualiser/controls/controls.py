from PyQt5 import QtWidgets, QtCore, QtGui
from satplot.visualiser.controls import widgets
from satplot.visualiser.assets import base
import datetime as dt
import string
import satplot.visualiser.controls.console as console

class OrbitConfigs(QtWidgets.QWidget):

	constellation_options = ['Iridium NEXT', 'Iridium SMALL', 'Thuraya', 'Swift']
	constellation_files = ['./data/TLEs/iridiumNEXT_latest.tle',
							'./data/TLEs/iridiumSMALL_latest.tle',
							'./data/TLEs/thuraya_latest.tle',
							'./data/TLEs/swift_latest.tle']
	constellation_beam_angles = [125.8, 125.8, 15.0, 0.1]

	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
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
															dflt_file='spirit_latest.tle',
															dflt_dir='data/TLEs/',
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

	def getConstellationIndex(self):
		return self.suppl_constellation_selector.getCurrentIndex()

	def prepSerialisation(self):
		state = {}
		return state

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
												   			dflt_file='20240223-030000_quaternion.csv',
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
															options_list=OrbitConfigs.constellation_options)		
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

	def getCurrentIndex(self):
		return self.suppl_constellation_selector.getCurrentIndex()

class OptionConfigs(QtWidgets.QWidget):
	def __init__(self, asset_dict, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.la_dict = asset_dict
		
		self.pane_groupbox = QtWidgets.QGroupBox('Visual Options')
		# self.setFixedWidth(400)
		self.pane_layout = QtWidgets.QVBoxLayout()
		self.config_layout = QtWidgets.QVBoxLayout()
		
		self.buildWidgetPane(self.la_dict, self.pane_layout)
		self.pane_layout.addStretch()
		self.pane_groupbox.setLayout(self.pane_layout)

		self.scroll_area = QtWidgets.QScrollArea()
		self.scroll_area.setWidget(self.pane_groupbox)
		self.scroll_area.setWidgetResizable(True)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout.addWidget(self.scroll_area)

		self.setLayout(self.config_layout)
	
	def buildWidgetPane(self, root_dict, root_layout):
		for key, asset in root_dict.items():
			cb = widgets.CollapsibleSection(title=f"{key.capitalize()} Options")
			w_dict = self._buildNestedOptionWidgetDict(asset, asset_key=key)
			for key, widget in dict(sorted(w_dict.items())).items():
				cb.addWidget(widget)
			root_layout.addWidget(cb)
		return


	def _buildNestedOptionWidgetDict(self, asset, asset_key=''):
		# returns unsorted_dict
		w_dict = {}
		if not isinstance(asset, base.BaseAsset) and not isinstance(asset, base.SimpleAsset):
			# no options or nested assets with options
			return w_dict
		
		if hasattr(asset, 'opts') and asset.opts is not None:
			w_opt_dict = self._buildOptionWidgetDict(asset.opts)
		else:
			w_opt_dict = None

		w_dict.update(w_opt_dict)

		if hasattr(asset, 'assets'):
			for sub_key, sub_asset in asset.assets.items():
				if not isinstance(sub_asset, base.BaseAsset) and not isinstance(sub_asset, base.SimpleAsset):
					continue
				sub_w_dict = self._buildNestedOptionWidgetDict(sub_asset, asset_key=sub_key)
				cb = widgets.CollapsibleSection(title=f"{sub_key.capitalize()} Options")
				for sub_w_key, widget in dict(sorted(sub_w_dict.items())).items():
					cb.addWidget(widget)
				if sub_key not in w_dict.keys():
					w_dict[sub_key] = cb
				else:
					w_dict[f"{sub_key}_"] = cb

		return w_dict

	def _buildOptionWidgetDict(self, opts):
		w_dict = {}
		for opt_key, opt_dict in opts.items():
			w_str = string.capwords(' '.join(opt_key.split('_')))
			if opt_dict['type'] == 'boolean':
				try:
					widget = widgets.ToggleBox(w_str,
												opt_dict['value'])
					widget.add_connect(opt_dict['callback'])
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			if opt_dict['type'] == 'colour':
				try:
					widget = widgets.ColourPicker(w_str,
												opt_dict['value'])
					widget.add_connect(opt_dict['callback'])
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			if opt_dict['type'] == 'integer' or opt_dict['type'] == 'number':
				try:
					widget = widgets.ValueSpinner(w_str,
								  				opt_dict['value'])
					widget.add_connect(opt_dict['callback'])
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError
			if opt_dict['type'] == 'float':
				try:
					widget = widgets.ValueSpinner(w_str,
								  				opt_dict['value'],
												integer=False)
					widget.add_connect(opt_dict['callback'])
				except:
					print(f"Can't make widget {w_str} for asset {opt_key}")
					raise ValueError

			w_key = opt_key.split('_')
			if len(w_key) > 0:
				if w_key[0] == 'plot':
					w_key = '_'.join(w_key[1:])
				else:
					w_key = '_'.join(w_key)
			try:
				w_dict[w_key] = widget
			except UnboundLocalError:
				print(f"UnboundLocalError when generating options widget for {w_key}")
				raise UnboundLocalError


		return w_dict

class Toolbar(QtWidgets.QWidget):
	# TODO: this should be in widgets, not controls	
	def __init__(self, parent_window, action_dict, context_name=None):
		super().__init__()
		self.window = parent_window
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
		self.window.addToolBar(self.toolbar)

	def setActiveState(self, state):
		self.toolbar.toggleViewAction().setChecked(not state)
		self.toolbar.toggleViewAction().trigger()

class Menubar(QtWidgets.QWidget):
	# TODO: this should be in widgets, not controls
	def __init__(self, parent_window, action_dict, context_name=None):
		super().__init__()
		self.window = parent_window
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
			self.window.setMenuBar(self.menubar)
		else:	
			self.menubar.setParent(None)

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))