import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import gizmo

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons

import satplot.visualiser.controls.console as console
import satplot.visualiser.assets.sensors as sensors
from scipy.spatial.transform import Rotation

import geopandas as gpd

from vispy import scene, color
from vispy.visuals import transforms as vTransforms

import numpy as np

class SpacecraftVisualiser(BaseAsset):
	def __init__(self, canvas=None, parent=None,  sc_sens_suite=None):
	
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False

		self.parent = parent
		self.canvas = canvas
		self.data['sc_sens_suite_dict'] = sc_sens_suite

		self._setDefaultOptions()	
		self._initDummyData()
		self.draw()
	
	def draw(self):
		self.addOrbitalMarker()
		self.addBodyFrame()
		if self.data['sc_sens_suite_dict'] is not None:
			self.addSensorSuite()

	def compute(self):
		pass

	def _initDummyData(self):
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		
	def setSource(self, source, pointing):
		self.data['coords'] = source.pos
		self.data['pointing'] = pointing

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.requires_recompute:
			self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['spacecraft_point_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_point_colour']['value']))
			#TODO: This check could be done better
			if np.any(np.isnan(self.data['pointing'][self.data['curr_index'],:])):
				non_nan_found = False
				for ii in range(self.data['curr_index'], len(self.data['pointing'])):
					if np.all(np.isnan(self.data['pointing'][ii,:])==False):
						non_nan_found = True
						quat = self.data['pointing'][ii,:].reshape(-1,4)
						rotation = Rotation.from_quat(quat).as_matrix()
						break				
				if not non_nan_found:
					for ii in range(self.data['curr_index'], -1, -1):
						if np.all(np.isnan(self.data['pointing'][ii,:])==False):
							quat = self.data['pointing'][ii,:].reshape(-1,4)
							rotation = Rotation.from_quat(quat).as_matrix()
							break
				self.visuals['body_frame'].setTemporaryGizmoXColour((255,0,255))
				self.visuals['body_frame'].setTemporaryGizmoYColour((255,0,255))
				self.visuals['body_frame'].setTemporaryGizmoZColour((255,0,255))
			else:
				quat = self.data['pointing'][self.data['curr_index']].reshape(-1,4)
				rotation = Rotation.from_quat(quat).as_matrix()
				self.visuals['body_frame'].restoreGizmoColours()
			# rotation = Rotation.align_vectors(np.array((0,0,1)).reshape(1,3),
			# 									-self.data['coords'][self.data['curr_index']].reshape(1,3))[0].as_matrix()
			self.visuals['body_frame'].setTransform(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
										   			rotation=rotation)
			self.visuals['sensor_suite'].setTransform(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
										   			quat=quat)
			self.requires_recompute = False

	def addOrbitalMarker(self):
		self.visuals['marker'] = scene.visuals.Markers(parent=self.parent, scaling=True, antialias=0)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['spacecraft_point_colour']['value']),
										edge_color='white',
										size=self.opts['spacecraft_point_size']['value'],
										symbol='o')

	def addBodyFrame(self):
		self.visuals['body_frame'] = gizmo.BodyGizmo(parent=self.parent, scale=700, width=3)

	def addSensorSuite(self):
		self.visuals['sensor_suite'] = sensors.SensorSuite(self.data['sc_sens_suite_dict'], parent=self.parent)

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_spacecraft'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setSpacecraftAssetVisibility}		
		self._dflt_opts['spacecraft_point_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'callback': self.setMarkerColour}
		self._dflt_opts['plot_spacecraft_point'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalMarkerVisibility}
		self._dflt_opts['spacecraft_point_size'] = {'value': 250,
										  		'type': 'number',
												'help': '',
												'callback': None}
		self._dflt_opts['plot_body_frame'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'callback': self.setBodyFrameVisibility}
		self._dflt_opts['plot_sensor_suite'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'callback': self.setSensorSuiteVisibility}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass
	
	def setMarkerColour(self, new_colour):
		self.opts['spacecraft_point_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['marker'].set_data(face_color=colours.normaliseColour(new_colour))

	def setSpacecraftAssetVisibility(self, state):
		self.setOrbitalMarkerVisibility(state)
		self.setBodyFrameVisibility(state)
		self.setSensorSuiteVisibility(state)

	def setSensorSuiteVisibility(self, state):
		self.visuals['sensor_suite'].setVisibility(state)

	def setOrbitalMarkerVisibility(self, state):
		self.visuals['marker'].visible = state

	def setBodyFrameVisibility(self, state):
		self.visuals['body_frame'].setVisibility(state)