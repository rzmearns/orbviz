from vispy import scene

from satplot.util import constants as c
from satplot.visualiser.assets.earth import Earth3DAsset
from satplot.visualiser.assets.orbit import Orbit3DAsset
from satplot.visualiser.assets.sun import Sun3DAsset
from satplot.visualiser.assets.moon import Moon3DAsset
from satplot.visualiser.assets.spacecraft import SpacecraftVisualiser
from satplot.visualiser.assets.widgets import PopUpTextBox
from satplot.visualiser.assets.constellation import Constellation
from satplot.visualiser.assets.gizmo import ViewBoxGizmo

from satplot.visualiser.controls import console
import json
import numpy as np
import time
import satplot.model.geometry.primgeom as pg

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False

class History3D():
	def __init__(self, w=800, h=600, keys='interactive', bgcolor='white'):
		self.canvas = scene.SceneCanvas(size=(w,h),
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

		self.assets = {}
		self._buildAssets()
		self.mouseOverText = PopUpTextBox(v_parent=self.view_box,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)

	def _buildAssets(self):
		self.assets['earth'] = Earth3DAsset(v_parent=self.view_box.scene)
		self.assets['earth'].makeActive()
		self.assets['primary_orbit'] = Orbit3DAsset(v_parent=self.view_box.scene)
		self.assets['moon'] = Moon3DAsset(v_parent=self.view_box.scene)
		self.assets['sun'] = Sun3DAsset(v_parent=self.view_box.scene)

		# self.assets['constellation'] = Constellation(v_parent=self.view_box.scene)

		# with open('./data/spacecraft/spirit.json') as fp:
		# 	sc_sens_dict = json.load(fp)

		# sens_suites={}
		# sens_suites['loris'] = sc_sens_dict

		# self.assets['spacecraft'] = SpacecraftVisualiser(v_parent=self.view_box.scene, sens_suites=sens_suites)




		# if self.is_asset_active['ECI_gizmo']:
		# self.assets['ECI_gizmo'] = ViewBoxGizmo(canvas=self.canvas,
		# 				   					parent=self.view_box.scene,
		# 									translate=(c.R_EARTH,c.R_EARTH),
		# 									scale=(2*c.R_EARTH,2*c.R_EARTH,2*c.R_EARTH,1))
		self.setCameraZoom(5*c.R_EARTH)
		# self.assets['ECI_gizmo'].attachCamera(self.view_box.camera)

	def getActiveAssets(self):
		active_assets = []
		for k,v in self.assets.items():
			if v.isActive():
				active_assets.append(k)
		return active_assets

	def setCameraMode(self, mode='turntable'):
		allowed_cam_modes = ['turntable',
					   		'arcball',
							'fly',
							'panzoom',
							'magnify',
							'perspective']
		if mode not in allowed_cam_modes:
			raise NameError
		
		self.view_box.camera = mode

	def setCameraZoom(self, zoom):
		self.view_box.camera.scale_factor = zoom

	def setModel(self, data):
		self.data_model = data
		self.modelUpdated()

	def modelUpdated(self):
		# Update data source for earth asset
		if self.data_model.timespan is not None:
			self.assets['earth'].setSource(self.data_model.timespan)
			self.assets['earth'].makeActive()

		# Update data source for moon asset
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			self.assets['moon'].setSource(list(self.data_model.orbits.values())[0])
			self.assets['moon'].makeActive()

		# Update data source for sun asset
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			self.assets['sun'].setSource(list(self.data_model.orbits.values())[0])
			self.assets['sun'].makeActive()

		# Update data source for primary orbit(s)
		if len(self.data_model.getConfigValue('primary_satellite_ids')) > 0:
			# TODO: extend to draw multiple primary satellites
			self.assets['primary_orbit'].setSource(list(self.data_model.orbits.values())[0])
			self.assets['primary_orbit'].makeActive()


		# if self.data_model.getConfigValue('is_pointing_defined':
		# 	self.assets['spacecraft'].setModel(list(self.data_model.orbits.values())[0],
		# 										list(self.data_model.pointings.values())[0],
		# 										self.data_model['pointing_invert_transform'])
		# 	self.is_asset_active['spacecraft'] = True
		# elif self.is_asset_active['spacecraft']:
		# 	# No pointing on this recalculate, but there is a spacecraft asset
		# 	self.is_asset_active['spacecraft'] = False
		# 	self.assets['spacecraft'].setSpacecraftAssetVisibility(False)
		# 	self.assets['primary_orbit'].setOrbitalMarkerVisibility(True)
		# else:
		# 	self.assets['primary_orbit'].setOrbitalMarkerVisibility(True)

		# if self.data_model['has_supplemental_constellation']:
		# 	self.assets['constellation'].setModel(c_list, c_beam_angle)
		# 	self.is_asset_active['constellation'] = True



	def updateIndex(self, index):
		for asset_name,asset in self.assets.items():
			if asset.isActive():
				asset.updateIndex(index)

		# TODO: remove this (doesn't need to be in updateIndex, just when drawn)
		# Sun must be last so that umbra doesn't occlude objects
		if self.assets['sun'].isActive():
			self.assets['sun'].updateIndex(index)

	def recomputeRedraw(self):
		for asset_name, asset in self.assets.items():
			if asset_name == 'sun':
				continue
			if asset.isActive():
				asset.recomputeRedraw()

		# Sun must be last so that umbra doesn't occlude objects
		if self.assets['sun'].isActive():
			self.assets['sun'].recomputeRedraw()

	def forceRedraw(self):
		for k,v in self.assets.items():
			if self.is_asset_active[k]:
				v.forceRedraw()

	def setFirstDrawFlags(self):
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def centerCameraSpacecraft(self, set_zoom=True):
		if self.is_asset_active['spacecraft']:
			sc_pos = tuple(self.assets['spacecraft'].data['coords'][self.assets['spacecraft'].data['curr_index']])			
		else:
			sc_pos = tuple(self.assets['primary_orbit'].data['coords'][self.assets['primary_orbit'].data['curr_index']])

		self.view_box.camera.center = sc_pos
		if set_zoom:
			self.setCameraZoom(2200)
		self.canvas.update()


	def centerCameraEarth(self):
		self.view_box.camera.center = (0,0,0)
		self.setCameraZoom(5*c.R_EARTH)
		self.canvas.update()

	def prepSerialisation(self):
		state = {}
		state['cam-center'] = self.view_box.camera.center
		state['cam-zoom'] = self.view_box.camera.scale_factor
		state['cam-az'] = self.view_box.camera.azimuth
		state['cam-el'] = self.view_box.camera.elevation
		state['cam-roll'] = self.view_box.camera.roll
		return state

	def deSerialise(self, state):
		self.view_box.camera.center = state['cam-center']
		self.view_box.camera.scale_factor = state['cam-zoom']
		self.view_box.camera.azimuth = state['cam-az']
		self.view_box.camera.elevation = state['cam-el']
		self.view_box.camera.roll = state['cam-roll']

	def mapAssetPositionsToScreen(self):
		mo_infos = []
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				mo_infos.append(asset.getScreenMouseOverInfo())

		return mo_infos

	def onMouseMove(self, event):
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

	def onMouseScroll(self, event):
		# print(self.view_box.camera.scale_factor)
		pass		