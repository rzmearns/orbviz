import json
import logging
import numpy as np
import time
from typing import Any

from PyQt5 import QtGui

from vispy import scene
from vispy.app.canvas import MouseEvent, ResizeEvent

from satplot.model.data_models.history_data import (HistoryData)
import satplot.model.geometry.primgeom as pg
from satplot.model.data_models.data_types import PrimaryConfig
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.util.constants as c
import satplot.util.exceptions as exceptions
# import satplot.visualiser.assets.axis_indicators as axis_indicators
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.constellation as constellation
import satplot.visualiser.assets.earth as earth
import satplot.visualiser.assets.gizmo as gizmo
import satplot.visualiser.assets.orbit as orbit
import satplot.visualiser.assets.moon as moon
import satplot.visualiser.assets.spacecraft as spacecraft
import satplot.visualiser.assets.sun as sun
import satplot.visualiser.assets.widgets as widgets

from vispy.visuals.transforms import STTransform

logger = logging.getLogger(__name__)

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False


class History3DCanvasWrapper(BaseCanvas):
	def __init__(self, w:int=800, h:int=600, keys:str='interactive', bgcolor:str='white'):
		self.canvas = scene.canvas.SceneCanvas(size=(w,h),
										keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.canvas.events.mouse_move.connect(self.onMouseMove)
		self.canvas.events.mouse_wheel.connect(self.onMouseScroll)
		self.canvas.events.resize.connect(self.onResize)
		self.grid = self.canvas.central_widget.add_grid()
		self.view_box = self.canvas.central_widget.add_view()
		self.view_box.camera = scene.cameras.TurntableCamera(parent=self.view_box.scene,
															fov=60,
															center=(0,0,0),
															name='Turntable')
		self.data_models: dict[str,Any] = {}
		self.assets = {}
		self._buildAssets()
		self.mouseOverText = widgets.PopUpTextBox(v_parent=self.view_box,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)
		self.mouseOverObject = None

	def _buildAssets(self) -> None:
		self.assets['earth'] = earth.Earth3DAsset(v_parent=self.view_box.scene)
		self.assets['primary_orbit'] = orbit.Orbit3DAsset(v_parent=self.view_box.scene)
		self.assets['moon'] = moon.Moon3DAsset(v_parent=self.view_box.scene)

		self.assets['spacecraft'] = spacecraft.Spacecraft3DAsset(v_parent=self.view_box.scene)

		self.assets['constellation'] = constellation.Constellation(v_parent=self.view_box.scene)
		self.assets['sun'] = sun.Sun3DAsset(v_parent=self.view_box.scene)

		self.assets['ECI_gizmo'] = gizmo.ViewBoxGizmo(v_parent=self.view_box)
		self.setCameraZoom(5*c.R_EARTH)

	def getActiveAssets(self) -> list[base_assets.AbstractAsset|base_assets.AbstractCompoundAsset|base_assets.AbstractSimpleAsset]:
		active_assets = []
		for k,v in self.assets.items():
			if v.isActive():
				active_assets.append(k)
		return active_assets

	def setCameraMode(self, mode:str='turntable') -> None:
		allowed_cam_modes = ['turntable',
							'arcball',
							'fly',
							'panzoom',
							'magnify',
							'perspective']
		if mode not in allowed_cam_modes:
			logger.error(f'specified camera mode is not a valid mode: {mode}')
			raise NameError

		self.view_box.camera = mode

	def setCameraZoom(self, zoom:float) -> None:
		self.view_box.camera.scale_factor = zoom

	def setModel(self, hist_data:HistoryData) -> None:
		self.data_models['history'] = hist_data
		self.modelUpdated()

	def modelUpdated(self) -> None:
		# Update data source for earth asset
		if self.data_models['history'] is None:
			logger.error(f'canvas wrapper: {self} does not have a history data model yet')
			raise exceptions.InvalidDataError

		if self.data_models['history'].timespan is not None:
			self.assets['earth'].setSource(self.data_models['history'].timespan)
			self.assets['earth'].makeActive()

		# Update data source for moon asset
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			self.assets['moon'].setSource(list(self.data_models['history'].orbits.values())[0])
			self.assets['moon'].makeActive()


		# Update data source for primary orbit(s)
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			# TODO: extend to draw multiple primary satellites
			self.assets['primary_orbit'].setSource(self.data_models['history'].getOrbits())
			self.assets['primary_orbit'].makeActive()

		if self.data_models['history'].hasOrbits():
			if self.data_models['history'].getConfigValue('is_pointing_defined'):
				self.assets['spacecraft'].setSource(self.data_models['history'].getOrbits(),
													self.data_models['history'].getPointings(),
													self.data_models['history'].getConfigValue('pointing_invert_transform'),
													list(self.data_models['history'].getPrimaryConfig().getAllSpacecraftConfigs().values())[0])
				self.assets['spacecraft'].makeActive()
				self.assets['spacecraft'].setOrbitalMarkerVisibility(False)
				self.assets['spacecraft'].setAttitudeAssetsVisibility(True)
			else:
				self.assets['spacecraft'].setSource(self.data_models['history'].getOrbits(),
													None,
													None,
													list(self.data_models['history'].getPrimaryConfig().getAllSpacecraftConfigs().values())[0])
				self.assets['spacecraft'].makeActive()
				self.assets['spacecraft'].setOrbitalMarkerVisibility(True)
				self.assets['spacecraft'].setAttitudeAssetsVisibility(False)

		if self.data_models['history'].getConfigValue('has_supplemental_constellation'):
			self.assets['constellation'].setSource(self.data_models['history'].getConstellation().getOrbits(),
													self.data_models['history'].getConstellation().getConfigValue('beam_angle_deg'))
			self.assets['constellation'].makeActive()
		else:
			self.assets['constellation'].makeDormant()

		# Update data source for sun asset
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			self.assets['sun'].setSource(self.data_models['history'].getOrbits())
			self.assets['sun'].makeActive()


	def updateIndex(self, index:int) -> None:
		for asset_name,asset in self.assets.items():
			if asset.isActive():
				asset.updateIndex(index)

	def recomputeRedraw(self) -> None:
		for asset_name, asset in self.assets.items():
			# if asset_name == 'sun':
			# 	continue
			if asset.isActive():
				asset.recomputeRedraw()


	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def centerCameraSpacecraft(self, set_zoom:bool=True) -> None:
		if self.canvas is None:
			logger.warning(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
			raise AttributeError(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
		if self.assets['spacecraft'].isActive():
			sc_pos = tuple(self.assets['spacecraft'].data['coords'][self.assets['spacecraft'].data['curr_index']])
		else:
			sc_pos = tuple(self.assets['primary_orbit'].data['coords'][self.assets['primary_orbit'].data['curr_index']])

		self.view_box.camera.center = sc_pos
		if set_zoom:
			self.setCameraZoom(2200)
		self.canvas.update()


	def centerCameraEarth(self) -> None:
		if self.canvas is None:
			logger.warning(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
			raise AttributeError(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
		self.view_box.camera.center = (0,0,0)
		self.setCameraZoom(5*c.R_EARTH)
		self.canvas.update()

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}
		state['cam-center'] = self.view_box.camera.center
		state['cam-zoom'] = self.view_box.camera.scale_factor
		state['cam-az'] = self.view_box.camera.azimuth
		state['cam-el'] = self.view_box.camera.elevation
		state['cam-roll'] = self.view_box.camera.roll
		asset_states = {}
		for asset_name, asset in self.assets.items():
			asset_states[asset_name] = asset.prepSerialisation()

		state['asset_states'] = asset_states
		return state

	def deSerialise(self, state:dict[str,Any]) -> None:
		self.view_box.camera.center = state['cam-center']
		self.view_box.camera.scale_factor = state['cam-zoom']
		self.view_box.camera.azimuth = state['cam-az']
		self.view_box.camera.elevation = state['cam-el']
		self.view_box.camera.roll = state['cam-roll']
		for asset_name, asset in self.assets.items():
			asset.deSerialise(state['asset_states'][asset_name])

	def mapAssetPositionsToScreen(self) -> list:
		mo_infos = []
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				mo_infos.append(asset.getScreenMouseOverInfo())

		return mo_infos

	def onMouseMove(self, event:MouseEvent) -> None:
		global last_mevnt_time
		global mouse_over_is_highlighting
		# for asset_name,asset in self.assets.items():
		# 	if asset.isActive():
		# 		asset.onMouseMove(event)
		self.assets['ECI_gizmo'].onMouseMove(event)

		# cull if behind center of camera plane
		az = np.deg2rad(self.view_box.camera.azimuth+179)
		el = np.deg2rad(self.view_box.camera.elevation)
		acamv = np.array([[0,0,0],[np.sin(-az)*np.cos(el),np.cos(-az)*np.cos(el),np.sin(el)]])

		# throttle mouse events to 100ms
		if time.monotonic() - last_mevnt_time < 0.1:
			return
		mo_infos = self.mapAssetPositionsToScreen()
		pp = event.pos

		for jj, mo_info in enumerate(mo_infos):
			for ii, pos in enumerate(mo_info['screen_pos']):
				if ((abs(pos[0] - pp[0]) < MOUSEOVER_DIST_THRESHOLD) and \
					(abs(pos[1] - pp[1]) < MOUSEOVER_DIST_THRESHOLD)):
					dot = np.dot(pg.unitVector(mo_info['world_pos'][ii]),acamv[1,:])[0]
					if dot >=0:
						last_mevnt_time = time.monotonic()
						self.mouseOverText.setVisible(True)
						self.mouseOverText.setText(mo_info['strings'][ii].lower().capitalize())
						self.mouseOverText.setPos((pos[0]+5, pos[1]))
						self.mouseOverObject = mo_info['objects'][ii].mouseOver(ii)
						mouse_over_is_highlighting = True
						return

		self.mouseOverText.setVisible(False)
		if mouse_over_is_highlighting:
			if self.mouseOverObject is not None:
				self.mouseOverObject = self.mouseOverObject.restoreMouseOver()
			mouse_over_is_highlighting = False
		last_mevnt_time = time.monotonic()

	def onResize(self, event:ResizeEvent) -> None:
		self.assets['ECI_gizmo'].onResize(event)

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		pass		