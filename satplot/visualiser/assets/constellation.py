import logging

import typing
from typing import Any
from typing_extensions import Self

import numpy as np
import numpy.typing as nptyping
from scipy.spatial.transform import Rotation
import spherapy.orbit as orbit

import vispy.color.color_array as vcolor_array
import vispy.scene as scene
import vispy.scene.visuals as vVisuals
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.filters as vFilters
import vispy.visuals.transforms as vTransforms

import satplot
import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.geometry.primgeom as pg
import satplot.util.constants as c
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class Constellation(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Constellation'
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self.data['beam_angle_deg'] = 0
		self.data['num_sats'] = 0
		self.data['beam_height'] = 0
		
	def setSource(self, *args, **kwargs) -> None:
		# args[0] = [orbits]
		# args[1] = beam angle

		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]
		beam_angle = args[1]

		if type(sats_dict) is not dict:
			logger.error('args[0] of Constellation.setSource() should be a dictionary of satellites ')
			raise TypeError
		for k, v in sats_dict.items():
			if type(v) is not orbit.Orbit:
				logger.error("setSource() of %s requires an %s as value of dict from args[0], not: %s", self, orbit.Orbit, type(first_sat_orbit))
				raise TypeError

		if hasattr(first_sat_orbit,'pos'):
			pass
		else:
			console.sendErr('Orbit has no position data')
			logger.warning('Constellation orbit has no position data')
			raise ValueError('Constellation orbits have no position data')


		self.data['beam_angle_deg'] = beam_angle
		self.data['num_sats'] = len(sats_dict.values())
		self.data['coords'] = np.zeros((self.data['num_sats'],len(list(sats_dict.values())[0].pos),3))
		for ii in range(self.data['num_sats']):
			self.data['coords'][ii,:,:] = list(sats_dict.values())[ii].pos
		self.data['beam_height'] = self._calcBeamHeight(self.data['beam_angle_deg']/2,
												   			np.linalg.norm(list(sats_dict.values())[0].pos[0,:]))

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


	def _instantiateAssets(self) -> None:
		# self.assets['beams'] = None
		if satplot.gl_plus:
			self.assets['beams'] = InstancedConstellationBeams(name=f'{self.data["name"]}_beams', v_parent=self.data['v_parent'])
		else:
			self.assets['beams'] = ConstellationBeams(name=f'{self.data["name"]}_beams', v_parent=self.data['v_parent'])

	def _createVisuals(self) -> None:
		self.visuals['markers'] = scene.visuals.Markers(scaling=True,
														edge_color='white',
														symbol='o',
														antialias=0,
														parent=None)

	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._detachFromParentView()
			# if self.visuals['markers'] is not None:
			# 	# Must do this to clear old visuals before creating a new one
			# 	# TODO: not clear if this is actually deleting or just removing the reference (memory leak?)
			# 	self.visuals['markers'].parent = None
			self._attachToParentView()
			# self._createVisuals()
			# self._attachToParentView()
			# self.first_draw = False
			self._clearFirstDrawFlag()

		if self.isStale():
			self._updateMarkers()
			# recomputeRedraw child assets
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str,Any]:
		canvas_poss = []
		world_poss = []
		for ii in range(self.data['num_sats']):
			curr_world_pos = (self.data['coords'][ii,self.data['curr_index']]).reshape(1,3)
			canvas_pos = self.visuals['markers'].get_transform('visual','canvas').map(curr_world_pos)
			canvas_pos /= canvas_pos[:,3:]
			canvas_poss.append((canvas_pos[0,0], canvas_pos[0,1]))
			world_poss.append(curr_world_pos)

		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = canvas_poss
		mo_info['world_pos'] = world_poss
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]*self.data['num_sats']
		return mo_info
	def mouseOver(self, index:int) -> Self:
		self.assets['beams'].mouseOver(index)
		return self

	def restoreMouseOver(self) -> None:
		return self.assets['beams'].restoreMouseOver()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['plot_constellation'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setConstellationAssetVisibility,
											'widget_data': None}
		self._dflt_opts['constellation_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setConstellationColour,
											'widget_data': None}
		self._dflt_opts['plot_constellation_position_markers'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setConstellationMarkersVisibility,
											'widget_data': None}
		self._dflt_opts['constellation_position_marker_size'] = {'value': 250,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setConstellationMarkerSize,
											'widget_data': None}
		self._dflt_opts['constellation_position_marker_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setConstellationMarkerColour,
											'widget_data': None}
		self._dflt_opts['plot_constellation_beams'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setConstellationBeamsVisibility,
											'widget_data': None}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self) -> None:
		pass
	
	def setConstellationColour(self, new_colour:tuple[int,int,int]) -> None:
		self.setConstellationMarkerColour(new_colour)
		self.assets['beams'].setBeamsColour(new_colour)

	def setConstellationMarkerColour(self, new_colour:tuple[int,int,int]) -> None:
		self.opts['constellation_colour']['value'] = new_colour
		self._updateMarkers()

	def setConstellationAssetVisibility(self, state:bool) -> None:
		self.setConstellationMarkersVisibility(state)
		self.setConstellationBeamsVisibility(state)

	def setConstellationMarkerSize(self, value:int) -> None:
		self.opts['constellation_position_marker_size']['value'] = value
		self._updateMarkers()

	def setConstellationMarkersVisibility(self, state:bool) -> None:
		self.opts['plot_constellation_position_markers']['value'] = state
		self.visuals['markers'].visible = self.opts['plot_constellation_position_markers']['value']

	def setConstellationBeamsVisibility(self, state:bool) -> None:
		self.opts['plot_constellation_beams']['value'] = state
		self.assets['beams'].setVisibility(self.opts['plot_constellation_beams']['value'])

	def _updateMarkers(self):
		darkness_factor = 1
		self.visuals['markers'].set_data(pos=self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3),
										size=self.opts['constellation_position_marker_size']['value'],
										face_color=colours.normaliseColour((self.opts['constellation_colour']['value'][0]/darkness_factor,
											self.opts['constellation_colour']['value'][1]/darkness_factor,
											self.opts['constellation_colour']['value'][2]/darkness_factor)))

	def _calcBeamHeight(self, half_beam_angle:float, vector_length:float|np.floating[Any]) -> float:
		# calculates beam height such that edge of cone is tangent to the earth where it falls.
		theta = np.deg2rad(half_beam_angle)
		gamma = np.arcsin(vector_length*np.sin(theta)/c.R_EARTH)
		# gamma must be in 2nd quadrant
		gamma = np.pi - gamma
		beta = np.pi - theta - gamma
		cone_range = c.R_EARTH * np.sin(beta)/np.sin(theta)
		beam_height = cone_range * np.sin(np.pi/2-theta)
		return beam_height
	
