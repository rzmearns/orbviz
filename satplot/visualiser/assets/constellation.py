import numpy as np
from scipy.spatial.transform import Rotation
import scipy.special as sc

import vispy.scene as scene
import vispy.visuals.transforms as vTransforms
import vispy.scene.visuals as vVisuals
import vispy.visuals.filters as vFilters

import satplot
import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.geometry.primgeom as pg
import satplot.util.constants as c
import satplot.visualiser.assets.base as base
import satplot.visualiser.colours as colours
import spherapy.orbit as orbit


class Constellation(base.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Constellation'
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self.data['beam_angle_deg'] = 0
		self.data['num_sats'] = 0
		self.data['beam_height'] = 0
		
	def setSource(self, *args, **kwargs):
		# args[0] = [orbits]
		# args[1] = beam angle
		if type(args[0]) is not list:
			raise TypeError
		for el in args[0]:
			if type(el) is not orbit.Orbit:
				raise TypeError

		if hasattr(args[0][0],'pos'):
			pass
		else:
			raise ValueError('Constellation orbits have no position data')

		self.data['beam_angle_deg'] = args[1]
		self.data['num_sats'] = len(args[0])
		if self.data['num_sats'] > 1:
			self.data['coords'] = np.zeros((self.data['num_sats'],len(args[0][0].pos),3))
			for ii in range(self.data['num_sats']):
				self.data['coords'][ii,:,:] = args[0][ii].pos
			self.data['num_sats'] = self.data['num_sats']
			self.data['beam_height'] = self._calcBeamHeight(self.data['beam_angle_deg']/2,
												   			np.linalg.norm(args[0][0].pos[0,:]))
		else:
			self.data['coords'] = np.zeros((len(args[0][0].pos),3))
			self.data['coords'][:,:] = args[0][0].pos
			self.data['num_sats'] = 1
			self.data['beam_height'] = self._calcBeamHeight(self.data['beam_angle_deg']/2,
												   			np.linalg.norm(args[0][0].pos[0,:]))

		if self.assets['beams'] is not None:
			self.assets['beams'].setSource(self.data['num_sats'],
											self.data['coords'],
											self.data['curr_index'],
											self.data['beam_height'],
											self.data['beam_angle_deg'])
		self.data['strings'] = []
		for o in args[0]:
			if hasattr(o,'name'):
				self.data['strings'].append(o.name)
			else:
				self.data['strings'].append('')
		

	def _instantiateAssets(self):
		# self.assets['beams'] = None
		if satplot.gl_plus:
			self.assets['beams'] = InstancedConstellationBeams(name=f'{self.data["name"]}_beams', v_parent=self.data['v_parent'])
		else:
			self.assets['beams'] = ConstellationBeams(name=f'{self.data["name"]}_beams', v_parent=self.data['v_parent'])

	def _createVisuals(self):
		self.visuals['markers'] = scene.visuals.Markers(scaling=True,
														edge_color='white',
														symbol='o',
														antialias=0,
														parent=None)

	# Use AbstractAsset.updateIndex()

	def recompute(self):
		if self.first_draw:
			if self.visuals['markers'] is not None:
				# Must do this to clear old visuals before creating a new one
				# TODO: not clear if this is actually deleting or just removing the reference (memory leak?)
				self.visuals['markers'].parent = None
			self._createVisuals()
			self.attachToParentView()
			self.first_draw = False

		if self.requires_recompute:
			if self.data['num_sats'] > 1:
				self.visuals['markers'].set_data(pos=self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3),
												size=self.opts['constellation_position_marker_size']['value'],
												face_color=colours.normaliseColour((self.opts['constellation_colour']['value'][0]/2,
													self.opts['constellation_colour']['value'][1]/2,
													self.opts['constellation_colour']['value'][2]/2)))
			else:
				self.visuals['markers'].set_data(pos=self.data['coords'][self.data['curr_index'],:].reshape(-1,3),
												size=self.opts['constellation_position_marker_size']['value'],
												face_color=colours.normaliseColour((self.opts['constellation_colour']['value'][0]/2,
																					self.opts['constellation_colour']['value'][1]/2,
																					self.opts['constellation_colour']['value'][2]/2)))
			
			for asset in self.assets.values():
				asset.recompute()
			self.requires_recompute = False

	def getScreenMouseOverInfo(self):
		canvas_poss = []
		world_poss = []
		if self.data['num_sats'] > 1:
			for ii in range(self.data['num_sats']):
				curr_world_pos = (self.data['coords'][ii,self.data['curr_index']]).reshape(1,3)
				canvas_pos = self.visuals['markers'].get_transform('visual','canvas').map(curr_world_pos)
				canvas_pos /= canvas_pos[:,3:]
				canvas_poss.append((canvas_pos[0,0], canvas_pos[0,1]))
				world_poss.append(curr_world_pos)
		else:
			curr_world_pos = (self.data['coords'][self.data['curr_index']]).reshape(1,3)
			canvas_pos = self.visuals['marker'].get_transform('visual','canvas').map(curr_world_pos)
			canvas_pos /= canvas_pos[:,3:]
			canvas_poss.append((canvas_pos[0,0],canvas_pos[0,1]))
			world_poss.append(curr_world_pos)

		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = canvas_poss
		mo_info['world_pos'] = world_poss
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]*self.data['num_sats']
		return mo_info

	def mouseOver(self, index):
		self.assets['beams'].mouseOver(index)

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
												'callback': self.setConstellationMarkerSize}
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

	def setConstellationMarkerSize(self, value):
		self.opts['constellation_position_marker_size']['value'] = value
		self.recompute()

	def setConstellationMarkersVisibility(self, state):
		self.visuals['markers'].visible = state

	def setConstellationBeamsVisibility(self, state):
		self.assets['beams'].setVisibility(state)

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def _calcBeamHeight(self, half_beam_angle, vector_length):
		phi = np.deg2rad(half_beam_angle)
		altitude = vector_length - c.R_EARTH
		beam_height = (np.cos(phi)**2 * (vector_length))
		return beam_height
	
