import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
import numpy as np
import logging

logger = logging.getLogger(__name__)


def subplotint2idx(subplot_pos):
	rows = int(subplot_pos / 100)
	cols = int((subplot_pos - (rows * 100)) / 10)
	idx = int(subplot_pos - (rows * 100) - (cols * 10))

	return rows, cols, idx


def find_figure(name_str):
	exis_fignums = plt.get_fignums()
	if not exis_fignums:
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


def find_axes(name_str, subplot_pos):
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

	fig = find_figure(name_str)

	if isinstance(subplot_pos, int):
		_, _, ax_idx = subplotint2idx(subplot_pos)
	else:
		ax_idx = subplot_pos[-1]
	axes = fig.get_axes()
	if len(axes) == 0:
		return None
	for ax in axes:

		if ax.get_subplotspec().get_geometry()[2] == ax_idx - 1:
			return ax
	
	return None


def clear_plot(name_str, subplot_pos=111):
	"""Emptys an axes

	Parameters
	----------
	name_str : {String}		
		string of figure and window
	"""
	ax = find_axes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	logger.debug("Clearing axes: %s", name_str)
	ax.clear()


def label_axes(name_str, subplot_pos=111, x='x', y='y', z='z'):
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
	ax = find_axes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	logger.debug('Labeling %s axes', name_str)
	ax.set_xlabel(x)
	ax.set_ylabel(y)
	if ax.name == '3d':
		ax.set_zlabel(z)


def square_axes(name_str, max_dim=None, subplot_pos=111):
	"""Squares the axes
	
	Takes the maximum and minimum value across each axis, sets each axis to these values
	
	Parameters
	----------
	name_str : {String}		
		string of figure and window
	"""
	ax = find_axes(name_str, subplot_pos)
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


def set_square_limits(ax, min, max):
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


def set_title(name_str, title, subplot_pos=111):
	'''
	Sets the title on the most recent figure specified by label_str

	Parameters
	----------
	name_str : {String}	
		string of figure and window
	title : str
		title of axes	
	'''
	ax = find_axes(name_str, subplot_pos)
	if ax is None:
		logger.error("%s figure does not exist", name_str)
		return
	ax.set_title(title)
	plt.show(block=False)


def create_figure(name_str, title, three_dim=False, subplot_pos=111):
	if find_figure(name_str) is None:
		fig = plt.figure()
		fig.canvas.manager.set_window_title(name_str)
		fig.set_label(name_str)
	else:
		fig = find_figure(name_str)
	if not three_dim:
		ax = fig.add_subplot(subplot_pos)
	else:
		ax = fig.add_subplot(subplot_pos, projection='3d')

	set_title(name_str, title, subplot_pos=subplot_pos)
	

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
		self.fig = find_figure(figure_name)
		self.axcolor = 'lightgoldenrodyellow'
		self.ax = plt.axes([0.25, 0.05, 0.65, 0.015], facecolor=self.axcolor)