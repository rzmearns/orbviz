import logging

import typing

import astropy.constants as astroconst

'''
A list of useful constants!

Created by Benjamin Metha
Last updated: September 11 2018
'''

# ######### BODY CONSTANTS ##########
M_EARTH = astroconst.M_earth.value 	# Mass of earth (Kg)
M_SUN = astroconst.M_sun.value 	# Mass of the sun (Kg)
M_MOON = 7.342e22 	# Mass of the sun (Kg)
M_MARS = 6.4171e23 	# Mass of the sun (Kg)
R_SUN = astroconst.R_sun.value / 1000  # Radius of sun (695700 km)
R_EARTH = astroconst.R_earth.value / 1000    # Radius of Earth (6378.1 km)
R_MOON = 1738 	# Radius of the Moon (km)
R_MARS = 3390 	# Radius of Mars (km)
SUN_MIN_ALT = 0 	# Minimum orbital altitude of the sun (km)
EARTH_MIN_ALT = 350 	# Minimum orbital altitude of the earth (km)
MOON_MIN_ALT = 10 	# Minimum orbital altitude of the moon (km)
MARS_MIN_ALT = 200 	# Minimum orbital altitude of mars (km)
G = astroconst.G.value 	# Gravitational constant (SI)
GM_EARTH = astroconst.GM_earth.value 	# Earth standard gravitational parameter (SI)
GM_SUN = astroconst.GM_sun.value 	# Sun standard gravitational parameter (SI)
GM_MOON = 4.9048695e12 	# Moon standard gravitational parameter (SI)
GM_MARS = 4.282837e13 	# Mars standard gravitational parameter (SI)
AU = astroconst.au.value / 1000 	# Earth-Sun avg distance (1.49597871e8 km)
J2 = 1082.6267e-6 	# Earth J2 perturbations (SI)
W_EARTH = 7.29211510e-5 # Rotation rate of Earth rads/sec
# ######### TEMP CONSTANTS ##########
SB_SIGMA = astroconst.sigma_sb.value 	# the Stefan-Boltzmann constant (5.67037442e-8 SI)
T_EARTH = 250     # Temperature of the Earth (K)
T_SUN = 5780    # Temperature of the Sun (K)
T_SPACE = 4       # Temperature of space (K)
SOL_CONST = 1391    # Max. flux of the sun at the earth (W/m^2)
L_SUN     = 3.828e26 # Solar luminosity in watts

# ######### TIME CONSTANTS ##########

DAY_IN_MINS = 24 * 60
HALF_HOUR = 30
SECS_PER_DAY = 24 * 60 * 60
