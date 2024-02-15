import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.polyhedra as polyhedra
import plotly.graph_objects as go
import numpy as np
import logging

logger = logging.getLogger(__name__)


def subplotInt2Idx(subplot_pos):
	rows = int(subplot_pos / 100)
	cols = int((subplot_pos - (rows * 100)) / 10)
	idx = int(subplot_pos - (rows * 100) - (cols * 10))

	return rows, cols, idx


def findFigure(name_str):
	exis_fignums = plt.get_fignums()
	if exis_fignums is None or len(exis_fignums)==0:
		return None
	else:
		if name_str == '':
			return plt.gcf()
		exis_figlabels = plt.get_figlabels()

		logger.debug("Extant figure labels: {}".format(', '.join(map(str, exis_figlabels))))

		try:
			fig_idx = exis_figlabels.index(name_str)
		except ValueError:
			return None
		return plt.figure(exis_fignums[fig_idx])


def findAxes(name_str, subplot_pos):
	'''
	Finds the last drawn figure with the specified label, and returns its ax handle
	Returns None if no figure with the specified label exists.

	Parameters
	----------
	name_str : {String}		
		string of figure and window
	Returns
	-------
	ax : pointer
	'''

	fig = findFigure(name_str)

	if isinstance(subplot_pos, int):
		_, _, ax_idx = subplotInt2Idx(subplot_pos)
	else:
		ax_idx = subplot_pos[-1]
	axes = fig.get_axes()
	if len(axes) == 0:
		return None
	for ax in axes:

		if ax.get_subplotspec().get_geometry()[2] == ax_idx - 1:
			return ax
	
	return None


def clearPlot(name_str, subplot_pos=111):
	"""Emptys an axes

	Parameters
	----------
	name_str : {String}		
		string of figure and window
	"""
	ax = findAxes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	logger.debug("Clearing axes: %s", name_str)
	ax.clear()


def labelAxes(name_str, subplot_pos=111, x='x', y='y', z='z'):
	"""Labels each axis
	
	If supplied axes is 2d, will only apply x and y labels.

	Parameters
	----------
	name_str : {String}
		string of figure and window
	x : {str}, optional
		x label (the default is 'x'
	y : {str}, optional
		y label (the default is 'y'
	z : {str}, optional
		z label (the default is 'z'
	"""
	ax = findAxes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	logger.debug('Labeling %s axes', name_str)
	ax.set_xlabel(x)
	ax.set_ylabel(y)
	if ax.name == '3d':
		ax.set_zlabel(z)


def squareAxes(name_str, max_dim=None, subplot_pos=111):
	"""Squares the axes
	
	Takes the maximum and minimum value across each axis, sets each axis to these values
	
	Parameters
	----------
	name_str : {String}		
		string of figure and window
	"""
	ax = findAxes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	lims = []
	lims.append(ax.get_xlim3d())
	lims.append(ax.get_ylim3d())
	if ax.name == '3d':
		lims.append(ax.get_zlim3d())

	limlist = [i for sub in lims for i in sub]

	if max_dim is None:
		max_val = np.abs(limlist).max()
	else:
		max_val = max_dim
	logger.debug("Setting %s axes to [%f, %f]", name_str, -max_val, max_val)
	ax.set_xlim3d([-max_val, max_val])
	ax.set_ylim3d([-max_val, max_val])

	if ax.name == '3d':
		ax.set_zlim3d([-max_val, max_val])
		ax.set_box_aspect((1, 1, 1))
	else:
		ax.set_aspect('equal')


def setSquareLimits(ax, min, max):
	ax.set_xlim([min, max])
	ax.set_ylim([min, max])
	ax.set_zlim([min, max])


def _dictionary(sc):
	'''
	Prints dictionary of Poly3DCollection,
	Documentation of Poly3DCollection sucks
	'''
	side = Poly3DCollection([sc.node_list[0].face_verts])
	d = side.__dict__
	for key in d:
		print(key + 'corresponds to' + d[key])


def setTitle(name_str, title, subplot_pos=111):
	'''
	Sets the title on the most recent figure specified by label_str

	Parameters
	----------
	name_str : {String}	
		string of figure and window
	title : str
		title of axes	
	'''
	ax = findAxes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	ax.set_title(title)
	plt.show(block=False)


def createFigure(name_str, title, three_dim=False, subplot_pos=111):
	fig = findFigure(name_str)
	if fig is None:
		fig = plt.figure()
		fig.canvas.manager.set_window_title(name_str)
		fig.set_label(name_str)
	# TODO: check if axis already exists in figure
	ax = findAxes(name_str, subplot_pos)
	if ax is None:
		if not three_dim:
			ax = fig.add_subplot(subplot_pos)
		else:
			ax = fig.add_subplot(subplot_pos, projection='3d')
		setTitle(name_str, title, subplot_pos=subplot_pos)
	

class Arrow3D(FancyArrowPatch):
	def __init__(self, xs, ys, zs, *args, **kwargs):
		FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
		self._verts3d = xs, ys, zs

	def draw(self, renderer):
		xs3d, ys3d, zs3d = self._verts3d
		xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
		self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
		FancyArrowPatch.draw(self, renderer)


class SliderAxes(object):
	def __init__(self, figure_name):
		self.fig = findFigure(figure_name)
		self.axcolor = 'lightgoldenrodyellow'
		self.ax = plt.axes([0.25, 0.05, 0.65, 0.015], facecolor=self.axcolor)


