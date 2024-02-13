import numpy as np

import logging

import satplot.util.exceptions as exceptions
import satplot.model.geometry.primgeom as pg

'''
Used Data Types
vector = numpy
line = (2,3) ndarray
poly = (n,3) ndarray - n > 2, all points coplanar, non-closed i.e. a triangle has vertices [0,1,2] not [0,1,2,0]
hull = (m,3) ndarray - m > 4, not all points coplanar
'''


def shiftPolytope(poly, delta):
	'''Translate a polytope by the specified delta
	
	Parameters
	----------
	poly : {(n,3) ndarray}
		List of vertices in poly
	delta : {3 tuple}
		Tuple of delta in x,y,z to translate poly
	
	Returns
	-------
	(n,3) ndarray
		Translated poly
	'''
	m, n = poly.shape
	poly_out = np.zeros((poly.shape))
	poly_out[:, 0] = poly[:, 0] + delta[0]
	poly_out[:, 1] = poly[:, 1] + delta[1]
	if n == 3:
		poly_out[:, 2] = poly[:, 2] + delta[2]
	return poly_out


def expandPolyhedron(poly, factor):
	'''Expand poly vertices from center by factor
	
	Parameters
	----------
	poly : {(n,3) ndarray}
		List of polytope vertices
	factor : {float}
		expansion factor
	
	Returns
	-------
	(n,3) ndarray
		List of expanded polytope vertices
	'''
	centroid = np.sum(poly, axis=0) / len(poly)
	new_poly = (factor * (poly - centroid)) + centroid
	return new_poly


def rotationMatrix(v1, v2): 
	"""
	Calculates a rotation matrix that changes v1 into v2. 
	
	Parameters
	----------
	v1: (3,) numpy array
	v2: (3,) numpy array
	
	Returns
	-------
	M: (3,3) numpy array
		A rotation matrix that, when applied to v1, yields v2.
	
	"""
	if np.allclose(v1, v2):
		return np.eye(3)
	if np.allclose(v1, -v2):
		return -np.eye(3)
	# v1_norm = v1 / np.linalg.norm(v1) 
	v1_norm = pg.unitVector(v1)
	# v2_norm = v2 / np.linalg.norm(v2) 
	v2_norm = pg.unitVector(v2)

	cos = np.dot(v1_norm, v2_norm) 
	k = pg.unitVector(np.cross(v1_norm, v2_norm))
	sin = np.linalg.norm(k)
	
	# print(f'sin_angle:{sin}')
	if np.isclose(sin, 0): 
		M = np.eye(3) if cos > 0. else -np.eye(3) 
	else: 
		# Using Rodrigues rotation formula
		# https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula
		# K = np.array([[0, -k[2], k[1]], 
		# 				[k[2], 0, -k[0]], 
		# 				[-k[1], k[0], 0]], dtype=np.float64)
		# M = np.eye(3) + sin * K + (1 - cos) * np.dot(K, K)
		# d /= sin_angle 

		# eye = np.eye(3) 
		# ddt = np.outer(d, d) 
		# # skew = np.array([[0, d[2], -d[1]], 
		# # 				[-d[2], 0, d[0]], 
		# # 				[d[1], -d[0], 0]], dtype=np.float64)
		# skew = np.array([[0, -d[2], d[1]], 
		# 				[d[2], 0, -d[0]], 
		# 				[-d[1], d[0], 0]], dtype=np.float64)

		# # M = ddt + cos_angle * (eye - ddt) + sin_angle * skew 
		# M = np.eye(3) + skew + np.dot(skew,skew) * (1 - cos_angle) / (sin_angle)**2

		# M = 2 * np.dot((v1_norm + v2_norm),(v1_norm + v2_norm).T) / np.dot((v1_norm + v2_norm).T,(v1_norm + v2_norm)) - np.eye()

		c = np.dot(v1_norm, v2_norm)
		v = np.cross(v1_norm, v2_norm)
		h = (1 - c) / np.dot(v, v)
		M = np.array([[c + h * v[0]**2, h * v[0] * v[1] - v[2], h * v[0] * v[2] + v[1]], 
						[h * v[0] * v[1] + v[2], c + h * v[1]**2, h * v[1] * v[2] - v[0]], 
						[h * v[0] * v[2] - v[1], h * v[1] * v[2] + v[0], c + h * v[2]**2]], dtype=np.float64)


	return M

	
def rotAround(angle, axis=pg.Z):
	'''
	Returns rotation matrix that rotates counterclockwise by an angle theta
	around a chosen axis, following the right hand rule.
	
	Mathematics powered by the Rodrigues rotation formula:
	https://mathworld.wolfram.com/RodriguesRotationFormula.html
	
	Parameters
	----------
	angle: float
		Angle about which to rotate all points (radians)
	
	axis: {(3,) numpy array}
		Axis around which to rotate points (points on this axis will not move)
		Defaults to the z-axis
	
	Returns
	-------
	rot_mat: {(3,3) numpy array}
		Rotation matrix that rotates about the axis by the given angle.
	'''
	axis = pg.unitVector(axis)
	W = np.array([[0,		 -axis[2], axis[1] ],
				  [axis[2],	 0,		   -axis[0]],
				  [-axis[1], axis[0],  0	   ]])
	rot_mat = np.eye(3) + np.sin(angle)*W + (1 - np.cos(angle))* (W @ W)
	return rot_mat
	

