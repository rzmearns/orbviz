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