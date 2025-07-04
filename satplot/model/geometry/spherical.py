import numpy as np
import satplot.util.array_u as array_u

def smallCircleRadius(center_lat: float, center_lon:float, radii_end_lat: float, radii_end_lon: float) -> float:
	'''Calculates the great circle distance between center (lon,lat) and radii_end (lon,lat)

	[description]

	Args:
		center_lat (float): [description]
		center_lon (float): [description]
		radii_end_lat (float): [description]
		radii_end_lon (float): [description]

	Returns:
		float: [description]
	'''
	lat = np.deg2rad(radii_end_lat)
	lat_0 = np.deg2rad(center_lat)
	lon = np.deg2rad(radii_end_lon)
	lon_0 = np.deg2rad(center_lon)
	d = 2*np.arcsin(np.sqrt(np.sin((lat-lat_0)/2)**2+np.cos(lat)*np.cos(lat_0)*np.sin((lon-lon_0)/2)**2))

	return d

def wrapToCircleRange(arr) -> np.ndarray:
	'''Wrap the values in arr between pi,-pi

	Args:
		arr (np.ndarray[n,]):

	Returns:
		ndarray[n,]:
	'''
	return (arr + np.pi) % (2*np.pi) - np.pi

def wrapToCircleRangeDegrees(arr):
	'''Wrap the values in arr between 180,-180

	Args:
		arr (np.ndarray[n,]):

	Returns:
		ndarray[n,]:
	'''
	return (arr + 180) % (2*180) - 180

def getSmallCirclePoint(great_circle_radius:float, center_lat:float, center_lon:float, param_lat:float) -> tuple[float,float]:
	d = great_circle_radius
	phi_0 = np.deg2rad(center_lon)
	theta_0 = np.deg2rad(center_lat)
	theta = np.deg2rad(param_lat)
	s = 2*np.arcsin(np.sqrt((np.sin(d/2)**2-np.sin((theta-theta_0)/2)**2)/(np.cos(theta)*np.cos(theta_0))))
	phi1 = phi_0 + s
	phi2 = phi_0 - s
	lon1 = np.rad2deg(phi1)
	lon2 = np.rad2deg(phi2)
	return lon1, lon2

def genSmallCircleCenterRadii(great_circle_radius:float, center_lat:float, center_lon:float) -> np.ndarray:
	'''Generate lat,lon points around small circle on surface of unit sphere, centered at (center_lat, center_lon)

		Generate lat,lon points around small circle on surface of sphere, centered at (center_lat, center_lon),
		and circle diameter determined by the great circle radius

	Args:
		great_circle_radius (float): great circle distance of radius on unit circle
		center_lat (float): latitude of center
		center_lon (float): longitude of center

	Returns:
		[np.ndarray]: points [lons,lats]
	'''
	d = great_circle_radius
	lats = np.arange(-90,90,0.1)
	lons1,lons2 = getSmallCirclePoint(d,center_lat,center_lon,lats)
	circle = np.vstack((np.hstack((lons1.reshape(-1,1),lats.reshape(-1,1))),
	                    np.flip(np.hstack((lons2.reshape(-1,1),lats.reshape(-1,1))),axis=0)))
	circle = circle[~np.isnan(circle).any(axis=1),:]
	return circle


def genEarthSmallCircle(great_circle_radius:float, center_lat:float, center_lon:float):
	Re = 6371
	d = great_circle_radius/Re

	circle = genSmallCircleCenterRadii(d,center_lat,center_lon)

	return circle

def findSmallCircleLatRange(subtended_angle:float, center_lat:float) -> tuple[float,float]:
	'''Calculate minimum and maximum lattitudes of points in small circle centered at center_lat

		Calculate minimum and maximum lattitudes of points in small circle centered at center_lat (center_lat, xx),
		and circle diameter determined by the solid angle it subtends at the center of the sphere.

	Args:
		subtended_angle (float): angle in degrees
		center_lat (float): latitude of center

	Returns:
		tuple[float,float]: [max, min]
	'''
	lat = np.deg2rad(center_lat)
	radius = np.deg2rad(subtended_angle/2)
	if lat - radius < -np.pi/2:
		lat_min = -np.pi - (lat - radius)
	else:
		lat_min = lat - radius

	if lat + radius > np.pi/2:
		lat_max = np.pi - (lat + radius)
	else:
		lat_max = lat + radius

	return np.rad2deg(lat_max), np.rad2deg(lat_min)

