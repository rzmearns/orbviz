- Using astropy based conversion from eci to ecf is slower than rotating by sidereal time
	- but yields different lat lons for projected pixels
	- using `data/primary_configs/SpIRIT_XYNegZ.json` and `data/primary_configs/SpIRIT_XYNegZ.json` as input data
	
## Equatorial data set
- computing lats and lons for `Axes:Z` @ 2024-01-08 01:56:15 using both methods
- no points satisfy np.isclose
- Distance
	- in 2D lat, lon space
		- mean: 0.0278
		- std: 0.00486
	- in 2D pixel space (x5.68334)
		- mean: 0.0362
		- std: 0.00985
	- -> less than 1 pixel error
	- ![Pixel Space Error Axes:Z Equatorial](pixel_space_err-20240108-015615.png)
	- points in plot do not represent pixel sizes

## South pole data set
- computing lats and lons for `Axes:Z` @ 2024-01-08 01:56:15 using both methods
- no points satisfy np.isclose
- Distance
	- in 2D lat, lon space
		- mean: 0.0443
		- std: 0.0272
	- in 2D pixel space (x5.68334)
		- mean: 0.0892
		- std: 0.0397
	- -> less than 1 pixel error
	- ![Pixel Space Error Axes:Z South Pole](pixel_space_err-20240108-004445.png)
	- points in plot do not represent pixel sizes
	
## North pole data set
- computing lats and lons for `Axes:Z` @ 2024-01-08 02:18:45 using both methods
- no points satisfy np.isclose
- Distance
	- in 2D lat, lon space
		- mean: 0.0486
		- std: 0.0322
	- in 2D pixel space (x5.68334)
		- mean: 0.0939
		- std: 0.0434
	- -> less than 1 pixel error
	- ![Pixel Space Error Axes:Z North Pole](pixel_space_err-20240108-021845.png)
	- points in plot do not represent pixel sizes
	

- => No issue using faster sidereal rotation
- Is it altitude dependant?
	- angle difference betweeen true and false is on order of 0.3 deg
	- => some altitude dependance