class InstancedConstellationBeams(base.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		# Can't create instanced mesh until source set
		# Add circles to dict first, so that parent gets set first, otherwise will be hidden by cones
		self.visuals['circles'] = None
		self.visuals['scircle'] = None
		self.visuals['beams'] = None
		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'ConstellationBeams'
		self.data['coords'] = None
		self.data['curr_index'] = 0
		self.data['num_sats'] = 0
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)
		self.data['c_conn'] = None

	def setSource(self, *args, **kwargs):
		# args[0] = num_sats
		# args[1] = coords
		# args[2] = curr_index
		# args[3] = beam_height
		# args[4] = beam_angle_deg
		
		if type(args[0]) is not int:
			raise TypeError(f"args[0]:num_sats is not an int -> {args[0]}")
		self.data['num_sats'] = args[0]

		if type(args[1]) is not np.ndarray:
			raise TypeError(f"args[1]:coords is not an ndarray -> {args[1]}")
		self.data['coords'] = args[1]

		if type(args[2]) is not int:
			raise TypeError(f"args[2]:curr_index is not an int -> {args[2]}")
		self.data['curr_index'] = args[2]

		if type(args[3]) is not float and type(args[3]) is not np.float64:
			print(type(args[3]))
			raise TypeError(f"args[3]:beam_height is not a float -> {args[3]}")
		self.data['beam_height'] = args[3]

		if type(args[4]) is not float and type(args[4]) is not np.float64:
			print(type(args[4]))
			raise TypeError(f"args[4]:beam_angle_deg is not a float -> {args[4]}")
		self.data['beam_angle_deg'] = args[4]

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
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
		
		generic_cone_points = polyhedra.calcConePoints((0,0,0),
													self.data['beam_height'],
													self.data['start_beam_vec'],
													self.data['beam_angle_deg'],
													axis_sample=2,
													theta_sample=60,
													sorted=False)
		self.data['generic_circle_points'] = generic_cone_points[(generic_cone_points != np.asarray((0,0,0))).all(axis=1),:]
		self.data['generic_circle_points'] = np.vstack((self.data['generic_circle_points'],self.data['generic_circle_points'][0,:]))
		circles = self._genBeamCircles(instance_transforms, instance_positions)
		self.visuals['circles'] = vVisuals.Line(circles,
										  		connect=self.data['c_conn'],
								 				color=colours.normaliseColour((self.opts['beams_colour']['value'][0]/2,
												self.opts['beams_colour']['value'][1]/2,
												self.opts['beams_colour']['value'][2]/2)),
												width=self.opts['circle_width']['value'],
												parent=None)
		self.data['num_generic_circle_points'] = len(self.data['generic_circle_points'])
		self.data['s_c_conn'] = np.array((0,0)).reshape(-1,2)
		self.visuals['scircle'] = vVisuals.Line(circles,
												connect=self.data['s_c_conn'],
								 				color=colours.normaliseColour((self.opts['beams_colour']['value'][0]/2,
												self.opts['beams_colour']['value'][1]/2,
												self.opts['beams_colour']['value'][2]/2)),
												width=5.0,
												parent=None)	
		self.visuals['beams'] = vVisuals.InstancedMesh(vertices,
													faces,
													instance_colors=instance_colours,
													instance_positions=instance_positions,
													instance_transforms=instance_transforms,
													parent=None)
		alpha_filter = vFilters.Alpha(self.opts['beams_alpha']['value'])
		self.visuals['beams'].attach(alpha_filter)

	# Use AbstractAsset.updateIndex()

	def recompute(self):
		if self.first_draw:
			if self.visuals['beams'] is not None:
				self.visuals['beams'].parent = None
				self.visuals['circles'].parent = None
				self.visuals['scircle'].parent = None
			self._createVisuals()
			self.attachToParentView()
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
			circles = self._genBeamCircles(instance_transforms,instance_positions)
			self.visuals['circles'].set_data(circles)
			self.data['s_c_conn'] = np.array((0,0)).reshape(-1,2)
			self.visuals['scircle'].set_data(pos=circles, connect=self.data['s_c_conn'])
			self.requires_recompute = False

	def mouseOver(self, index):
		self.data['s_c_conn'] = np.array([np.arange(self.data['num_generic_circle_points']-1),
											np.arange(1,self.data['num_generic_circle_points'])]).T + index * self.data['num_generic_circle_points']
		self.visuals['scircle'].set_data(connect=self.data['s_c_conn'])

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['beams_alpha'] = {'value': 0.5,
										'type': 'float',
										'help': '',
										'callback': self.setBeamsAlpha}
		self._dflt_opts['beams_colour'] = {'value': (0, 255, 0),
										'type': 'colour',
										'help': '',
										'callback': self.setBeamsColour}
		self._dflt_opts['circle_width'] = {'value': 0.5,
										'type': 'float',
										'help': '',
										'callback': self.setCirclesWidth}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setBeamsColour(self, new_colour):
		self.opts['beams_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['beams'].set_data(face_color=colours.normaliseColour(new_colour))		

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def setCirclesWidth(self, width):
		self.opts['circle_width']['value'] = width
		self._updateLineVisualsOptions()

	def _updateLineVisualsOptions(self):
		self.visuals['circles'].set_data(width=self.opts['circle_width']['value'])

	def setVisibility(self, state):
		self.visuals['beams'].visible = state

	def _genBeamCircles(self, instance_transforms, instance_positions):
		total_len = 0
		gen_conn = False
		circles = None
		if self.data['c_conn'] is None:
			gen_conn = True
		
		for ii in range(len(instance_transforms)):
			circle = np.dot(instance_transforms[ii],self.data['generic_circle_points'].T).T + instance_positions[ii]	
			poly_len = len(circle)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			if gen_conn:
				if self.data['c_conn'] is not None:
					self.data['c_conn'] = np.vstack((self.data['c_conn'],new_conn))
				else:
					self.data['c_conn'] = new_conn
			total_len += poly_len
			if circles is not None:
				circles = np.vstack((circles, circle))
			else:
				circles = circle

		return circles

class ConstellationBeams(base.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		# Can't create instanced mesh until source set
		self.visuals['beams'] = None
		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'ConstellationBeams'
		self.data['coords'] = None
		self.data['curr_index'] = 0
		self.data['num_sats'] = 0
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)		

	def setSource(self, *args, **kwargs):
		# args[0] = num_sats
		# args[1] = coords
		# args[2] = curr_index
		# args[3] = beam_height
		# args[4] = beam_angle_deg
		
		if type(args[0]) is not int:
			raise TypeError(f"args[0]:num_sats is not an int -> {args[0]}")
		self.data['num_sats'] = args[0]

		if type(args[1]) is not np.ndarray:
			raise TypeError(f"args[1]:coords is not an ndarray -> {args[1]}")
		self.data['coords'] = args[1]

		if type(args[2]) is not int:
			raise TypeError(f"args[2]:curr_index is not an int -> {args[2]}")
		self.data['curr_index'] = args[2]

		if type(args[3]) is not float and type(args[3]) is not np.float64:
			print(type(args[3]))
			raise TypeError(f"args[3]:beam_height is not a float -> {args[3]}")
		self.data['beam_height'] = args[3]

		if type(args[4]) is not float and type(args[4]) is not np.float64:
			print(type(args[4]))
			raise TypeError(f"args[4]:beam_angle_deg is not a float -> {args[4]}")
		self.data['beam_angle_deg'] = args[4]

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
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
													parent=None))
			T = np.eye(4)
			T[0:3,0:3] = instance_transforms[ii]
			T[3,0:3] = instance_positions[ii]
			try:
				transform = vTransforms.linear.MatrixTransform(T)
			except:
				print(f"T:{T}")
			self.visuals['beams'][ii].transform = transform
			self.visuals['beams'][ii].attach(alpha_filter)

	# Use AbstractAsset.updateIndex()

	def recompute(self):
		if self.first_draw:
			if self.visuals['beams'] is not None:
				for ii in range(len(self.visuals['beams'])):
					self.visuals['beams'][ii].parent = None
			self._createVisuals()
			self.attachToParentView()
			self.first_draw = False
		
		if self.requires_recompute:
			if self.data['num_sats'] > 1:
				instance_transforms = []
				instance_positions = []
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
				T[0:3,0:3] = instance_transforms[ii,:,:]
				T[3,0:3] = instance_positions[ii,:]
				transform = vTransforms.linear.MatrixTransform(T)
				self.visuals['beams'][ii].transform = transform
			
			self.requires_recompute = False


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

	#----- OPTIONS CALLBACKS -----#	
	def setBeamsColour(self, new_colour):
		self.opts['beams_colour']['value'] = colours.normaliseColour(new_colour)
		for ii in range(self.data['num_sats']):
			self.visuals['beams'][ii].set_data(color=colours.normaliseColour(new_colour))		

	def setBeamsAlpha(self, alpha):
		raise NotImplementedError
	
	def setVisibility(self, state):
		for ii in range(self.data['num_sats']):
			self.visuals['beams'][ii].visible = False