import numpy as np
import satplot.model.geometry.primgeom as pg

def generateCircle(center, radius, normal, sampling=180):
	coords = np.zeros((sampling,3))
	theta = np.linspace(0, 2*np.pi, 180)
	center = np.asarray(center)
	e1,e2,e3 = pg.generateONBasisFromPointNormal(center, normal)
	for ii in range(3):
		coords[:,ii] = radius*np.cos(theta)*e1[ii] + radius*np.sin(theta)*e2[ii] + np.zeros(180)*e3[ii]

	return coords + center