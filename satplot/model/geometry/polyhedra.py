import numpy as np
import satplot.model.geometry.primgeom as pg
import scipy.spatial

def calcConeMeshGrid(apex, height, axis, apex_angle_deg, axis_sample=3, r_sample=2, theta_sample=100):
		
	phi = np.deg2rad(apex_angle_deg/2)
	R = height*np.tan(phi)

	e3 = pg.unitVector(np.asarray(axis))

	not_e3 = np.array([1,0,0])
	if(e3 == not_e3).all():
		not_e3 = np.array([0,1,0])
	e1 = pg.unitVector(np.cross(e3, not_e3))
	e2 = pg.unitVector(np.cross(e3, e1))

	t = np.linspace(0,height,axis_sample)
	theta = np.linspace(0, 2*np.pi, theta_sample)
	rsample = np.linspace(0,R,r_sample)
	t2, theta2 = np.meshgrid(t,theta)

	# cone
	X,Y,Z = [apex[i] + t2*e3[i] + (t2*np.tan(phi))*np.cos(theta2)*e1[i] + (t2*np.tan(phi))*np.sin(theta2)*e2[i] for i in [0,1,2]]
	# circle cap
	X2,Y2,Z2 = [apex[i] + e3[i]*height + R*np.sin(theta)*e1[i] + R*np.cos(theta)*e2[i] for i in [0, 1, 2]]
	
	return [X,Y,Z],[X2,Y2,Z2]

def calcConePoints(apex, height, axis, apex_angle_deg, axis_sample=3, theta_sample=30):

	phi = np.deg2rad(apex_angle_deg/2)
	
	
	apex = np.asarray(apex)
	e3 = pg.unitVector(np.asarray(axis))

	not_e3 = np.array([1,0,0])
	if(e3 == not_e3).all():
		not_e3 = np.array([0,1,0])
	e1 = pg.unitVector(np.cross(e3, not_e3))
	e2 = pg.unitVector(np.cross(e3, e1))

	t = np.linspace(0,height,axis_sample)
	theta = np.linspace(0, 2*np.pi, theta_sample)

	print(f"t:{t}")
	print(f"theta:{theta}")
	print(f"phi:{phi}")

	R = height*np.tan(phi)
	coords = t[0]*np.outer(np.cos(theta),e1) + t[0]*np.outer(np.sin(theta),e2)

	for ii in range(1,axis_sample):
		R = t[ii]*np.tan(phi)
		print(f"R:{R}, t[ii]:{t[ii]}")
		new_coords = R*np.outer(np.cos(theta),e1) + R*np.outer(np.sin(theta),e2)
		coords = np.vstack((coords,(t[ii]*e3)+new_coords))

	return np.unique(coords,axis=0)

def calcConeMesh(apex, height, axis, apex_angle_deg, axis_sample=3, theta_sample=30):
	coords = calcConePoints(apex, height, axis, apex_angle_deg, axis_sample=axis_sample, theta_sample=theta_sample)
	hull = scipy.spatial.ConvexHull(coords)

	vertices = hull.points
	faces = hull.simplices

	return vertices.astype('float32'), faces.astype(dtype='uint32')

def calcSphereMeshGrid(center, r):
	R = np.sqrt(r)
	u_angle = np.linspace(0, 2*np.pi, 25)
	v_angle = np.linspace(0, np.pi, 25)
	x = np.outer(R*np.cos(u_angle), R*np.sin(v_angle)) + center[0]
	y = np.outer(R*np.sin(u_angle), R*np.sin(v_angle)) + center[1]
	z = np.outer(R*np.ones(u_angle.shape[0]), R*np.cos(v_angle)) + center[2]
	return [x,y,z]

def calcCylinderMeshGrid(end_point, height, axis, radius, axis_sample=3, r_sample=2, theta_sample=100):	

	R = radius

	e3 = pg.unitVector(np.asarray(axis))

	not_e3 = np.array([1,0,0])
	if(e3 == not_e3).all():
		not_e3 = np.array([0,1,0])
	e1 = pg.unitVector(np.cross(e3, not_e3))
	e2 = pg.unitVector(np.cross(e3, e1))

	t = np.linspace(0,height,axis_sample)
	theta = np.linspace(0, 2*np.pi, theta_sample)
	t2, theta2 = np.meshgrid(t,theta)

	# cone
	X,Y,Z = [end_point[i] + t2*e3[i] + R*np.cos(theta2)*e1[i] + R*np.sin(theta2)*e2[i] for i in [0,1,2]]
	# circle cap 1
	X2,Y2,Z2 = [end_point[i] + R*np.sin(theta)*e1[i] + R*np.cos(theta)*e2[i] for i in [0, 1, 2]]
	# circle cap 2
	X3,Y3,Z3 = [end_point[i] + e3[i]*height + R*np.sin(theta)*e1[i] + R*np.cos(theta)*e2[i] for i in [0, 1, 2]]

	return [X,Y,Z],[X2,Y2,Z2],[X3,Y3,Z3]

def calcCylinderPoints(end_point, height, axis, radius, axis_sample=3, theta_sample=30):

	R = radius
	end_point = np.asarray(end_point)
	e3 = pg.unitVector(np.asarray(axis))

	not_e3 = np.array([1,0,0])
	if(e3 == not_e3).all():
		not_e3 = np.array([0,1,0])
	e1 = pg.unitVector(np.cross(e3, not_e3))
	e2 = pg.unitVector(np.cross(e3, e1))

	print(0,height,axis_sample)
	t = np.linspace(0,height,axis_sample)
	theta = np.linspace(0, 2*np.pi, theta_sample)

	coords = R*np.outer(np.cos(theta),e1) + R*np.outer(np.sin(theta),e2)
	new_coords = coords.copy()

	for ii in range(1,axis_sample):
		coords = np.vstack((coords,(t[ii]* e3)+new_coords))

	coords = np.vstack((end_point, coords+end_point, end_point + height*e3))

	return coords

def calcCylinderMesh(end_point, height, axis, radius, axis_sample=3, theta_sample=30):
	coords = calcCylinderPoints(end_point, height, axis, radius, axis_sample=axis_sample, theta_sample=theta_sample)
	hull = scipy.spatial.ConvexHull(coords)

	vertices = hull.points
	faces = hull.simplices

	return vertices.astype('float32'), faces.astype(dtype='uint32')