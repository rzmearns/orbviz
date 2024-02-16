import numpy as np
import satplot.model.geometry.primgeom as pg


def calcCone(apex, height, axis, apex_angle_deg, axis_sample=3, r_sample=2, theta_sample=100):
		
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

def calcSphere(center, r):
	R = np.sqrt(r)
	u_angle = np.linspace(0, 2*np.pi, 25)
	v_angle = np.linspace(0, np.pi, 25)
	x = np.outer(R*np.cos(u_angle), R*np.sin(v_angle)) + center[0]
	y = np.outer(R*np.sin(u_angle), R*np.sin(v_angle)) + center[1]
	z = np.outer(R*np.ones(u_angle.shape[0]), R*np.cos(v_angle)) + center[2]
	return [x,y,z]

def calcCylinder():
	shadow_point = -self.sun_dist * pg.unitVector(self.orbit.sun[self.curr_index])

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