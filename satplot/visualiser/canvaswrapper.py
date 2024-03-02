from vispy import scene

from satplot.util import constants as c
from satplot.visualiser.assets.earth import Earth
from satplot.visualiser.assets.orbit import OrbitVisualiser
from satplot.visualiser.assets.sun import Sun
from satplot.visualiser.assets.moon import Moon
from satplot.visualiser.assets.spacecraft import SpacecraftVisualiser
from satplot.visualiser.assets.constellation import Constellation
from satplot.visualiser.assets.gizmo import ViewBoxGizmo

from satplot.visualiser.controls import console
import json
import numpy as np

class CanvasWrapper():
	def __init__(self, w=800, h=600, keys='interactive', bgcolor='white'):
		self.canvas = scene.SceneCanvas(size=(w,h),
								  		keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.canvas.events.key_press.connect(self.onKeyPress)
		self.canvas.events.mouse_move.connect(self.onMouseMove)
		self.canvas.events.mouse_wheel.connect(self.onMouseScroll)
		self.grid = self.canvas.central_widget.add_grid()
		self.view_box = self.canvas.central_widget.add_view()
		self.view_box.camera = scene.cameras.TurntableCamera(parent=self.view_box.scene,
													   		fov=60,
															center=(0,0,0),
															name='Turntable')
		self.is_asset_instantiated = {}
		self.assets = {}
		self.initAssetInstantiatedFlags()
		self.buildScene()

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

	def setSource(self, timespan, orbit, pointing=None, c_list=None, c_beam_angle=None):
		self.assets['earth'].setSource(timespan)
		self.is_asset_instantiated['earth'] = True
		self.assets['moon'].setSource(orbit)
		self.is_asset_instantiated['moon'] = True

		self.assets['primary_orbit'].setSource(orbit)
		self.is_asset_instantiated['primary_orbit'] = True
		if pointing is not None:
			self.assets['spacecraft'].setSource(orbit, pointing)
			self.is_asset_instantiated['spacecraft'] = True
		elif self.is_asset_instantiated['spacecraft']:
			# No pointing on this recalculate, but there is a spacecraft asset
			self.is_asset_instantiated['spacecraft'] = False
			self.assets['spacecraft'].setSpacecraftAssetVisibility(False)
			self.assets['primary_orbit'].setOrbitalMarkerVisibility(True)
		else:
			self.assets['primary_orbit'].setOrbitalMarkerVisibility(True)
		
		if c_list is not None:
			self.assets['constellation'].setSource(c_list, c_beam_angle)
			self.is_asset_instantiated['constellation'] = True

		self.assets['sun'].setSource(orbit)
		self.is_asset_instantiated['sun'] = True

	def initAssetInstantiatedFlags(self):
		self.is_asset_instantiated['primary_orbit'] = False
		self.is_asset_instantiated['sun'] = False
		self.is_asset_instantiated['moon'] = False
		self.is_asset_instantiated['constellation'] = False
		self.is_asset_instantiated['earth'] = False
		self.is_asset_instantiated['spacecraft'] = False
		self.is_asset_instantiated['ECI_gizmo'] = False

	def updateIndex(self, index):
		if self.is_asset_instantiated['primary_orbit']:
			self.assets['primary_orbit'].updateIndex(index)
		if self.is_asset_instantiated['earth']:
			self.assets['earth'].updateIndex(index)
		if self.is_asset_instantiated['moon']:
			self.assets['moon'].updateIndex(index)
		if self.is_asset_instantiated['constellation']:
			self.assets['constellation'].updateIndex(index)
		if self.is_asset_instantiated['spacecraft']:
			self.assets['spacecraft'].updateIndex(index)
		# Sun must be last so that umbra doesn't occlude objects
		if self.is_asset_instantiated['sun']:
			self.assets['sun'].updateIndex(index)

	# TODO: change this to setFirstDrawFlags()
	def setFirstDrawFlags(self):
		for key,value in self.is_asset_instantiated.items():
			if value:
				self.assets[key].setFirstDrawFlag()

	def buildScene(self):		
		self.assets['earth'] = Earth(v_parent=self.view_box.scene)
		self.assets['primary_orbit'] = OrbitVisualiser(v_parent=self.view_box.scene)
		self.assets['moon'] = Moon(v_parent=self.view_box.scene)
		self.assets['constellation'] = Constellation(v_parent=self.view_box.scene)	
	
		# with open('./data/spacecraft/spirit.json') as fp:
		# 	sc_sens_dict = json.load(fp)

		# self.assets['spacecraft'] = SpacecraftVisualiser(canvas=self.canvas,
		# 									parent=self.view_box.scene, sc_sens_suite=sc_sens_dict)

		self.assets['sun'] = Sun(v_parent=self.view_box.scene)


		# if self.is_asset_instantiated['ECI_gizmo']:
		# self.assets['ECI_gizmo'] = ViewBoxGizmo(canvas=self.canvas,
		# 				   					parent=self.view_box.scene,
		# 									translate=(c.R_EARTH,c.R_EARTH),
		# 									scale=(2*c.R_EARTH,2*c.R_EARTH,2*c.R_EARTH,1))
		self.setCameraZoom(5*c.R_EARTH)
		# self.assets['ECI_gizmo'].attachCamera(self.view_box.camera)

	def onMouseMove(self, event):
		pass
		# console.send("captured event")
		# self.assets['ECI_gizmo'].onMouseMove(event)

	def onMouseScroll(self, event):
		# print(self.view_box.camera.scale_factor)
		pass
		
	def onKeyPress(self, event):
		if event.key == "Home":
			self.view_box.camera.center = (0,0,0)
			self.setCameraZoom(5*c.R_EARTH)
			self.canvas.update()

		if event.key == "End":
			if self.is_asset_instantiated['spacecraft']:
				sc_pos = tuple(self.assets['spacecraft'].data['coords'][self.assets['spacecraft'].data['curr_index']])
				self.view_box.camera.center = sc_pos
				self.setCameraZoom(2200)
				self.canvas.update()