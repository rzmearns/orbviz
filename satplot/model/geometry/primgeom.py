import numpy as np
import numpy.typing as nptyping
import scipy.spatial
import math
import warnings
import logging
import satplot.util.exceptions as exceptions
# warnings.filterwarnings('error',message='divide by zero')
# warnings.filterwarnings('error',message='invalid value')

'''
Used Data Types
vector = numpy
line = (2,3) ndarray
poly = (n,3) ndarray - n > 2, all points coplanar, non-closed i.e. a triangle has vertices [0,1,2] not [0,1,2,0]
hull = (m,3) ndarray - m > 4, not all points coplanar
'''

logger = logging.getLogger(__name__)

# The cartesian unit vectors
X = np.array([1, 0, 0])
Y = np.array([0, 1, 0])
Z = np.array([0, 0, 1])


def unitVector(vector:nptyping.NDArray) -> nptyping.NDArray:
	''' Returns the unit vector

	Parameters
	----------
	vector: numpy vector or array of vectors

	Returns
	----------
	: normalised numpy vector or vectors

	'''
	if np.allclose(vector, np.zeros(vector.shape), rtol=1e-8):
		raise exceptions.InputError("Cannot norm 0-vector")
	
	if len(vector.shape) == 1:
		return vector / np.linalg.norm(vector)
	elif len(vector.shape) == 2:
		norms = np.linalg.norm(vector, axis=1)
		return vector / norms[:, None]
	else:
		logger.error("Vector must be either a vector or an array of vectors")
		raise exceptions.InputError("Vectors of shape {} are not supported by unitVector.".format(vector.shape))


def randUnitVector() -> nptyping.NDArray:
	''' Returns a unit vector pointing in a random direction
	Maths powered by: mathworld.wolfram.com/SpherePointPicking.html
	'''
	v = np.random.normal(size=3)
	return v / np.linalg.norm(v)

def generateONBasisFromPointNormal(point, normal):
	e3 = unitVector(np.asarray(normal))
	not_e3 = np.array([1,0,0])
	if(e3 == not_e3).all():
		not_e3 = np.array([0,1,0])
	e1 = unitVector(np.cross(e3, not_e3))
	e2 = unitVector(np.cross(e3, e1))

	return e1,e2,e3


def angleBetween(v1:nptyping.NDArray, v2:nptyping.NDArray, units:str="rad") -> float:
	'''angle_between(v1,v2,units="rad/")
	returns the angle between numpy vectors v1 and v2
	
	Parameters
	----------
	v1: ndarray
	v2: ndarray
	
	units: {str}
		'rad' or 'deg'
	'''
	v1.shape
	v2.shape
	v1_u = unitVector(v1)
	v2_u = unitVector(v2)
	angle = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))		  
	if units == "rad":
		return angle
	elif units == "deg":
		return np.rad2deg(angle)
	else: 
		logger.error('Bad unit for angle between.')
		raise NotImplementedError("{} is not a valid unit for the angle. units must be either 'rad' or 'deg'.".format(units))


def seqPointsSignedAngle(prev_pnt:nptyping.NDArray, curr_pnt:nptyping.NDArray, next_pnt:nptyping.NDArray, norm:nptyping.NDArray=Z) -> float:
	'''
	Returns the signed angle defined by the three points `prev`->`curr`->`next`.
	curr_pnt is the vertex between edges defined by `prev_pnt` -> `curr_pnt` and `curr_pnt` -> `next_pnt`
	The direction of the sign is defined by `norm`
	-pi < res < pi
	Result will be negative if reflex, and points are wound CCW around the supplied norm.
	
	Parameters
	----------
	prev_pnt : {(3,) numpy array}
		Cartesian coordinates of previous point
	pnt_indx : {(3,) numpy array}
		Cartesian coordinates of current point
	next_pnt_indx : {(3,) numpy array}
		Cartesian coordinates of next point 
	norm : {(3,) numpy array}
		Normal vector, defining counterclockwise direction (defaults to z axis)
	
	Returns
	-------
	[float]
		signed angle between -pi and pi
	'''

	v1 = prev_pnt - curr_pnt
	v2 = next_pnt - curr_pnt

	angle = -vectorSignedAngle(v1, v2, norm)

	return angle 


def vectorSignedAngle(v1:nptyping.NDArray, v2:nptyping.NDArray, norm:nptyping.NDArray=Z) -> float:
	'''
	Returns the signed angle between the vector v1 to the vector v2.
	The direction of the sign is defined by `norm`
	
	Parameters
	----------
	v1: {(3,) numpy array}
	v2: {(3,) numpy array}
	norm: {(3,) numpy array}
		Normal vector, defining counterclockwise direction (defaults to z axis)
	
	Returns
	-------
	angle: {float}
		signed angle between -pi and pi
	'''

	m1 = v1.shape[0]
	m2 = v2.shape[0]

	# check v* are vectors
	if m1 == 1 or m1 > 3:
		raise exceptions.InputError(f'{v1} is not a vector')
	# Check v1 and v2 are same dimensions
	if m1 != m2:
		raise exceptions.InputError(f'Dimensions of {v1} and {v2} do not match')

	# If 2D pad to 3D, and set norm
	if m1 == 2:
		v1 = np.concatenate((v1, np.zeros(1)))
		v2 = np.concatenate((v2, np.zeros(1)))
		norm = Z

	sign = np.sign(np.dot(np.cross(v1, v2), norm))
	angle = angleBetween(v1, v2)

	# Fix sign for parallel vectors
	if sign == 0:
		sign = 1

	# Fix magnitude for identical vectors
	if np.isclose(angle, 0, atol=1e-7):
		angle = 0

	return sign * angle