def rotMat(theta,rot_base,rot_axis):
	'''
	Returns rotation matrix around arbitrary Axis defined by a base point, rot_base and an axis, rot_axis
	Rotation matrix will perform the following operations on the vector it is applied to:
		Move vector s.t. rot_base is origin
		Rotate vector s.t. rot_axis is in the XZ plane
		Rotate vector s.t. rot_axis is Z axis
		Rotate vector about Z axis by theta
		Reverse (rotate vector s.t. rot_axis is Z axis)
		Reverse (rotate vector s.t. rot_axis is in the XZ plane)
		Reverse (move vector s.t. rot_base is origin)
	R=T_P1^-1 T_xz^-1 T_z^-1 R_z(theta) T_z T_xz T_P1	 
	
	
	Maths powered by affine transformation matrix:
	https://www.brainvoyager.com/bv/doc/UsersGuide/CoordsAndTransforms/SpatialTransformationMatrices.html
	
	Parameters
	----------
	theta : float
		angle in radians

	Returns
	-------
	(4,4) ndarray
	Affine transformation matrix
	
	'''		  

	T_P1=np.array([[1,0,0,-rot_base[0]],[0,1,0,-rot_base[1]],[0,0,1,-rot_base[2]],[0,0,0,1]])
	try:
		np.linalg.inv(T_P1)
	except np.linalg.LinAlgError:
		print("T_P1")
		print(T_P1)
		print("T_P1 is singular")


	T_xz=np.eye(4)
	u=rot_axis[0]
	v=rot_axis[1]
	w=rot_axis[2]
	diag=u/np.sqrt(u**2+v**2)
	T_xz[0,0]=diag
	T_xz[1,1]=diag
	off_diag=v/np.sqrt(u**2+v**2)
	T_xz[0,1]=off_diag
	T_xz[1,0]=-off_diag		   
	try:
		np.linalg.inv(T_xz)
	except np.linalg.LinAlgError:
		print("T_xz")
		print(T_xz)
		print("T_xz is singular")


	T_z=np.eye(4)
	diag=w/np.sqrt(u**2+v**2+w**2)
	T_z[0,0]=diag
	T_z[2,2]=diag
	off_diag=np.sqrt(u**2+v**2)/np.sqrt(u**2+v**2+w**2)
	T_z[0,2]=-off_diag
	T_z[2,0]=off_diag		 
	try:
		np.linalg.inv(T_z)
	except np.linalg.LinAlgError:
		print("T_z")
		print(T_z)
		print("T_z is singular")

	R_z=np.eye(4)
	diag=np.cos(theta)
	R_z[0,0]=diag
	R_z[1,1]=diag
	off_diag=np.sin(theta)
	R_z[0,1]=-off_diag
	R_z[1,0]=off_diag		 

	if np.array_equal(np.abs(rot_axis),np.array([0,0,1])):
		return reduce(np.dot,[np.linalg.inv(T_P1),R_z,T_P1])
	else:
		return reduce(np.dot,[np.linalg.inv(T_P1),np.linalg.inv(T_xz),np.linalg.inv(T_z),R_z,T_z,T_xz,T_P1])

def rotMat2xy(normal):
	'''

	'''

#TODO Need to look at this to see what it is really doing

	T_xz=np.eye(4)
	u=normal[0]
	v=normal[1]
	w=normal[2]
	diag=u/np.sqrt(u**2+v**2)
	T_xz[0,0]=diag
	T_xz[1,1]=diag
	off_diag=v/np.sqrt(u**2+v**2)
	T_xz[0,1]=off_diag
	T_xz[1,0]=-off_diag		   
	try:
		np.linalg.inv(T_xz)
	except np.linalg.LinAlgError:
		print("T_xz")
		print(T_xz)
		print("T_xz is singular")


	T_z=np.eye(4)
	diag=w/np.sqrt(u**2+v**2+w**2)
	T_z[0,0]=diag
	T_z[2,2]=diag
	off_diag=np.sqrt(u**2+v**2)/np.sqrt(u**2+v**2+w**2)
	T_z[0,2]=-off_diag
	T_z[2,0]=off_diag		 
	try:
		np.linalg.inv(T_z)
	except np.linalg.LinAlgError:
		print("T_z")
		print(T_z)
		print("T_z is singular")

	if np.array_equal(np.abs(normal),np.array([0,0,1])):
		return np.eye(4)
	else:
		return reduce(np.dot,[T_z,T_xz])