class InstancedConstellationBeams(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		# Can't create instanced mesh until source set, -> _createVisuals must be called after first time source set
		self._first_creation = True
		# Add circles to dict first, so that parent gets set first, otherwise will be hidden by cones
		self.visuals['circles'] = None
		self.visuals['scircle'] = None
		self.visuals['beams'] = None
		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'ConstellationBeams'
		self.data['coords'] = None
		self.data['curr_index'] = 0
		self.data['num_sats'] = 0
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)
		self.data['c_conn'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = num_sats
		# args[1] = coords
		# args[2] = curr_index
		# args[3] = beam_height
		# args[4] = beam_angle_deg
		
		if type(args[0]) is not int:
			logger.error("InstancedConstellationBeams.setSource() args[0]:num_sats is not an int -> %s", args[0])
			raise TypeError(f"args[0]:num_sats is not an int -> {args[0]}")

		if self.data['num_sats'] != args[0]:
			require_beam_reinstantiation = True
		else:
			require_beam_reinstantiation = False
		self.data['num_sats'] = args[0]

		if type(args[1]) is not np.ndarray:
			logger.error("InstancedConstellationBeams.setSource() args[1]:coords is not an ndarray -> %s", args[1])
			raise TypeError(f"args[1]:coords is not an ndarray -> {args[1]}")
		self.data['coords'] = args[1]

		if type(args[2]) is not int:
			logger.error("InstancedConstellationBeams.setSource() args[2]:curr_index is not an int -> %s", args[2])
			raise TypeError(f"args[2]:curr_index is not an int -> {args[2]}")
		self.data['curr_index'] = args[2]

		if type(args[3]) is not float and type(args[3]) is not np.float64:
			logger.error("InstancedConstellationBeams.setSource() args[3]:beam_height is not a float -> %s", args[3])
			raise TypeError(f"args[3]:beam_height is not a float -> {args[3]}")
		self.data['beam_height'] = args[3]

		if args[4] >= 180 or args[4] <= 0:
			logger.error("InstancedConstellationBeams.setSource() args[4]:beam_angle_deg must be be 0<angle<180 -> %s", args[4])
			raise TypeError(f'args[4]: beam_angle_deg must be be 0<angle<180 -> {args[4]}')

		if type(args[4]) is not float and type(args[4]) is not np.float64:
			self.data['beam_angle_deg'] = float(args[4])
		else:
			self.data['beam_angle_deg'] = args[4]

		# # Create instanced mesh
		if self._first_creation or require_beam_reinstantiation:
			self._detachFromParentView()
			self._createVisuals()
			self._first_creation = False

	def _instantiateAssets(self) -> None:
		pass

	def _destroyVisuals(self) -> None:
		for name in self.visuals.values():
			del self.visuals[name]
			self.visuals[name] = None

	def _createVisuals(self) -> None:
		instance_colours = np.tile(colours.normaliseColour(self.opts['beams_colour']['value']),(self.data['num_sats'],1))
		instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)

		instance_transforms = np.zeros((self.data['num_sats'],3,3))
		for ii in range(self.data['num_sats']):
			beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
			instance_transforms[ii,:,:] = np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'],beam_axis)[0].as_matrix())
		
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
		# scircle is selected beam circle
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
		self.data['beams_alpha_filter'] = vFilters.Alpha(self.opts['beams_alpha']['value'])
		self.visuals['beams'].attach(self.data['beams_alpha_filter'])


	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._detachFromParentView()
			self._attachToParentView()
			# if self.visuals['beams'] is not None:
			# 	self.visuals['beams'].parent = None
			# 	self.visuals['circles'].parent = None
			# 	self.visuals['scircle'].parent = None
			# self._createVisuals()
			# self.attachToParentView()
			self._clearFirstDrawFlag()
		
		if self.isStale():
			instance_transforms = np.zeros((self.data['num_sats'],3,3))
			for ii in range(self.data['num_sats']):
				beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
				instance_transforms[ii,:,:] = np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'],beam_axis)[0].as_matrix())
			instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)

			self.visuals['beams'].instance_transforms = instance_transforms
			self.visuals['beams'].instance_positions = instance_positions
			circles = self._genBeamCircles(instance_transforms,instance_positions)
			self.visuals['circles'].set_data(circles)
			self.data['s_c_conn'] = np.array((0,0)).reshape(-1,2)
			self.visuals['scircle'].set_data(pos=circles, connect=self.data['s_c_conn'])
			self._recomputeRedrawChildren()
			self._clearStaleFlag()


	def mouseOver(self, index:int) -> Self:
		self.data['s_c_conn'] = np.array([np.arange(self.data['num_generic_circle_points']-1),
											np.arange(1,self.data['num_generic_circle_points'])]).T + index * self.data['num_generic_circle_points']
		self.visuals['scircle'].set_data(connect=self.data['s_c_conn'])
		return self


	def restoreMouseOver(self) -> None:
		self.data['s_c_conn'] = np.array((0,0)).reshape(-1,2)
		self.visuals['scircle'].set_data(connect=self.data['s_c_conn'])
		return

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['beams_alpha'] = {'value': 0.5,
										'type': 'fraction',
										'help': '',
										'static': True,
										'callback': self.setBeamsAlpha,
											'widget_data': None}
		self._dflt_opts['beams_colour'] = {'value': (0, 255, 0),
										'type': 'colour',
										'help': '',
										'static': True,
										'callback': self.setBeamsColour,
											'widget_data': None}
		self._dflt_opts['circle_width'] = {'value': 0.5,
										'type': 'float',
										'help': '',
										'static': True,
										'callback': self.setCirclesWidth,
											'widget_data': None}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setBeamsColour(self, new_colour:tuple[int,int,int]) -> None:
		logger.debug("Changing instanced beams colour %s -> %s", self.opts['beams_colour']['value'], new_colour)
		self.opts['beams_colour']['value'] = new_colour
		if self.data['num_sats'] > 0:
			new_cols_array = vcolor_array.ColorArray([colours.normaliseColour(self.opts['beams_colour']['value'])]*self.data['num_sats'])
			self.visuals['beams'].instance_colors = new_cols_array
			self._updateLineVisualsOptions()

	def setBeamsAlpha(self, alpha:float) -> None:
		logger.debug("Changing instanced beams alpha %s -> %s", self.opts['beams_alpha']['value'], alpha)
		self.opts['beams_alpha']['value'] = alpha
		self.data['beams_alpha_filter'].alpha = alpha
	
	def setCirclesWidth(self, width:float) -> None:
		self.opts['circle_width']['value'] = width
		self._updateLineVisualsOptions()

	def _updateLineVisualsOptions(self) -> None:
		if self.visuals['circles'] is not None:
			self.visuals['circles'].set_data(width=self.opts['circle_width']['value'],
											 color=colours.normaliseColour(self.opts['beams_colour']['value']))

	def _genBeamCircles(self, instance_transforms:list[nptyping.NDArray]|nptyping.NDArray,
							 instance_positions:list[nptyping.NDArray]|nptyping.NDArray) -> nptyping.NDArray | None:
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