def genSmallCircleCenterSubtendedAngle(subtended_angle:float, center_lat:float, center_lon:float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
	'''Generate lat,lon points around small circle on surface of sphere, centered at (center_lat, center_lon)

		Generate lat,lon points around small circle on surface of sphere, centered at (center_lat, center_lon),
		and circle diameter determined by the solid angle it subtends at the center of the sphere.
		It generates two coordinate sets, one for those points with longitudes greater than the center, one with longitudes
		less than the center.

	Args:
		subtended_angle (float): angle in degrees
		center_lat (float): latitude of center
		center_lon (float): longitude of center

	Returns:
		[np.ndarray, np.ndarray, np.ndarray]: lats, greater_lons, lesser_lons
	'''
	d = np.deg2rad(subtended_angle/2)
	lat_max, lat_min = findSmallCircleLatRange(subtended_angle, center_lat)
	if center_lat < 0 :
		lats = np.linspace(lat_min+0.1,lat_max-0.1,90)
	else:
		lats = np.flip(np.linspace(lat_min+0.1,lat_max-0.1,90))
	lons1 = np.zeros(lats.shape)
	lons2 = np.zeros(lats.shape)
	# for ii, lat in enumerate(lats):
	# 	lons1[ii],lons2[ii] = getSmallCirclePoint(d,center_lat,center_lon,lats[ii])
	lons1,lons2 = getSmallCirclePoint(d,center_lat,center_lon,lats)
	# circle = np.hstack((lons2.reshape(-1,1),np.hstack((lons1.reshape(-1,1),lats.reshape(-1,1)))))
	# circle = np.vstack((np.hstack((lons1.reshape(-1,1),lats.reshape(-1,1))),
	#                     np.flip(np.hstack((lons2.reshape(-1,1),lats.reshape(-1,1))),axis=0)))
	# circle = circle[~np.isnan(circle).any(axis=1),:]

	return lats, lons1, lons2

def splitSmallCirclePatch(center_lon, center_lat, lats, lons1, lons2):
	num_side1_crossings = None
	num_side2_crossings = None
	hemisphere_sign = np.sign(center_lat)
	hemisphere_boundary = hemisphere_sign * 90
	if np.all(lons1>-180) and np.all(lons1<180) and np.all(lons2>-180) and np.all(lons2<180):
		split = False


		if not (abs(lons1[0] - lons1[-1]) < 90) or  not (abs(lons2[0] - lons2[-1]) < 90):
			# gaussian shape which isn't split by map edges
			lons1 = np.hstack((180,180,lons1))
			lats1 = np.hstack((hemisphere_boundary,lats[0], lats))
			lons2 = np.hstack((-180,-180,lons2))
			lats2 = np.hstack((hemisphere_boundary,lats[0], lats))
		else:
			lats1 = lats.copy()
			lats2 = lats.copy()

		circle = np.vstack((np.hstack((lons1.reshape(-1,1),lats1.reshape(-1,1))),
							np.flip(np.hstack((lons2.reshape(-1,1),lats2.reshape(-1,1))),axis=0)))

		return circle, circle
	else:
		split = True
		if (lons1>180).all():
			# all points of right side are to right of edge of map
			num_side1_crossings = 1
		else:
			num_side1_crossings = len(np.where(np.diff(lons1>180))[0])

		if (lons2<-180).all():
			# all points of left side are to left of edge of map
			num_side2_crossings = 1
		else:
			num_side2_crossings = len(np.where(np.diff(lons2<-180))[0])

		if num_side1_crossings == 1 or num_side2_crossings == 1:
			# TODO: ignore those cases were the circle is a circle in 2D (i.e. not a saddle)
			# could test if start and end lons are the same within some threshold.

			# join the two saddle shapes
			diff = abs(lons1[0]-lons2[0])
			lons1 = np.hstack((lons1[0]+(360-diff)/2,lons1[0]+(360-diff)/2,lons1))
			lats1 = np.hstack((hemisphere_boundary,lats[0], lats))
			lons2 = np.hstack((lons2[0]-(360-diff)/2,lons2[0]-(360-diff)/2,lons2))
			lats2 = np.hstack((hemisphere_boundary,lats[0], lats))

		else:
			lats1 = lats.copy()
			lats2 = lats.copy()

		circle = np.vstack((np.hstack((lons1.reshape(-1,1),lats1.reshape(-1,1))),
							np.flip(np.hstack((lons2.reshape(-1,1),lats2.reshape(-1,1))),axis=0)))

		circle1 = circle.copy()
		circle2 = circle.copy()
		if np.any(circle[:,0] > 180):
			circle2[:,0] = (circle[:,0] - 360)

		if np.any(circle[:,0]<-180):
			circle1[:,0] = (circle[:,0] + 360)

	return circle1, circle2