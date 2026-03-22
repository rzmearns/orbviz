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

def polygonTriangulate(polygon_verts: np.ndarray):
	if len(polygon_verts)<3:
		return np.zeros((3,2), dtype=np.float64), np.array((0,1,2), dtype=np.int32)
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

def closePolygon(points):
	if np.all(points[-1] == points[0]):
		return points
	else:
		return np.append(points,points[0,:].reshape(1,2),axis=0)

def reorderCW(points):
	center = np.mean(points, axis=0)

	diff = points - center
	angles = np.arctan2(diff[:, 1], diff[:, 0])
	indices = np.argsort(-angles)

	return points[indices]

def findCentroid(verts):

	verts_shift = np.roll(verts, -1, axis=0)

	# using shoelace formula
	common_term = verts[:,0] * verts_shift[:,1] - verts_shift[:,0] * verts[:,1]
	area = 0.5 * np.sum(common_term)
	common_term = common_term.reshape(-1,1)

	# Calculate centroid coordinates
	c = np.sum(verts*common_term + verts_shift*common_term, axis=0) / (6.0 * area)

	return c

def isSplitVertically(x_split, poly_verts):

	if np.all(poly_verts[:,0] < x_split) or np.all(poly_verts[:,0] >= x_split):
		return False

	return True

def segmentIntersection(l1, l2) -> None|np.ndarray[tuple[int], np.dtype(np.float64)]:
	'''Return intersection of two line segments

	Args:
		l1 ([type]): 2x2 array
		l2 ([type]): 2x2 array

	Returns:
		[ndarray (2,)]: intersection point
		None: no intersection
	'''
	# Vectors
	d1 = l1[1]-l1[0]
	d2 = l2[1]-l2[0]
	v = l2[0] - l1[0]

	m1 = np.array((d1,d2))
	m2 = np.array((v,d1))
	m3 = np.array((v,d2))

	denom = np.linalg.det(m1)

	# check parallelism
	if np.isclose(denom, 0):
	    return None

	# Calculate parameterisations of int for each segment
	t = np.linalg.det(m3) / denom
	u = np.linalg.det(m2) / denom

	if 0 <= t <= 1 and 0 <= u <= 1:
	    p_int = l1[0] + t * d1
	    return p_int

	return None

def getPolygonVerticalIntersection(verts, x_value):

	''' must be ordered'''

	c_verts = closePolygon(verts)
	straddling_segment_idxs = np.where(np.diff(c_verts[:,0]>x_value))[0]

	if len(straddling_segment_idxs) > 2:
		raise ValueError('More than 2 intersections found')

	int_points = [segmentIntersection(np.array((c_verts[idx,:], c_verts[idx+1,:])),
												np.array([[x_value,-90],[x_value,90]])) for idx in straddling_segment_idxs]

	return np.asarray(int_points)
