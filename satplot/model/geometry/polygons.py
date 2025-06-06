import numpy as np
import numpy.typing as nptyping
import triangle as tr
import satplot.model.geometry.primgeom as pg
import satplot.util.array_u as array_u

def generateCircle(center:tuple[float,float,float] | nptyping.NDArray,
					 radius:float,
					 normal:tuple[float,float,float] | nptyping.NDArray,
					 sampling:int=180):
	coords = np.zeros((sampling,3))
	theta = np.linspace(0, 2*np.pi, 180)
	center = np.asarray(center)
	e1,e2,e3 = pg.generateONBasisFromPointNormal(center, normal)
	for ii in range(3):
		coords[:,ii] = radius*np.cos(theta)*e1[ii] + radius*np.sin(theta)*e2[ii] + np.zeros(180)*e3[ii]

	return coords + center

def polygonTriangulate(polygon_verts):
	t_data = {}
	t_data['vertices'] = array_u.uniqueRowsOrdered(polygon_verts)
	t_data['segments'] = np.hstack((np.arange(len(t_data['vertices'])-1).reshape(-1,1),np.arange(1,len(t_data['vertices'])).reshape(-1,1)))
	t_data['segments'] = np.vstack((t_data['segments'],[len(t_data['segments']-1),0]))
	t = tr.triangulate(t_data,'pq10')
	return t['vertices'], t['triangles']