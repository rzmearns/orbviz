import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset

import satplot.visualiser.controls.console as console
import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.geometry.primgeom as pg

from scipy.spatial.transform import Rotation
import scipy.special as sc

from vispy import scene
from vispy.visuals import transforms as vTransforms
from vispy.scene import visuals as vVisuals
from vispy.visuals import filters as vFilters

import numpy as np

import satplot

class Constellation(BaseAsset):
	def __init__(self, canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False
		self.first_draw = True
		self._setDefaultOptions()
		self.visuals['markers']	= None
		self.visuals['beams'] = None
		self._initDummyData()
		self.draw()

	def compute(self):
		pass

	def _initDummyData(self):
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		
	def setSource(self, source_list, beam_angle):
		self.data['beam_angle_deg'] = beam_angle
		if len(source_list) > 1:
			self.data['coords'] = np.zeros((len(source_list),len(source_list[0].pos),3))
			for ii in range(len(source_list)):
				self.data['coords'][ii,:,:] = source_list[ii].pos
			self.data['num_sats'] = len(source_list)
			self.data['beam_height'] = self.calcBeamHeight(beam_angle/2, np.linalg.norm(source_list[0].pos[0,:]))
		else:
			self.data['coords'] = np.zeros((len(source_list[0].pos),3))
			self.data['coords'][:,:] = source_list[0].pos
			self.data['num_sats'] = 1
			self.data['beam_height'] = self.calcBeamHeight(beam_angle/2, np.linalg.norm(source_list[0].pos[0,:]))

		self.visuals['beams'].setSource(self.data['num_sats'],
								  		self.data['coords'],
										self.data['curr_index'],
										self.data['beam_height'],
										self.data['beam_angle_deg'])

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.visuals['beams'].updateIndex(new_index)
		self.requires_recompute = True
		self.recompute()

	def setFirstDraw(self):
		self.first_draw = True
		self.visuals['beams'].setFirstDraw(True)

	def recompute(self):
		if self.first_draw:
			if self.visuals['markers'] is not None:
				# Must do this to clear old visuals before creating a new one
				# TODO: not clear if this is actually deleting or just removing the reference (memory leak?)
				self.visuals['markers'].parent = None
				self.visuals['beams'].parent = None
			self.addOrbitalMarkers()
			if satplot.gl_plus:
				self.visuals['beams'] = InstancedConstellationBeams(dflt_col=(0,255,0),
																	parent=self.parent)
				self.visuals['beams'].setSource(self.data['num_sats'],
								self.data['coords'],
								self.data['curr_index'],
								self.data['beam_height'],
								self.data['beam_angle_deg'])
			else:
				self.visuals['beams'].setSource(self.data['num_sats'],
								self.data['coords'],
								self.data['curr_index'],
								self.data['beam_height'],
								self.data['beam_angle_deg'])
			self.first_draw = False

		if self.requires_recompute:
			if self.data['num_sats'] > 1:
				self.visuals['markers'].set_data(pos=self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3),
												size=self.opts['constellation_position_marker_size']['value'],
												face_color=colours.normaliseColour(self.opts['constellation_colour']['value']))
			else:
				self.visuals['markers'].set_data(pos=self.data['coords'][self.data['curr_index'],:].reshape(-1,3),
												size=self.opts['constellation_position_marker_size']['value'],
												face_color=colours.normaliseColour(self.opts['constellation_colour']['value']))
			self.visuals['beams'].recompute()
			self.requires_recompute = False

	def draw(self):
		if satplot.gl_plus:
			self.visuals['beams'] = InstancedConstellationBeams(dflt_col=(0,255,0),
													parent=self.parent)
		else:
			self.visuals['beams'] = ConstellationBeams(dflt_col=(0,255,0),
													parent=self.parent)
		self.first_draw = False

	def addOrbitalMarkers(self):
		self.visuals['markers'] = scene.visuals.Markers(parent=self.parent, scaling=True, antialias=0)
		if self.data['num_sats'] > 1:
			self.visuals['markers'].set_data(pos=self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3),
											edge_width=0,
											face_color=colours.normaliseColour(self.opts['constellation_colour']['value']),
											edge_color='white',
											size=self.opts['constellation_position_marker_size']['value'],
											symbol='o')
		else:
			self.visuals['markers'].set_data(pos=self.data['coords'][self.data['curr_index'],:].reshape(-1,3),
											edge_width=0,
											face_color=colours.normaliseColour(self.opts['constellation_colour']['value']),
											edge_color='white',
											size=self.opts['constellation_position_marker_size']['value'],
											symbol='o')

	def addBeams(self):
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)
		instance_colours = np.tile(colours.normaliseColour(self.opts['constellation_colour']['value']),(self.data['num_sats'],1))
		if self.data['num_sats'] > 1:
			instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)
		else:
			instance_positions = self.data['coords'][self.data['curr_index'],:].reshape(-1,3)
		
		if self.data['num_sats'] > 1:
			instance_transforms = []
			for ii in range(self.data['num_sats']):
				beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
				instance_transforms.append(Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix())
			instance_transforms = np.asarray(instance_transforms)
		else:
			beam_axis = -1 * pg.unitVector(self.data['coords'][self.data['curr_index'],:]).reshape(1,3)
			instance_transforms = Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix()
		
		vertices, faces = polyhedra.calcConeMesh((0,0,0),
												self.data['beam_height'],
												self.data['start_beam_vec'],
												self.data['beam_angle_deg'],
												theta_sample = 60)
		self.visuals['beams'] = vVisuals.Mesh(vertices,
													faces,
													instance_colors=instance_colours,
													instance_positions=instance_positions,
													instance_transforms=instance_transforms,
													parent=self.parent)
		alpha_filter = vFilters.Alpha(self.opts['beams_alpha']['value'])
		self.visuals['beams'].attach(alpha_filter)
	
	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_constellation'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setConstellationAssetVisibility}		
		self._dflt_opts['constellation_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'callback': self.setConstellationColour}
		self._dflt_opts['plot_constellation_position_markers'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setConstellationMarkersVisibility}
		self._dflt_opts['constellation_position_marker_size'] = {'value': 250,
										  		'type': 'number',
												'help': '',
												'callback': None}
		self._dflt_opts['plot_constellation_beams'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setConstellationBeamsVisibility}	

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass
	
	def setConstellationColour(self, new_colour):
		self.opts['constellation_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['marker'].set_data(face_color=colours.normaliseColour(new_colour))

	def setConstellationAssetVisibility(self, state):
		self.setConstellationMarkersVisibility(state)
		self.setConstellationBeamsVisibility(state)

	def setConstellationMarkersVisibility(self, state):
		self.visuals['markers'].visible = state

	def setConstellationBeamsVisibility(self, state):
		self.visuals['beams'].visible = state

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def calcBeamHeight(self, half_beam_angle, vector_length):
		phi = np.deg2rad(half_beam_angle)
		altitude = vector_length - c.R_EARTH
		beam_height = (np.cos(phi)**2 * (vector_length))
		return beam_height
	
class InstancedConstellationBeams(BaseAsset):
	def __init__(self, dflt_col=(0,255,0), canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False
		self.first_draw = True
		self._setDefaultOptions()
		self.opts['beams_colour']['value'] = dflt_col
		self.visuals['beams'] = None
		self.draw()

	def setSource(self, num_sats, coords, curr_index, beam_height, beam_angle_deg,):
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)
		self.data['num_sats'] = num_sats
		self.data['coords'] = coords
		self.data['curr_index'] = curr_index
		self.data['beam_height'] = beam_height
		self.data['beam_angle_deg'] = beam_angle_deg

	def draw(self):
		pass

	def compute(self):
		pass

	def recompute(self):
		if self.first_draw:
			if self.visuals['beams'] is not None:
				self.visuals['beams'].parent = None
			self.addInstancedBeams()
			self.first_draw = False
		
		if self.requires_recompute:
			if self.data['num_sats'] > 1:
				instance_transforms = []
				for ii in range(self.data['num_sats']):
					beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
					instance_transforms.append(np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix()))
				instance_transforms = np.asarray(instance_transforms)
				instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)
			else:
				beam_axis = -1 * pg.unitVector(self.data['coords'][self.data['curr_index'],:]).reshape(1,3)
				instance_transforms = np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix())
				instance_positions = self.data['coords'][self.data['curr_index'],:].reshape(-1,3)				

			self.visuals['beams'].instance_transforms = instance_transforms
			self.visuals['beams'].instance_positions = instance_positions
			self.requires_recompute = False

	def setFirstDraw(self, state):
		self.first_draw = state

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.requires_recompute = True
		self.recompute()

	def addInstancedBeams(self):
		
		instance_colours = np.tile(colours.normaliseColour(self.opts['beams_colour']['value']),(self.data['num_sats'],1))
		if self.data['num_sats'] > 1:
			instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)
		else:
			instance_positions = self.data['coords'][self.data['curr_index'],:].reshape(-1,3)
		
		if self.data['num_sats'] > 1:
			instance_transforms = []
			for ii in range(self.data['num_sats']):
				beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
				instance_transforms.append(Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix())
			instance_transforms = np.asarray(instance_transforms)
		else:
			beam_axis = -1 * pg.unitVector(self.data['coords'][self.data['curr_index'],:]).reshape(1,3)
			instance_transforms = Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix()
		
		vertices, faces = polyhedra.calcConeMesh((0,0,0),
												self.data['beam_height'],
												self.data['start_beam_vec'],
												self.data['beam_angle_deg'],
												theta_sample = 60)
		self.visuals['beams'] = vVisuals.InstancedMesh(vertices,
													faces,
													instance_colors=instance_colours,
													instance_positions=instance_positions,
													instance_transforms=instance_transforms,
													parent=self.parent)
		alpha_filter = vFilters.Alpha(self.opts['beams_alpha']['value'])
		self.visuals['beams'].attach(alpha_filter)		

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['beams_alpha'] = {'value': 0.5,
										'type': 'number',
										'help': '',
										'callback': self.setBeamsAlpha}
		self._dflt_opts['beams_colour'] = {'value': (0, 255, 0),
										'type': 'colour',
										'help': '',
										'callback': self.setBeamsColour}
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass

	def setBeamsColour(self, new_colour):
		self.opts['beams_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['beams'].set_data(face_color=colours.normaliseColour(new_colour))		

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def setVisibility(self, state):
		self.visuals['beams'].visible = False

class ConstellationBeams(BaseAsset):
	def __init__(self, dflt_col=(0,255,0), canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False
		self.first_draw = True
		self._setDefaultOptions()
		self.opts['beams_colour']['value'] = dflt_col
		self.visuals['beams'] = None
		self.draw()

	def setSource(self, num_sats, coords, curr_index, beam_height, beam_angle_deg,):
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)
		self.data['num_sats'] = num_sats
		self.data['coords'] = coords
		self.data['curr_index'] = curr_index
		self.data['beam_height'] = beam_height
		self.data['beam_angle_deg'] = beam_angle_deg

	def draw(self):
		pass

	def compute(self):
		pass

	def recompute(self):
		if self.first_draw:
			if self.visuals['beams'] is not None:
				for ii in range(len(self.visuals['beams'])):
					self.visuals['beams'][ii].parent = None
			self.addBeams()
			self.first_draw = False
		
		if self.requires_recompute:
			if self.data['num_sats'] > 1:
				instance_transforms = []
				instance_positions = []
				print(f"coords:{self.data['coords'].shape}")
				for ii in range(self.data['num_sats']):
					beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
					instance_transforms.append((Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix()))
				instance_transforms = np.asarray(instance_transforms)
				instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)
			else:
				beam_axis = -1 * pg.unitVector(self.data['coords'][self.data['curr_index'],:]).reshape(1,3)
				instance_transforms = (Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix())
				instance_positions = self.data['coords'][self.data['curr_index'],:].reshape(-1,3)				

			for ii in range(self.data['num_sats']):
				T = np.eye(4)
				print(f"T:{instance_transforms.shape}")
				print(f"O:{instance_positions.shape}")
				T[0:3,0:3] = instance_transforms[ii,:,:]
				T[3,0:3] = instance_positions[ii,:]
				transform = vTransforms.linear.MatrixTransform(T)
				self.visuals['beams'][ii].transform = transform
			
			self.requires_recompute = False

	def setFirstDraw(self, state):
		self.first_draw = state

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.requires_recompute = True
		self.recompute()

	def addBeams(self):
		self.visuals['beams'] = []
		instance_colours = np.tile(colours.normaliseColour(self.opts['beams_colour']['value']),(self.data['num_sats'],1))
		if self.data['num_sats'] > 1:
			instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)
		else:
			instance_positions = self.data['coords'][self.data['curr_index'],:].reshape(-1,3)
		
		if self.data['num_sats'] > 1:
			instance_transforms = []
			for ii in range(self.data['num_sats']):
				beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
				instance_transforms.append(Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix())
			instance_transforms = np.asarray(instance_transforms)
		else:
			beam_axis = -1 * pg.unitVector(self.data['coords'][self.data['curr_index'],:]).reshape(1,3)
			instance_transforms = Rotation.align_vectors(self.data['start_beam_vec'],
																beam_axis)[0].as_matrix()
		alpha_filter = vFilters.Alpha(self.opts['beams_alpha']['value'])			
		for ii in range(self.data['num_sats']):
			vertices, faces = polyhedra.calcConeMesh((0,0,0),
													self.data['beam_height'],
													self.data['start_beam_vec'],
													self.data['beam_angle_deg'],
													theta_sample = 60)
			self.visuals['beams'].append(vVisuals.Mesh(vertices,
													faces,
													color=instance_colours[ii,:],

													parent=self.parent))
			T = np.eye(4)
			T[0:3,0:3] = instance_transforms[ii]
			T[3,0:3] = instance_positions[ii]
			try:
				transform = vTransforms.linear.MatrixTransform(T)
			except:
				print(f"T:{T}")
			self.visuals['beams'][ii].transform = transform
			self.visuals['beams'][ii].attach(alpha_filter)		

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['beams_alpha'] = {'value': 0.5,
										'type': 'number',
										'help': '',
										'callback': self.setBeamsAlpha}
		self._dflt_opts['beams_colour'] = {'value': (0, 255, 0),
										'type': 'colour',
										'help': '',
										'callback': self.setBeamsColour}
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass

	def setBeamsColour(self, new_colour):
		self.opts['beams_colour']['value'] = colours.normaliseColour(new_colour)
		for ii in range(self.data['num_sats']):
			self.visuals['beams'][ii].set_data(color=colours.normaliseColour(new_colour))		

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def setVisibility(self, state):
		for ii in range(self.data['num_sats']):
			self.visuals['beams'][ii].visible = False