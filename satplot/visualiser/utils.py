import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.polyhedra as polyhedra
import plotly.graph_objects as go
import numpy as np
import logging

logger = logging.getLogger(__name__)


def subplotInt2Idx(subplot_pos):
	raise NotImplementedError()


def findFigure(name_str):
	raise NotImplementedError()


def findAxes(name_str, subplot_pos):
	raise NotImplementedError()

def clearPlot(name_str, subplot_pos=111):
	raise NotImplementedError()

def labelAxes(name_str, subplot_pos=111, x='x', y='y', z='z'):
	raise NotImplementedError()

def squareAxes(name_str, max_dim=None, subplot_pos=111):
	raise NotImplementedError()


def setSquareLimits(ax, min, max):
	raise NotImplementedError()

def _dictionary(sc):
	raise NotImplementedError()


def setTitle(name_str, title, subplot_pos=111):
	raise NotImplementedError()

def createFigure(name_str, title, three_dim=False, subplot_pos=111):
	raise NotImplementedError()	

class Arrow3D():
	def __init__():
		raise NotImplementedError()

class SliderAxes(object):
	def __init__():
		raise NotImplementedError()


def plotSphere(fig, center, r, col='rgb(220,220,220)', alpha=1):
	sphere = polyhedra.calcSphere(center, r)
	num_traces = len(fig.data)
	fig.add_surface(x=sphere[0],
				 	y=sphere[1],
					z=sphere[2],
					colorscale=[[0, col], [1, col]],
					opacity=alpha,
					showlegend=False,
					lighting=dict(diffuse=0.1),
					hoverinfo='skip',
					showscale=False)
	trace_index = num_traces
	return trace_index

def plotCone(fig, apex, height, height_v, apex_angle_deg, col='rgb(220,220,220)', alpha=1, hovertext=None):
		
		cone,cap = polyhedra.calcCone(apex,height,height_v,apex_angle_deg, axis_sample=2,theta_sample=30)

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
