

import numpy as np
import numpy.typing as nptyping
import triangle as tr

import orbviz.model.geometry.primgeom as pg
import orbviz.util.array_u as array_u


def generateCircle(center:tuple[float,float,float] | nptyping.NDArray,
					 radius:float,
					 normal:tuple[float,float,float] | nptyping.NDArray,
					 sampling:int=180):
	coords = np.zeros((sampling,3))
	theta = np.linspace(0, 2*np.pi, sampling)
	center = np.asarray(center)
	e1,e2,e3 = pg.generateONBasisFromPointNormal(center, normal)
	for ii in range(3):
		coords[:,ii] = radius*np.cos(theta)*e1[ii] + radius*np.sin(theta)*e2[ii] + np.zeros(sampling)*e3[ii]

	return coords + center

def polygonTriangulate(polygon_verts):
	t_data = {}
	t_data['vertices'] = array_u.uniqueRowsOrdered(polygon_verts)
	t_data['segments'] = np.hstack((np.arange(len(t_data['vertices'])-1).reshape(-1,1),np.arange(1,len(t_data['vertices'])).reshape(-1,1)))
	t_data['segments'] = np.vstack((t_data['segments'],[len(t_data['segments']-1),0]))
	t = tr.triangulate(t_data,'pq10')
	return t['vertices'], t['triangles']

def isPolygonConvex(polygon_verts):
	rot_verts = polygon_verts[:,[1,0]]
	rot_verts[:,0] *= -1

	# does p_(ii+2) lie on left side of segment between p_(ii) and p_(ii+1)
	cnvx_angles = np.sum((np.roll(rot_verts,shift=-1, axis=0)-rot_verts)*
						(np.roll(polygon_verts,shift=-2,axis=0)-rot_verts), axis=1)>0
	# regardless of winding, if all convex_angle is False or True then poly is convex
	return (cnvx_angles == cnvx_angles[0]).all()