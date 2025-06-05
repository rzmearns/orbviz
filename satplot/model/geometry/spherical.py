import numpy as np

def smallCircleRadius(center_lat: float, center_lon:float, radii_end_lat: float, radii_end_lon: float) -> float:
	lat = np.deg2rad(radii_end_lat)
	lat_0 = np.deg2rad(center_lat)
	lon = np.deg2rad(radii_end_lon)
	lon_0 = np.deg2rad(center_lon)
	d = 2*np.arcsin(np.sqrt(np.sin((lat-lat_0)/2)**2+np.cos(lat)*np.cos(lat_0)*np.sin((lon-lon_0)/2)**2))

	return d

def wrapToCircleRange(arr):
	return (arr + np.pi) % (2*np.pi) - np.pi

def getSmallCirclePoint(great_circle_radius:float, center_lat:float, center_lon:float, param_lat:float) -> tuple[float,float]:
	d = great_circle_radius
	phi_0 = np.deg2rad(center_lon)
	theta_0 = np.deg2rad(center_lat)
	theta = np.deg2rad(param_lat)
	s = 2*np.arcsin(np.sqrt((np.sin(d/2)**2-np.sin((theta-theta_0)/2)**2)/(np.cos(theta)*np.cos(theta_0))))
	# phi1 = wrapToCircleRange(phi_0 + s)
	# phi2 = wrapToCircleRange(phi_0 - s)
	phi1 = phi_0 + s
	phi2 = phi_0 - s
	lon1 = np.rad2deg(phi1)
	lon2 = np.rad2deg(phi2)
	return lon1, lon2

def genSmallCircleCenterRadii(great_circle_radius:float, center_lat:float, center_lon:float):
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

def findSmallCircleLatRange(subtended_angle:float, center_lat:float):
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

def genSmallCircleCenterSubtendedAngle(subtended_angle:float, center_lat:float, center_lon:float):
	d = np.deg2rad(subtended_angle/2)
	lat_max, lat_min = findSmallCircleLatRange(subtended_angle, center_lat)
	if center_lat < 0 :
		lats = np.linspace(lat_min+0.1,lat_max-0.1,180)
	else:
		lats = np.flip(np.linspace(lat_min+0.1,lat_max-0.1,180))
	lons1 = np.zeros(lats.shape)
	lons2 = np.zeros(lats.shape)
	# for ii, lat in enumerate(lats):
	# 	lons1[ii],lons2[ii] = getSmallCirclePoint(d,center_lat,center_lon,lats[ii])
	lons1,lons2 = getSmallCirclePoint(d,center_lat,center_lon,lats)
	# circle = np.hstack((lons2.reshape(-1,1),np.hstack((lons1.reshape(-1,1),lats.reshape(-1,1)))))
	circle = np.vstack((np.hstack((lons1.reshape(-1,1),lats.reshape(-1,1))),
	                    np.flip(np.hstack((lons2.reshape(-1,1),lats.reshape(-1,1))),axis=0)))
	# circle = circle[~np.isnan(circle).any(axis=1),:]

	return lats, lons1, lons2