class ConstellationBeams(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		self.visuals['beams'] = None
		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'ConstellationBeams'
		self.data['coords'] = None
		self.data['curr_index'] = 0
		self.data['num_sats'] = 0
		self.data['start_beam_vec'] = np.array((0,0,1)).reshape(1,3)		

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = num_sats
		# args[1] = coords
		# args[2] = curr_index
		# args[3] = beam_height
		# args[4] = beam_angle_deg
		
		if type(args[0]) is not int:
			raise TypeError("args[0]:num_sats is not an int -> %s", args[0])
		self.data['num_sats'] = args[0]

		if type(args[1]) is not np.ndarray:
			raise TypeError("args[1]:coords is not an ndarray -> %s", args[1])
		self.data['coords'] = args[1]

		if type(args[2]) is not int:
			raise TypeError("args[2]:curr_index is not an int -> %s", args[2])
		self.data['curr_index'] = args[2]

		if type(args[3]) is not float and type(args[3]) is not np.float64:
			raise TypeError("args[3]:beam_height is not a float -> %s", args[3])
		self.data['beam_height'] = args[3]

		if type(args[4]) is not float and type(args[4]) is not np.float64:
			raise TypeError("args[4]:beam_angle_deg is not a float -> %s", args[4])
		self.data['beam_angle_deg'] = args[4]

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['beams'] = []
		instance_colours = np.tile(colours.normaliseColour(self.opts['beams_colour']['value']),(self.data['num_sats'],1))
		instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)

		instance_transforms = np.zeros((self.data['num_sats'],3,3))
		for ii in range(self.data['num_sats']):
			beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
			instance_transforms[ii,:,:] = np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'], beam_axis)[0].as_matrix())

		self.data['beams_alpha_filter'] = vFilters.Alpha(self.opts['beams_alpha']['value'])

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
			transform = vTransforms.linear.MatrixTransform(T)
			self.visuals['beams'][ii].transform = transform
			self.visuals['beams'][ii].attach(self.data['beams_alpha_filter'])


	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._detachFromParentView()
			self._attachToParentView()
			self._clearStaleFlag()
		
		if self.isStale():

			instance_transforms = np.zeros((self.data['num_sats'],3,3))
			for ii in range(self.data['num_sats']):
				beam_axis = -1 * pg.unitVector(self.data['coords'][ii,self.data['curr_index'],:]).reshape(1,3)
				instance_transforms[ii,:,:] = np.linalg.inv(Rotation.align_vectors(self.data['start_beam_vec'], beam_axis)[0].as_matrix())
			instance_positions = self.data['coords'][:,self.data['curr_index'],:].reshape(-1,3)

			for ii in range(self.data['num_sats']):
				T = np.eye(4)
				T[0:3,0:3] = instance_transforms[ii,:,:]
				T[3,0:3] = instance_positions[ii,:]
				transform = vTransforms.linear.MatrixTransform(T)
				self.visuals['beams'][ii].transform = transform
			
			self._recomputeRedrawChildren()
			self._clearStaleFlag()


	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['beams_alpha'] = {'value': 0.5,
										'type': 'fraction',
										'help': '',
										'static': True,
										'callback': self.setBeamsAlpha,
											'widget_data': None}
		self._dflt_opts['beams_colour'] = {'value': (0, 255, 0),
										'type': 'colour',
										'help': '',
										'static': True,
										'callback': self.setBeamsColour,
											'widget_data': None}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setBeamsColour(self, new_colour:tuple[float,float,float]) -> None:
		logger.debug("Changing beams colour %s -> %s", self.opts['beams_colour']['value'], new_colour)
		self.opts['beams_colour']['value'] = new_colour
		if self.data['num_sats'] > 0:
			for ii in range(self.data['num_sats']):
				n_faces = self.visuals['beams']._meshdata.n_faces
				n_verts = self.visuals['beams']._meshdata.n_vertices
				self.visuals['beams']._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
				self.visuals['beams']._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
			self.visuals['beams'].mesh_data_changed()
		# self.visuals['circles'].set_data(color=colours.normaliseColour(new_colour))

	def setBeamsAlpha(self, alpha:float) -> None:
		logger.debug("Changing beams alpha %s -> %s", self.opts['beams_alpha']['value'], alpha)
		self.opts['beams_alpha']['value'] = alpha
		self.data['beams_alpha_filter'].alpha = alpha
