import numpy as np
import logging
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Patch

import satplot.visualiser.utils as vis_utils
import satplot.visualiser.Assets as assets
import satplot.visualiser.basevisualiser as basevisualiser

logger = logging.getLogger(__name__)

#TODO: need to check garbage collection of actors
# ipython keeps its own references so can't check in there
# TODO: add earth patch asset


class SpacecraftVisualiser(basevisualiser.Base):
	"""Visualiser for an orbit created within satplot
	
	"""
	def __init__(self, subplot=False, subplot_args=[None, 111]):
		"""Creates visualiser instance
		
		Creates a new matplotlib figure and 3d axes within it.
		"""
		if not subplot:
			self.label_str = 'spacecraft'
			# If want to draw on same figure, create_figure may need to be extended to accept/ignore a 'new' keyword
			vis_utils.create_figure(self.label_str, 'Spacecraft', three_dim=True)
			
		else:
			self.label_str = subplot_args[0]
			vis_utils.create_figure(self.label_str, 'Spacecraft', three_dim=True, subplot_pos=subplot_args[1])

		self.subplot_pos = subplot_args[1]
		vis_utils.square_axes(self.label_str, subplot_pos=self.subplot_pos)
		self.set_dflt_options()
		self.fig = vis_utils.find_figure(self.label_str)
		self.ax = vis_utils.find_axes(self.label_str, self.subplot_pos)
		self.gizmo = assets.Gizmo(self, self.ax, 0.5)
		self.gizmo.opts['line_weight'] = 5
		self.sun = assets.Sun(self, self.ax, 2)
		self.index = 0
		self.actors = {}
		self.max_dim = 0

	def setDefaultOptions(self):
		""" Sets the default options for the orbit_visualiser
		"""
		self._dflt_opts = {}
		
		# TODO: Add flags to options for drawing gizmo and sun
		self._dflt_opts['color_map'] = 'numbered'
		self._dflt_opts['norm_color_map'] = 'black'
		self._dflt_opts['draw_sun'] = False
		self._dflt_opts['draw_gizmo'] = True
		self._dflt_opts['norm_scale'] = 0.5
		self._dflt_opts['wireframe'] = False
		self._dflt_opts['x_units'] = 'x [mm]'
		self._dflt_opts['y_units'] = 'y [mm]'
		self._dflt_opts['z_units'] = 'z [mm]'
		self._dflt_opts['legend'] = True

		self.opts = self._dflt_opts.copy()
		self._create_opt_help()

	def setSource(self, source):
		""" Sets source for spacecraft visualiser
		
		Parameters
		----------
		source : {Spacecraft}
		"""
		# Set source to orbit class
		self.source = source
		min_dim = min(self.source.axes_limits[0], self.source.axes_limits[2], self.source.axes_limits[4])
		max_dim = max(self.source.axes_limits[1], self.source.axes_limits[3], self.source.axes_limits[5])
		greatest_dim = max(abs(min_dim), abs(max_dim))
		dim = 1.25 * (max_dim - min_dim)
		dim_center = (dim / 2) + min_dim
		vis_utils.set_square_limits(self.ax, -1.25 * greatest_dim, 1.25 * greatest_dim)
		self.opts['x_units'] = f'[{_getSCScale(self.source.scale)}]'
		self.opts['y_units'] = f'[{_getSCScale(self.source.scale)}]'
		self.opts['z_units'] = f'[{_getSCScale(self.source.scale)}]'
		# self.sun = self.source.orbit.sun / np.linalg.norm(self.source.orbit.sun, axis=1)[:, None]

	def draw(self):
		"""Draw spacecraft visualisation representing current spacecraft source.
		
		Will draw:
			Spacecraft nodes - not yet implemented
			Gizmo
			Sun Vec
		"""
		if 'gizmo' in self.actors.keys():
			self.actors['gizmo'].remove()
			del self.actors['gizmo']

		if self.opts['draw_gizmo']:
			self.actors['gizmo'] = self.gizmo.draw()

		if 'sun' in self.actors.keys():
			self.actors['sun'].remove()
			del self.actors['sun']
		
		if self.opts['draw_sun']:
			self.actors['sun'] = self.sun.draw()

		if 'faces' in self.actors.keys():
			for face in self.actors['faces']:
				face.remove()
			del self.actors['faces']
		if 'normals' in self.actors.keys():
			for normal in self.actors['normals']:
				normal.remove()			
			del self.actors['normals']
		if 'wf' in self.actors.keys():
			for wf in self.actors['wf']:
				wf.remove()			
			del self.actors['wf']

		self.ax.set_xlabel(self.opts['x_units'])
		self.ax.set_ylabel(self.opts['y_units'])
		self.ax.set_zlabel(self.opts['z_units'])

		self.draw_nodes()


		# resizing axes to include max dimension in all nodes
		# vis_utils.square_axes('spacecraft', max_dim=self.max_dim)

		# vis_utils.set_square_limits(self.ax, -1.5, 1.5)

	def _createOptionHelp(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['color_map'] = "Colour map to be used for displaying spacecraft nodes. dflt: '{opt}'. fmt: 'innate', 'numbered', 'visibility', 'temp'".format(opt=self._dflt_opts['color_map'])
				self.opts_help['norm_color_map'] = "Colour map to be used for displaying spacecraft face normals. dflt: '{opt}'. fmt: 'innate', 'numbered', 'visibility', 'temp'".format(opt=self._dflt_opts['norm_color_map'])
				self.opts_help['draw_sun'] = "Draw the sun patch?. dflt: '{opt}'. fmt: 'True', 'False'".format(opt=self._dflt_opts['draw_sun'])
				self.opts_help['draw_gizmo'] = "Draw the sun patch?. dflt: '{opt}'. fmt: 'True', 'False'".format(opt=self._dflt_opts['draw_gizmo'])
				self.opts_help['norm_scale'] = "Length of the face norm vectors. dflt: '{opt}'. fmt: float".format(opt=self._dflt_opts['norm_scale'])
				self.opts_help['wireframe'] = "Draw faces as wireframes. dflt: '{opt}'. fmt: float".format(opt=self._dflt_opts['wireframe'])
				self.opts_help['x_units'] = "Unit to be displayed on x axis. dflt: '{opt}'.".format(opt=self._dflt_opts['x_units'])
				self.opts_help['y_units'] = "Unit to be displayed on y axis. dflt: '{opt}'.".format(opt=self._dflt_opts['y_units'])
				self.opts_help['z_units'] = "Unit to be displayed on z axis. dflt: '{opt}'.".format(opt=self._dflt_opts['z_units'])
				self.opts_help['legend'] = "Display legend. dflt: '{opt}'.".format(opt=self._dflt_opts['legend'])				
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.set_dflt_options()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))

	def drawNodes(self, normals=False):
		# Set colour to use when drawing nodes
		if self.opts['color_map'] == 'visibility':
			pass
		self.actors['faces'] = []
		self.actors['normals'] = []
		self.actors['wf'] = []
		prev_ii = -1
		node_labels = [node.description for node in self.source.node_list]
		node_colours = [''] * len(node_labels)
		node_edge_colours = [''] * len(node_labels)
		for ii, bnode in enumerate(self.source.node_list):
			if len(bnode.face_list) > 0:
				for jj, fnode in enumerate(bnode.face_list):
					# keep track of maximum dimension for scaling axes
					max_dim = fnode.verts.max()
					if max_dim > self.max_dim:
						self.max_dim = max_dim

					# Draw normals
					if normals:
						norm_xs = [fnode.cent[0], fnode.cent[0] + self.opts['norm_scale'] * fnode.norm[0]]
						norm_ys = [fnode.cent[1], fnode.cent[1] + self.opts['norm_scale'] * fnode.norm[1]]
						norm_zs = [fnode.cent[2], fnode.cent[2] + self.opts['norm_scale'] * fnode.norm[2]]
						if self.opts['norm_color_map'] == 'black':
							# print("normal {}.{}".format(ii,jj))
							n = vis_utils.Arrow3D(norm_xs, norm_ys, norm_zs, 
													mutation_scale=10,
													lw=2,
													arrowstyle='-|>',
													color='k',
													zorder=100)
						elif self.opts['norm_color_map'] == 'numbered':
							n = vis_utils.Arrow3D(norm_xs, norm_ys, norm_zs, 
													mutation_scale=10,
													lw=2,
													arrowstyle='-|>',
													color=_getNumberedColour(ii),
													zorder=100)
						else:
							pass

						self.actors['normals'].append(n)
						self.ax.add_artist(n)

					# Draw faces
					if not self.opts['wireframe']:
						f = Poly3DCollection([fnode.verts])
						# print("face {}.{}".format(ii,jj))
						if self.opts['color_map'] == 'innate':
							pass
							# TODO:
						elif self.opts['color_map'] == 'numbered':
							if prev_ii != ii:
								node_colours[ii] = np.hstack((_getNumberedColour(ii), 0.4))
								node_edge_colours[ii] = np.asarray([[0, 0, 0, 1]])
								prev_ii = ii
							f.set_color(np.hstack((_getNumberedColour(ii), 0.4)))
							f._edgecolor3d = np.asarray([[0, 0, 0, 1]])
						elif self.opts['color_map'] == 'visibility':						
							pass
							# TODO:
						elif self.opts['color_map'] == 'temp':
							pass
							# TODO:
						else:
							pass
						self.actors['faces'].append(f)
						self.ax.add_collection3d(f)
			
		if self.opts['wireframe']:
			polyhedra = [node.verts for node in self.source.node_list]

			self.actors['wf'].append(dgjk.plot_poly_list(self.ax, polyhedra))

		if self.opts['legend']:
			custom_patches = []
			for ii in range(len(node_labels)):
				custom_patches.append(Patch(facecolor=node_colours[ii], edgecolor=node_edge_colours[ii], label=node_labels[ii]))

			self.ax.legend(handles=custom_patches, loc='upper left', bbox_to_anchor=(-0.15, 1))

		self.ax.view_init(elev=13, azim=-30)
					
		# 	if sc.any_co_node(ii)[0]:
		# 		faceVert =  sc.node_list[ii].explode_along_normal(0.01)
		# 	else:
		# 		faceVert =  sc.node_list[ii].face_verts
		# 	side.append(Poly3DCollection([faceVert]))
			
		# 	#Apply node colour
		# 	if col=='inate':
		# 		side[ii].set_color(sc.node_list[ii].colour)
		# 	elif col=='numbered':
		# 		_col=[node_color(ii)]
		# 		side[ii]._facecolors3d=np.asarray(_col)
		# 		_label="%d"%(ii)
		# 		ax.scatter(sc.node_list[ii].cen_vec[0],sc.node_list[ii].cen_vec[1],sc.node_list[ii].cen_vec[2],"%d"%(ii),zorder=0,color=_col,edgecolors='k',label=_label,s=50)
		# 		# ax.scatter(sc.node_list[ii].cen_vec[0],sc.node_list[ii].cen_vec[1],sc.node_list[ii].cen_vec[2],"%d"%(ii),zorder=2,color='ro',label=_label)
		# 	elif col=='visibility':
		# 		side[ii]._facecolors3d=np.asarray([m.to_rgba(vis_sums[ii])])
		# 		side[ii]._edgecolors3d=np.array([[1,0,0,1]])
			
		# 	#Draw normal arrow
		# 	if normals==True:
		# 		xs=[sc.node_list[ii].cen_vec[0],sc.node_list[ii].cen_vec[0]+100*sc.node_list[ii].norm_vec[0]]
		# 		ys=[sc.node_list[ii].cen_vec[1],sc.node_list[ii].cen_vec[1]+100*sc.node_list[ii].norm_vec[1]]
		# 		zs=[sc.node_list[ii].cen_vec[2],sc.node_list[ii].cen_vec[2]+100*sc.node_list[ii].norm_vec[2]]
		# 		if col=='numbered':
		# 			normal_list.append(Arrow3D(xs,ys,zs,mutation_scale=10,lw=2,arrowstyle='-|>',color=_col[0]))
		# 		else:
		# 			normal_list.append(Arrow3D(xs,ys,zs,mutation_scale=10,lw=2,arrowstyle='-|>',color='k'))
		# 		ax.add_artist(normal_list[ii])

		# 	#Draw node
		# 	if ii not in exclude:
		# 		ax.add_collection3d(side[ii])

		# 	plt.axis('square')
		
		# # if not new:
		# 	#Have to set axis to square before setting limits, otherwise limits are not respected
			
		# ax.set_zlim(-600,600)
		# ax.set_ylim(-600,600)
		# ax.set_xlim(-600,600)
		# ax.set_xlabel('x')
		# ax.set_ylabel('y')
		# ax.set_zlabel('z')
		# ax.set_title('SkyHopper Radiator Deployment Angles')
		

		# if col=='numbered':
		# 	plt.legend()

		# plt.show(block=block)
		#plt.show (block = False)