def plotSphere(fig, center, r, col='rgb(220,220,220)', alpha=1):
	R = np.sqrt(r)
	u_angle = np.linspace(0, 2*np.pi, 25)
	v_angle = np.linspace(0, np.pi, 25)
	x_dir = np.outer(R*np.cos(u_angle), R*np.sin(v_angle)) + center[0]
	y_dir = np.outer(R*np.sin(u_angle), R*np.sin(v_angle)) + center[1]
	z_dir = np.outer(R*np.ones(u_angle.shape[0]), R*np.cos(v_angle)) + center[2]
	num_traces = len(fig.data)
	fig.add_surface(z=z_dir, x=x_dir, y=y_dir,
						colorscale=[[0, col], [1, col]],
						opacity=alpha,
						showlegend=False,
						lighting=dict(diffuse=0.1),
						hoverinfo='skip',
						showscale=False)
	trace_index = num_traces
	return trace_index

# def plotCylinder(fig, )
# 		shadow_point = -self.sun_dist * pg.unitVector(self.orbit.sun[self.curr_index])

# 		p0 = np.array([0,0,0])
# 		p1 = shadow_point
# 		R = c.R_EARTH
# 		v_mag = np.linalg.norm(p1-p0)
# 		v = pg.unitVector(p1-p0)
# 		not_v = np.array([1,0,0])
# 		if(v == not_v).all():
# 			not_v = np.array([0,1,0])
# 		n1 = pg.unitVector(np.cross(v, not_v))
# 		n2 = pg.unitVector(np.cross(v, n1))

# 		t = np.linspace(0,v_mag,2)
# 		theta = np.linspace(0, 2*np.pi, 99)
# 		rsample = np.linspace(0,R,2)
# 		t, theta2 = np.meshgrid(t,theta)
# 		rsample, theta = np.meshgrid(rsample, theta)
# 		X,Y,Z = [p0[i] + v[i] * t + R * np.sin(theta2) * n1[i] + R * np.cos(theta) * n2[i] for i in [0, 1, 2]]
# 		X2,Y2,Z2 = [p0[i] + v[i]*v_mag + rsample[i] * np.sin(theta) * n1[i] + rsample[i] * np.cos(theta) * n2[i] for i in [0, 1, 2]]
# 		col=f"rgb{str(self.opts['umbra_colour'])}"
# 		num_traces = len(self.fig.data)

# 		self.fig.add_surface(x=X,
# 					   		y=Y,
# 							z=Z,
# 							colorscale=[[0, col], [1, col]],
# 							opacity=self.opts['umbra_opacity'],
# 							showlegend=False,
# 							lighting=dict(diffuse=0.1),
# 							hoverinfo='skip',
# 							showscale=False)
# 		self.traces['umbra_tube'] = num_traces

# 		self.fig.add_surface(x=X2,
# 					   		y=Y2,
# 							z=Z2,
# 							colorscale=[[0, col], [1, col]],
# 							opacity=self.opts['umbra_opacity'],
# 							showlegend=False,
# 							lighting=dict(diffuse=0.1),
# 							hoverinfo='skip',
# 							showscale=False)
# 		self.traces['umbra_cap'] = num_traces+1
		
# 		self.fig.data[self.traces['umbra_tube']].contours.x.highlight = False
# 		self.fig.data[self.traces['umbra_tube']].contours.y.highlight = False
# 		self.fig.data[self.traces['umbra_tube']].contours.z.highlight = False
# 		self.fig.data[self.traces['umbra_cap']].contours.x.highlight = False
# 		self.fig.data[self.traces['umbra_cap']].contours.y.highlight = False
# 		self.fig.data[self.traces['umbra_cap']].contours.z.highlight = False

# 		trace_index = visutils.plotSphere(self.fig, -1.5*shadow_point, 500, col=f"rgb{str(self.opts['sun_colour'])}")
# 		self.traces['sun'] = trace_index

# 		self.fig.update_layout(scene={'xaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})
# 		self.fig.update_layout(scene={'yaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})
# 		self.fig.update_layout(scene={'zaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})

def plotCone(fig, apex, height, height_v, apex_angle_deg, col='rgb(220,220,220)', alpha=1, hovertext=None):
		
		cone,cap = polyhedra.calcCone(apex,height,height_v,apex_angle_deg, axis_sample=2,theta_sample=15)

		if hovertext is None:
			hover_info = 'skip'
		else:
			hover_info = 'text'

		num_traces = len(fig.data)
		fig.add_surface(x=cone[0],
						y=cone[1],
						z=cone[2],
						colorscale=[[0, col], [1, col]],
						opacity=alpha,
						showlegend=False,
						lighting=dict(diffuse=0.1),
						hoverinfo=hover_info,
						text=hovertext,
						showscale=False)
		cone_index = num_traces

		fig.add_trace(go.Scatter3d(x=cap[0],
									y=cap[1],
									z=cap[2],
									mode='lines',
									line={'dash':'solid',
										'color':col,
										'width':2},
									hoverinfo='skip',
									showlegend=False))
		cap_index = num_traces+1

		fig.data[cone_index].contours.x.highlight = False
		fig.data[cone_index].contours.y.highlight = False
		fig.data[cone_index].contours.z.highlight = False

		return cone_index, cap_index
