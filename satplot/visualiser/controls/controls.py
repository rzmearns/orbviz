from PyQt5 import QtWidgets, QtCore, QtGui
from satplot.visualiser.controls import widgets
from satplot.visualiser.assets import base
import datetime as dt
import string
import satplot.visualiser.controls.console as console

class OrbitConfigs(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self.pane_groupbox = QtWidgets.QGroupBox('Orbit Configuration')
		# self.setFixedWidth(400)
		# self.setFixedHeight(500)
		self.pane_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		self.pane_layout.setSpacing(10)

		# Add widgets here
		self.period_start = widgets.DatetimeEntry("Period Start:", dt.datetime(2024,2,6,0,0,0))
		self.period_end = widgets.DatetimeEntry("Period End:", dt.datetime.now())
		self.button_layout = QtWidgets.QHBoxLayout()
		self.submit_button = QtWidgets.QPushButton('Recalculate')
		self.prim_orbit_selector = widgets.FilePicker('Primary Orbit','./data/TLEs/spirit_latest.tle')
		self.pointing_file_selector = widgets.FilePicker('Pointing File - Not Implemented')
		self.suppl_orbit_selector = widgets.FilePicker('Supplementary Orbits')

		self.pane_layout.addWidget(self.period_start)
		self.pane_layout.addWidget(self.period_end)
		self.pane_layout.addWidget(self.prim_orbit_selector)
		self.pane_layout.addWidget(self.pointing_file_selector)

		self.button_layout.addStretch()
		self.button_layout.addWidget(self.submit_button)
		self.button_layout.addStretch()
		self.pane_layout.addLayout(self.button_layout)

		self.pane_layout.addStretch()
		self.pane_groupbox.setLayout(self.pane_layout)

		self.scroll_area = QtWidgets.QScrollArea()
		self.scroll_area.setWidget(self.pane_groupbox)
		self.scroll_area.setWidgetResizable(True)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout.addWidget(self.scroll_area)

		self.setLayout(self.config_layout)

class OptionConfigs(QtWidgets.QWidget):
	def __init__(self, asset_dict, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.la_dict = asset_dict
		
		self.pane_groupbox = QtWidgets.QGroupBox('Display Options')
		# self.setFixedWidth(400)
		self.pane_layout = QtWidgets.QVBoxLayout(self)
		self.config_layout = QtWidgets.QVBoxLayout(self)
		
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
		print(f"iterating through canvas assets")
		for key, asset in root_dict.items():
			cb = widgets.CollapsibleSection(title=f"{key.capitalize()} Options")
			w_dict = self._buildNestedOptionWidgetDict(asset, asset_key=key)
			print()
			pretty(w_dict)
			for key, widget in dict(sorted(w_dict.items())).items():
				print(key, widget)
				cb.addWidget(widget)
			root_layout.addWidget(cb)
		return


	def _buildNestedOptionWidgetDict(self, asset, asset_key=''):
		# returns unsorted_dict
		w_dict = {}
		print(f"new root asset - {asset_key}")
		if not isinstance(asset, base.BaseAsset):
			# no options or nested assets with options
			return w_dict
		
		if hasattr(asset, 'opts') and asset.opts is not None:
			print(f"\t{asset_key} has options")
			w_opt_dict = self._buildOptionWidgetDict(asset.opts)
		else:
			w_opt_dict = None

		w_dict.update(w_opt_dict)

		if hasattr(asset, 'visuals'):
			print(f"\t{asset_key} has visuals")
			print(f"\titerating through {asset_key} visual assets")
			for sub_key, sub_asset in asset.visuals.items():
				if not isinstance(sub_asset, base.BaseAsset):
					continue
				sub_w_dict = self._buildNestedOptionWidgetDict(sub_asset, asset_key=sub_key)
				cb = widgets.CollapsibleSection(title=f"{sub_key.capitalize()} Options")
				for sub_w_key, widget in dict(sorted(sub_w_dict.items())).items():
					# print(f"\t{key}")
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
				widget = widgets.ToggleBox(w_str,
											opt_dict['value'])
				widget.add_connect(opt_dict['callback'])
			if opt_dict['type'] == 'colour':
				widget = widgets.ColourPicker(w_str,
											opt_dict['value'])
				widget.add_connect(opt_dict['callback'])
			if opt_dict['type'] == 'number':
				pass
			w_key = opt_key.split('_')
			if len(w_key) > 0:
				if w_key[0] == 'plot':
					w_key = '_'.join(w_key[1:])
				else:
					w_key = '_'.join(w_key)
			w_dict[w_key] = widget

		return w_dict

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))