def orthogonalProjection(v1:nptyping.NDArray, v2:nptyping.NDArray) -> nptyping.NDArray:
	'''
	Returns the projection of v1 in the direction orthogonal to v2.
	
	Parameters
	----------
	v1: (3,) or (N,3) numpy array
		Vector or list of vectors
	
	v2: (3,) or (N,3) numpy array
		Vector or list of vectors
		Must be either a single vector, or the same length as v1
		
	Returns
	-------
	ortho_proj: (3,) or (3,N) numpy array
		Projection of each vector in v1 orthogonal to v2.
	'''
	# check dimensions
	if v1.shape[-1] != 3 or v2.shape[-1] != 3:
		logger.error("Orthogonal projection only defined for 3D vectors or lists of 3D vectors!") 
		raise exceptions.DimensionError("Orthogonal projection only defined for 3D vectors or lists of 3D vectors!") 
	if v1.shape != v2.shape:
		if v2.shape != (3,):
			logger.error("v2 must be either a single vector, or a list of vectors the same length as v1.") 
			raise exceptions.DimensionError("v2 must be either a single vector, or a list of vectors the same length as v1.") 
		else:
			# Convert v2 to be the same shape as v1
			v2 = np.repeat([v2], v1.shape[0], axis=0)
	
	# Case 1: single vectors
	if v1.shape == (3,):
		v2 = unitVector(v2)
		proj = np.dot(v1,v2) * v2
		ortho_proj = v1 - proj
	# Case 2: Arrays of vectors
	else:
		# fancy trick from: https://stackoverflow.com/questions/37670658/python-dot-product-of-each-vector-in-two-lists-of-vectors
		dot		   = np.einsum('ij, ij->i', v1, v2)
		norm2	   = np.linalg.norm(v2, axis=1)
		proj	   = np.einsum('i, ij->ij',(dot/(norm2**2)), v2)
		ortho_proj = v1 - proj
	
	return ortho_proj


def lineParam(line:nptyping.NDArray) -> tuple[float, float, float, float, float, float]:
	'''
	Returns the parametrised equation of the line:
		x=a1+a2t
		y=b1+b2t
		z=c1+c2t
	
	Parameters
	----------
	line: ndarray
		(2,3)

	Returns
	-------
	coeff:(float,float,float,float,float,float)
		(a1,a2,b1,b2,c1,c2)
	'''
	a1,a2=(line[0,0],(-line[0,0]+line[1,0]))
	b1,b2=(line[0,1],(-line[0,1]+line[1,1]))
	c1,c2=(line[0,2],(-line[0,2]+line[1,2]))

	return (a1,a2,b1,b2,c1,c2)


def linesParam(lines:nptyping.NDArray) -> nptyping.NDArray:
	'''
	A vectorised version of lines_param
	Returns a (N,6) numpy array with each row giving the parameterisation of each line
	
	Parameters
	----------
	lines : (N,2,3) numpy array
		List of lines (each line is a (2,3) numpy array)
	
	Returns
	-------
	params: (N,6) numpy array
		Parametrisation of each line
	'''
	params=np.zeros([len(lines),6])
	params[:,0]=lines[:,0,0]
	params[:,1]=-lines[:,0,0]+lines[:,1,0]
	params[:,2]=lines[:,0,1]
	params[:,3]=-lines[:,0,1]+lines[:,1,1]
	params[:,4]=lines[:,0,2]
	params[:,5]=-lines[:,0,2]+lines[:,1,2]

	return params


def planeParam(poly: nptyping.NDArray) -> tuple[float, float, float, float]:
	'''
	Returns the equation of the plane ax+by+cz+d=0 from a poly

	Parameters
	----------
	plane: polygon ((N,3) numpy array with N >= 3)
	
	Returns
	-------
	coeff: (float,float,float,float)
		(a,b,c,d)
	'''
	P_12=unitVector(poly[1,:]-poly[0,:])
	P_13=unitVector(poly[2,:]-poly[0,:])

	normal=unitVector(np.cross(P_12,P_13))

	a=normal[0]
	b=normal[1]
	c=normal[2]
	d=-poly[0,0]*a-poly[0,1]*b-poly[0,2]*c

	return(a,b,c,d)


def planes_param(polys:nptyping.NDArray) -> nptyping.NDArray:
	''' 
	Returns the equation of the plane ax+by+cz+d=0 from many polygons
	
	Parameters
	----------
	polys : {list of N polygons}
	
	Returns
	-------
	params: (N,4) numpy array
		Parameters of the plane for each polygon
	'''
	num_polys,poly_dim,space_dim=polys.shape
	normals=np.cross(polys[:,1,:]-polys[:,0,:],polys[:,2,:]-polys[:,0,:])
	params=np.zeros([len(polys),4])
	params[:,0]=normals[:,0]
	params[:,1]=normals[:,1]
	params[:,2]=normals[:,2]
	if poly_dim>3:
		params[:,3]=-normals[:,0]*polys[:,3,0]-normals[:,1]*polys[:,3,1]-normals[:,2]*polys[:,3,2]
	else:
		params[:,3]=-normals[:,0]*polys[:,2,0]-normals[:,1]*polys[:,2,1]-normals[:,2]*polys[:,2,2]
	return params
		

def is_point_on_plane(point:nptyping.NDArray, coeff:nptyping.NDArray) -> bool:
	'''Test if point in plane
	
	Test if the point is a solution to the equation Ax+By+Cz+D=0
	Where coeff = [A, B, C, D]
	
	Parameters
	----------
	point : {(3,) ndarray}
		
	coeff : {(4,) ndarray}
		Coefficients of 3D plane
	
	Returns
	-------
	bool
	'''
	return np.isclose(coeff[0] * point[0] 
					+ coeff[1] * point[1]
					+ coeff[2] * point[2], -coeff[3])
