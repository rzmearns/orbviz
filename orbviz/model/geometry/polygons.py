import numpy as np
import numpy.typing as nptyping
import scipy.spatial
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

def segmentIntersection(l1, l2) -> None|np.ndarray[tuple[int], np.dtype[np.float64]]:
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

def getPolygonVerticalIntersection(verts, x_value, close=True):

	''' must be ordered
		can get intersection of polyline with x value by not closing polygon, close=False'''

	if close:
		c_verts = closePolygon(verts)
	else:
		c_verts = verts.copy()

	straddling_segment_idxs = np.where(np.diff(c_verts[:,0]>x_value))[0]

	int_points = [segmentIntersection(np.array((c_verts[idx,:], c_verts[idx+1,:])),
												np.array([[x_value,-90],[x_value,90]])) for idx in straddling_segment_idxs]

	return np.asarray(int_points)

def splitPolygonVertically(verts, x_value):
	r_verts = np.roll(verts, -1, axis=0)

	# A crossing occurs if one x is on one side of x_value, and the next index is on the other side
	cross_mask = (verts[:,0]<x_value) != (r_verts[:,0]<x_value)

	ints = getPolygonVerticalIntersection(verts, x_value)

	insert_idxs = np.where(cross_mask)[0] + 1
	try:
		new_verts = np.insert(verts, insert_idxs, ints, axis=0)
	except ValueError:
		raise ValueError()

	left_poly = new_verts[np.logical_or(new_verts[:, 0] < x_value, np.isclose(new_verts[:,0],x_value))]
	right_poly = new_verts[np.logical_or(new_verts[:, 0] > x_value, np.isclose(new_verts[:,0],x_value))]

	return left_poly, right_poly

def getAugmentedConvexHullBoundary(points):
	points = np.asarray(points)
	ch = scipy.spatial.ConvexHull(points, qhull_options='Qc')
	vertices = ch.vertices

	# Coplanar points (points on the edges but not corners)
	# hull.coplanar is an (n, 3) array where:
	# column 0: index of the coplanar point
	# column 1: index of the nearest vertex (not used here)
	# column 2: index of the facet (edge/face) it lies on
	if ch.coplanar.size > 0:
		coplanar_indices = ch.coplanar[:, 0]
		# Combine and remove duplicates
		all_boundary_indices = np.unique(np.concatenate([vertices, coplanar_indices]))
	else:
		all_boundary_indices = vertices

	return reorderCW(points[all_boundary_indices])