# vis_mask=[],normals=False,block=False,exclude=[]


# Visibility colour mapping
# Set grayscale colour map: black=min, white=max
			# try:
			# 	vis_sums=np.sum(vis_mask,axis=1)
			# 	col_max=np.max(vis_sums)
			# 	col_min=np.min(vis_sums)
			# 	col_norm=mpl.colors.Normalize(vmin=col_min,vmax=col_max)
			# 	m=cm.ScalarMappable(norm=col_norm,cmap=cm.gray)
			# except np.core._internal.AxisError:
			# 	print("No visibility mask supplied")
			# 	return


def _getNumberedColour(num):
	return {
		0: np.asarray([1, 0, 0]),
		1: np.asarray([0.75, 0, 0]),
		2: np.asarray([0, 0, 0.75]),
		3: np.asarray([0, 0.75, 0]),
		4: np.asarray([0.75, 0.75, 0]),
		5: np.asarray([0.75, 0, 0.75]),
		6: np.asarray([0, 0.75, 0.75]),
		7: np.asarray([0.5, 0, 0]),
		8: np.asarray([0, 0.5, 0]),
		9: np.asarray([0, 0, 0.5]),
		10: np.asarray([0.5, 0.5, 0]),
		11: np.asarray([0.5, 0, 0.5]),
		12: np.asarray([0, 0.5, 0.5]),
		13: np.asarray([0.25, 0, 0]),
		14: np.asarray([0, 0.25, 0]),
		15: np.asarray([0, 0, 0.25]),
		16: np.asarray([0.25, 0.25, 0]),
		17: np.asarray([0.25, 0, 0.25]),
		18: np.asarray([0, 0.25, 0.25]),
		19: np.asarray([0.75, 0.5, 0]),
		20: np.asarray([0.75, 0, 0.5]),
	}.get(num, np.asarray([0.5, 0.5, 0.5])) 


def _getSCScale(num):
	return {
		1: 'm',
		0.001: 'mm',
		1000: 'km' 
	}.get(num, 'unrecognised sc scale')