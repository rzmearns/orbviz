import json
import logging
import numpy as np
import time
from typing import Any

from PyQt5 import QtGui

from numpy._typing import _array_like
from vispy import scene
import vispy
from vispy.app.canvas import MouseEvent
from vispy.scene.cameras import PanZoomCamera



from satplot.model.data_models.history_data import (HistoryData)
from satplot.model.data_models.earth_raycast_data import (EarthRayCastData)
import satplot.model.geometry.primgeom as pg
from satplot.model.data_models.data_types import PrimaryConfig
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.util.constants as c
import satplot.util.exceptions as exceptions
import satplot.util.paths as satplot_paths
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.sensors as sensors
import satplot.visualiser.assets.spacecraft as spacecraft
import satplot.visualiser.assets.widgets as widgets
import satplot.visualiser.cameras.static2d as static2d

logger = logging.getLogger(__name__)

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False


class SensorViewsCanvasWrapper(BaseCanvas):
	def __init__(self, w:int=800, h:int=600, keys:str='interactive', bgcolor:str='white'):
		self.canvas = scene.canvas.SceneCanvas(size=(w,h),
										keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.canvas.events.mouse_move.connect(self.onMouseMove)
		self.canvas.events.mouse_wheel.connect(self.onMouseScroll)
		self.canvas.events.key_press.connect(self.on_key_press)
		self.grid = self.canvas.central_widget.add_grid()
		vb1 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		vb2 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		vb3 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		vb4 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		scenes = vb1.scene, vb2.scene, vb3.scene, vb4.scene
		self.view_boxes = [vb1, vb2, vb3, vb4]
		self.displayed_sensors = [None, None, None, None]

		self.grid.add_widget(self.view_boxes[0],0,0)
		self.grid.add_widget(self.view_boxes[1],0,1)
		self.grid.add_widget(self.view_boxes[2],1,0)
		self.grid.add_widget(self.view_boxes[3],1,1)

		for ii in range(len(scenes)):
			self.view_boxes[ii].camera = static2d.Static2D(parent=self.view_boxes[ii].scene)
			self.view_boxes[ii].camera.aspect = 1
			self.view_boxes[ii].camera.flip = (0,1,0)


		self.data_models: dict[str,Any] = {}
		self.assets = {}
		self._buildAssets()
		self.mouseOverObject = None

	def _buildAssets(self) -> None:
		pass
		self.assets['spacecraft'] = spacecraft.SpacecraftViewsAsset(v_parent=None)

	def _getCurrentDisplayedSensor(self, view:int) -> sensors.SensorImageAsset | None:
		return self.displayed_sensors[view]

	def selectSensor(self, view:int, sc_id: int, sens_suite_key: str, sens_key: str) -> None:
		# remove parent scene of old sensor
		# make old sensor dormant
		logger.debug(f'Clearing sensor: {self.displayed_sensors[view]} from view: {view}')
		if self.displayed_sensors[view] is not None:
			self.displayed_sensors[view].makeDormant()
			self.displayed_sensors[view] = None

		if sc_id == None or \
			sens_suite_key == None or \
			sens_key == None:
			return

		# attach parent scene to new sensor
		# make new sensor active
		suite_asset, sensor_asset = self._getSensorAsset(sc_id, sens_suite_key, sens_key)
		sensor_asset.setParentView(self.view_boxes[view].scene)
		# Only want to set a single sensor to be active, not all within one suite
		suite_asset._setActiveFlag()
		sensor_asset._setActiveFlag()
		sensor_asset._attachToParentView()
		width, height = sensor_asset.getDimensions()
		logger.debug(f'Setting view: {view} to SC: {sc_id}, Sensor Suite: {sens_suite_key}, sensor:{sens_key}')
		self.view_boxes[view].camera.set_range(x=(0,width), y=(0, height), margin=0)
		self.displayed_sensors[view] = sensor_asset


	def _getSensorAsset(self, sc_id: int, sens_suite_key: str, sens_key: str) -> tuple[sensors.SensorSuiteImageAsset,sensors.SensorImageAsset]:
		# TODO: index spacecraft list using sc_id
		suite_asset = self.assets['spacecraft'].getSensorSuiteByKey(sens_suite_key)
		sensor_asset = suite_asset.getSensorByKey(sens_key)

		return suite_asset, sensor_asset

	def getActiveAssets(self) -> list[base_assets.AbstractAsset|base_assets.AbstractCompoundAsset|base_assets.AbstractSimpleAsset]:
		active_assets = []
		for k,v in self.assets.items():
			if v.isActive():
				active_assets.append(k)
		return active_assets

	def setModel(self, hist_data:HistoryData, earth_raycast_data:EarthRayCastData) -> None:
		self.data_models['history'] = hist_data
		self.data_models['raycast_src'] = earth_raycast_data
		self.modelUpdated()

	def modelUpdated(self) -> None:
		logger.debug(f'updating model for {self}')
		# Update data source for earth asset
		if self.data_models['history'] is None:
			logger.error(f'canvas wrapper: {self} does not have a history data model yet')
			raise exceptions.InvalidDataError

		if self.data_models['raycast_src'] is None:
			logger.error(f'canvas wrapper: {self} does not have a raycast source data model yet')
			raise exceptions.InvalidDataError

		if self.data_models['history'].hasOrbits():
			if self.data_models['history'].getConfigValue('is_pointing_defined'):
				self.assets['spacecraft'].setSource(list(self.data_models['history'].getPrimaryConfig().getAllSpacecraftConfigs().values())[0],
													self.data_models['history'],
													self.data_models['raycast_src'])
				self.assets['spacecraft']._setActiveFlag()



	def updateIndex(self, index:int) -> None:
		for asset_name,asset in self.assets.items():
			if asset.isActive():
				asset.updateIndex(index)

	def recomputeRedraw(self) -> None:
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				asset.recomputeRedraw()

	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}
		return state

	def deSerialise(self, state:dict[str,Any]) -> None:
		pass

	def mapAssetPositionsToScreen(self) -> list:
		mo_infos = []
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				mo_infos.append(asset.getScreenMouseOverInfo())
		return mo_infos

	def on_key_press(self, event):
		pass

	def onMouseMove(self, event:MouseEvent) -> None:
		pass

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		pass		