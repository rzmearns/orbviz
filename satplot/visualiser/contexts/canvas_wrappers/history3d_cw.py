import json
import numpy as np
import time
from typing import Any

from PyQt5 import QtGui

from vispy import scene

from satplot.model.data_models.history_data import (HistoryData)
import satplot.model.geometry.primgeom as pg
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.util.constants as c
import satplot.util.exceptions as exceptions
import satplot.visualiser.assets.base as base_assets
import satplot.visualiser.assets.constellation as constellation
import satplot.visualiser.assets.earth as earth
import satplot.visualiser.assets.gizmo as gizmo
import satplot.visualiser.assets.orbit as orbit
import satplot.visualiser.assets.moon as moon
import satplot.visualiser.assets.spacecraft as spacecraft
import satplot.visualiser.assets.sun as sun
import satplot.visualiser.assets.widgets as widgets


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
		self.grid = self.canvas.central_widget.add_grid()
		self.view_box = self.canvas.central_widget.add_view()
		self.view_box.camera = scene.cameras.TurntableCamera(parent=self.view_box.scene,
													   		fov=60,
															center=(0,0,0),
															name='Turntable')

		self.data_model: HistoryData|None = None
		self.assets = {}
		self._buildAssets()
		self.mouseOverText = widgets.PopUpTextBox(v_parent=self.view_box,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)

	def _buildAssets(self) -> None:
		self.assets['earth'] = earth.Earth3DAsset(v_parent=self.view_box.scene)
		self.assets['primary_orbit'] = orbit.Orbit3DAsset(v_parent=self.view_box.scene)
		self.assets['moon'] = moon.Moon3DAsset(v_parent=self.view_box.scene)

		with open('./data/spacecraft/spirit.json') as fp:
			sc_sens_dict = json.load(fp)

		sens_suites={}
		sens_suites['loris'] = sc_sens_dict

		self.assets['spacecraft'] = spacecraft.Spacecraft3DAsset(v_parent=self.view_box.scene, sens_suites=sens_suites)

		self.assets['constellation'] = constellation.Constellation(v_parent=self.view_box.scene)
		self.assets['sun'] = sun.Sun3DAsset(v_parent=self.view_box.scene)

		# if self.is_asset_active['ECI_gizmo']:
		# self.assets['ECI_gizmo'] = ViewBoxGizmo(canvas=self.canvas,
		# 				   					parent=self.view_box.scene,
		# 									translate=(c.R_EARTH,c.R_EARTH),
		# 									scale=(2*c.R_EARTH,2*c.R_EARTH,2*c.R_EARTH,1))
		self.setCameraZoom(5*c.R_EARTH)
		# self.assets['ECI_gizmo'].attachCamera(self.view_box.camera)

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
			raise NameError
		
		self.view_box.camera = mode

	def setCameraZoom(self, zoom:float) -> None:
		self.view_box.camera.scale_factor = zoom

	def setModel(self, data:HistoryData) -> None:
		self.data_model = data
		self.modelUpdated()

	def modelUpdated(self) -> None:
		# Update data source for earth asset
		if self.data_model is None:
			raise exceptions.InvalidDataError



		if self.data_model.timespan is not None:
			self.assets['earth'].setSource(self.data_model.timespan)
			self.assets['earth'].makeActive()

		# Update data source for moon asset
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			self.assets['moon'].setSource(list(self.data_model.orbits.values())[0])
			self.assets['moon'].makeActive()



		# Update data source for primary orbit(s)
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			# TODO: extend to draw multiple primary satellites
			self.assets['primary_orbit'].setSource(self.data_model.getOrbits())
			self.assets['primary_orbit'].makeActive()

		if self.data_model.getConfigValue('is_pointing_defined'):
			self.assets['spacecraft'].setSource(self.data_model.getOrbits(),
												self.data_model.getPointings(),
												self.data_model.getConfigValue('pointing_invert_transform'))
			self.assets['spacecraft'].makeActive()
			self.assets['primary_orbit'].setOrbitalMarkerVisibility(False)
		else:
			# TODO: making this dormant at creation
			self.assets['spacecraft'].makeDormant()
			self.assets['primary_orbit'].setOrbitalMarkerVisibility(True)

		if self.data_model.getConfigValue('has_supplemental_constellation'):
			self.assets['constellation'].setSource(self.data_model.getConstellation().getOrbits(),
													self.data_model.getConstellation().getConfigValue('beam_angle_deg'))
			self.assets['constellation'].makeActive()

		# Update data source for sun asset
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			self.assets['sun'].setSource(self.data_model.getOrbits())
			self.assets['sun'].makeActive()


	def updateIndex(self, index:int) -> None:
		for asset_name,asset in self.assets.items():
			if asset.isActive():
				asset.updateIndex(index)

		# TODO: remove this (doesn't need to be in updateIndex, just when drawn)
		# Sun must be last so that umbra doesn't occlude objects
		# if self.assets['sun'].isActive():
		# 	self.assets['sun'].updateIndex(index)

	def recomputeRedraw(self) -> None:
		for asset_name, asset in self.assets.items():
			# if asset_name == 'sun':
			# 	continue
			if asset.isActive():
				asset.recomputeRedraw()

		# Sun must be last so that umbra doesn't occlude objects
		# if self.assets['sun'].isActive():
		# 	self.assets['sun'].recomputeRedraw()

	def forceRedraw(self) -> None:
		for k,v in self.assets.items():
			if v.isActive():
				v.forceRedraw()

	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def centerCameraSpacecraft(self, set_zoom:bool=True) -> None:
		if self.canvas is None:
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
		return state

	def deSerialise(self, state:dict[str,Any]) -> None:
		self.view_box.camera.center = state['cam-center']
		self.view_box.camera.scale_factor = state['cam-zoom']
		self.view_box.camera.azimuth = state['cam-az']
		self.view_box.camera.elevation = state['cam-el']
		self.view_box.camera.roll = state['cam-roll']

	def mapAssetPositionsToScreen(self) -> list:
		mo_infos = []
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				mo_infos.append(asset.getScreenMouseOverInfo())

		return mo_infos

	def onMouseMove(self, event:QtGui.QMouseEvent) -> None:
		global last_mevnt_time
		global mouse_over_is_highlighting
		
		# cull if behind center of camera plane
		az = np.deg2rad(self.view_box.camera.azimuth+179)
		el = np.deg2rad(self.view_box.camera.elevation)
		acamv = np.array([[0,0,0],[np.sin(-az)*np.cos(el),np.cos(-az)*np.cos(el),np.sin(el)]])
		
		# throttle mouse events to 100ms
		if time.monotonic() - last_mevnt_time < 0.1:
			return
		mo_infos = self.mapAssetPositionsToScreen()
		pp = event.pos()
		
		for jj, mo_info in enumerate(mo_infos):
			for ii, pos in enumerate(mo_info['screen_pos']):
				if ((abs(pos[0] - pp.x) < MOUSEOVER_DIST_THRESHOLD) and \
					(abs(pos[1] - pp.y) < MOUSEOVER_DIST_THRESHOLD)):
					dot = np.dot(pg.unitVector(mo_info['world_pos'][ii]),acamv[1,:])[0]
					if dot >=0:
						last_mevnt_time = time.monotonic()
						self.mouseOverText.setVisible(True)
						self.mouseOverText.setText(mo_info['strings'][ii].lower().capitalize())
						self.mouseOverText.setPos((pos[0]+5, pos[1]))
						mo_info['objects'][ii].mouseOver(ii)
						mouse_over_is_highlighting = True
						return

		self.mouseOverText.setVisible(False)
		if mouse_over_is_highlighting:
			self.forceRedraw()
			mouse_over_is_highlighting = False
		last_mevnt_time = time.monotonic()

		
		# console.send("captured event")
		# self.assets['ECI_gizmo'].onMouseMove(event)

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		# print(self.view_box.camera.scale_factor)
		pass		