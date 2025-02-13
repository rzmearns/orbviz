

# constellation_config
# constellation_name
# constellation_beam_angle


class ConstellationData():
	def __init__(self, timespan, constellation_config, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.timespan = timespan
		self.updateConfig('data_type', DataType.CONSTELLATION)
		# initialise empty config
		self.updateConfig('timespan_period_start', None)
		self.updateConfig('timespan_period_end', None)
		self.updateConfig('sampling_period', None)
		self.updateConfig('pointing_defines_timespan', False)
		self.updateConfig('primary_satellite_ids', None) # keys of orbits, position dict
		self.updateConfig('has_supplemental_constellation', False)
		self.updateConfig('num_geolocations', 0)
		self.updateConfig('is_pointing_defined', False)
		self.updateConfig('pointing_file', None)
		self.updateConfig('pointing_invert_transform', False)

		self.timespan = None
		self.orbits = {}
		self.pointings = {}
		self.constellation = None
		self.sun = None
		self.moon = None
		self.geo_locations = []