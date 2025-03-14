import json
import numpy as np
import time
from typing import Any

from PyQt5 import QtGui

from numpy._typing import _array_like
from vispy import scene
import vispy
from vispy.app.canvas import MouseEvent

from satplot.model.data_models.history_data import (HistoryData)
import satplot.model.geometry.primgeom as pg
from satplot.model.data_models.data_types import PrimaryConfig
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.util.constants as c
import satplot.util.exceptions as exceptions
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.constellation as constellation
import satplot.visualiser.assets.earth as earth
import satplot.visualiser.assets.sky as sky
import satplot.visualiser.assets.gizmo as gizmo
import satplot.visualiser.assets.orbit as orbit
import satplot.visualiser.assets.moon as moon
import satplot.visualiser.assets.spacecraft as spacecraft
import satplot.visualiser.assets.sun as sun
import satplot.visualiser.assets.widgets as widgets
import satplot.visualiser.cameras.cameras as cameras


create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False


class SensorView3DCanvasWrapper(BaseCanvas):
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
		# vb2 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		# vb3 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		# vb4 = scene.widgets.ViewBox(border_color='black', parent=self.canvas.scene)
		# scenes = vb1.scene, vb2.scene, vb3.scene, vb4.scene
		# self.view_boxes = [vb1, vb2, vb3, vb4]
		self.view_box = vb1

		self.grid.add_widget(self.view_box,0,0)
		# self.grid.add_widget(self.view_boxes[0],0,0)
		# self.grid.add_widget(self.view_boxes[1],0,1)
		# self.grid.add_widget(self.view_boxes[2],1,0)
		# self.grid.add_widget(self.view_boxes[3],1,1)

		# vb1.camera = scene.cameras.TurntableCamera(parent=self.view_box.scene,
		# 									   		fov=60,
		# 											center=(0,0,0),
		# 											name='Turntable')
		# vb1.camera = scene.cameras.FlyCamera(parent=self.view_box.scene,
		# 									   		fov=60,
		# 											center=(0,0,0),
		# 											scale_factor=0)
		vb1.camera = cameras.FixedCamera(parent=self.view_box.scene,fov=62.2,distance=0.1)
		# vb1.camera = cameras.MovableFixedCamera(parent=self.view_box.scene,fov=62.2,distance=0.1)
		# vb1.camera._near_clip_distance = 0.01
		vb1.camera.name = 'fixed'
		# vb1.camera.depth_value = 2e-9

		# vb1.camera = scene.BaseCamera()

		# vb2.camera = scene.BaseCamera()
		# vb3.camera = scene.BaseCamera()
		# vb4.camera = scene.BaseCamera()

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
		# self.assets['sky'] = sky.Sky3DAsset(v_parent=self.view_box.scene)
		self.assets['earth'] = earth.Earth3DAsset(v_parent=self.view_box.scene)
		self.assets['primary_orbit'] = orbit.Orbit3DAsset(v_parent=self.view_box.scene)
		self.assets['moon'] = moon.Moon3DAsset(v_parent=self.view_box.scene)

		self.assets['spacecraft'] = spacecraft.Spacecraft3DAsset(v_parent=self.view_box.scene)

		self.assets['constellation'] = constellation.Constellation(v_parent=self.view_box.scene)
		self.assets['sun'] = sun.Sun3DAsset(v_parent=self.view_box.scene)


		# if self.is_asset_active['ECI_gizmo']:
		# self.assets['ECI_gizmo'] = ViewBoxGizmo(canvas=self.canvas,
		# 				   					parent=self.view_box.scene,
		# 									translate=(c.R_EARTH,c.R_EARTH),
		# 									scale=(2*c.R_EARTH,2*c.R_EARTH,2*c.R_EARTH,1))
		# self.setCameraZoom(5*c.R_EARTH)
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

	# def setCameraZoom(self, zoom:float) -> None:
	# 	self.view_box.camera.scale_factor = zoom

	def setModel(self, hist_data:HistoryData) -> None:
		self.data_models['history'] = hist_data
		self.modelUpdated()

	def modelUpdated(self) -> None:
		# Update data source for earth asset
		if self.data_models['history'] is None:
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
				# self.assets['sky'].makeActive()

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

		self._updateCamera()

	def recomputeRedraw(self) -> None:
		for asset_name, asset in self.assets.items():
			# if asset_name == 'sun':
			# 	continue
			if asset.isActive():
				asset.recomputeRedraw()

	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def _updateCamera(self):
		if self.assets['spacecraft'].isActive():
			sc_pos = tuple(self.assets['spacecraft'].data['coords'][self.assets['spacecraft'].data['curr_index']])
		else:
			sc_pos = tuple(self.assets['primary_orbit'].data['coords'][self.assets['primary_orbit'].data['curr_index']])

		sc_quat = self.assets['spacecraft'].assets['sensor_suite_Axes'].assets['NegZ'].data['vispy_quat'].reshape(4,)
		sc_quat = tuple(sc_quat.reshape(4,))
		self.view_box.camera.setPose(sc_pos,sc_quat,scaler_first=False)
		# self.view_box.camera.center = sc_pos


	# def _updateCameraRotation(self):
	# 	# self.view_box.camera.rotation1 = self.assets['spacecraft'].assets['sensor_suite_Axes'].assets['NegZ'].data['vispy_quat']
	# 	self.view_box.camera._quaternion = self.assets['spacecraft'].assets['sensor_suite_Axes'].assets['NegZ'].data['vispy_quat']


	# def centerCameraSpacecraft(self, set_zoom:bool=True) -> None:
	# 	if self.canvas is None:
	# 		raise AttributeError(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
	# 	if self.assets['spacecraft'].isActive():
	# 		sc_pos = tuple(self.assets['spacecraft'].data['coords'][self.assets['spacecraft'].data['curr_index']])
	# 	else:
	# 		sc_pos = tuple(self.assets['primary_orbit'].data['coords'][self.assets['primary_orbit'].data['curr_index']])

	# 	self.view_box.camera.center = sc_pos
	# 	if set_zoom:
	# 		self.setCameraZoom(2200)
	# 	self.canvas.update()


	# def centerCameraEarth(self) -> None:
	# 	if self.canvas is None:
	# 		raise AttributeError(f"Canvas has not been set for History3D Canvas Wrapper. No camera to center")
	# 	self.view_box.camera.center = (0,0,0)
	# 	self.setCameraZoom(5*c.R_EARTH)
	# 	self.canvas.update()

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

	def on_key_press(self, event):
		print(f'KEY PRESS')
		if event.key == 'down':
			self.view_box.camera.depth_value /= 10
			print(f'{self.view_box.camera.depth_value=}')
			# sphere2.mesh.update()

		if event.key == 'up':
			self.view_box.camera.depth_value *= 10
			print(f'{self.view_box.camera.depth_value=}')
			# sphere2.mesh.update()

	def onMouseMove(self, event:MouseEvent) -> None:
		global last_mevnt_time
		# throttle mouse events to 50ms
		if time.monotonic() - last_mevnt_time < 0.05:
			return
		last_mevnt_time = time.monotonic()
		self.assets['sky'].on_mouse_move(event,self.canvas)
		# global last_mevent_time
		# # throttle mouse events to 50ms
		# if time.monotonic() - throttle < 0.05:
		# 	return
		# last_mevent_time = time.monotonic()

		# # adjust the event position for hidpi screens
		# render_size = tuple(d * self.canvas.pixel_scale for d in self.canvas.size)
		# x_pos = event.pos[0] * self.canvas.pixel_scale
		# y_pos = render_size[1] - (event.pos[1] * self.canvas.pixel_scale)

		# # render a small patch around the mouse cursor
		# restore_state = not face_picking_filter.enabled
		# face_picking_filter.enabled = True
		# sphere2.mesh.update_gl_state(blend=False)
		# picking_render = self.canvas.render(
		# 	region=(x_pos - 1, y_pos - 1, 3, 3),
		# 	size=(3, 3),
		# 	bgcolor=(0, 0, 0, 0),
		# 	alpha=True,
		# )
		# if restore_state:
		# 	face_picking_filter.enabled = False
		# sphere2.mesh.update_gl_state(blend=not face_picking_filter.enabled)

		# # unpack the face index from the color in the center pixel
		# face_idx = (picking_render.view(np.uint32) - 1)[1, 1, 0]
		# # print(f'A:{face_idx=}')
		# if face_idx > 0 and face_idx < num_faces:
		# 	# this may be less safe, but it's faster than set_data
		# 	# print(f'B:{face_idx=}')
		# 	# sphere2.mesh.mesh_data._face_colors_indexed_by_faces[face_idx] = (0, 1, 0, 1)
		# 	# if face_idx == crit_face_idx:
		# 	#     print(f'{getFaceCentroid(face_idx,sphere2.mesh._meshdata)=}')
		# 	r,theta,phi = getRaDecECI(getFaceCentroid(face_idx,sphere2.mesh._meshdata))
		# 	print(f'{r,theta,phi}')
		# 	sphere2.mesh.mesh_data_changed()

		
		# console.send("captured event")
		# self.assets['ECI_gizmo'].onMouseMove(event)

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		# print(self.view_box.camera.scale_factor)
		pass		