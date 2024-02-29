Installation
------------
Run the following to install the necessary dependancies

`pip3 install -r requirements.txt`

Execute the following in the root directory of the repo

`python3 application.py`


Demos
-----
Demo data is provided in the .data/directories
* TLEs
	* SpIRIT satellite
	* Iridium NEXT constellation
	* Subset of the Iridium NEXT constellation
	* Swift satellite
	* Thuraya constellation
* Land boundaries for drawing on the earth globe
* Pointing files
	* Example pointing data from SpIRIT (2024-02-23 03:00:00 UTC)
* Spacecraft files
	* Example sensor suite for the SpIRIT spacecraft

Usage
-----
To load data from the selected files, click the 'Recalculate Button'  
The time slider will then activate.  

* Time Slider
	* Click and drag the time slider bar to run to a particular time
	* The extents of the time slider are set by the `Period Start` field, and the length is hardcoded at 90mins for the moment
	* Each tick of the time slider represents one time step in the calculation, this is currently hard coded to 30secs.
	* A particular time can be jumped to, by entering the time in the textbox above the slider (the nearest previous timestep will be selected)

* Camera Controls
	* Click and drag in the display pane to rotate the model
	* Hold `Shift`, and click and drag to pan the model
	* Use the `Home` key to reset the camera to center on the Earth
	* Use the `End` key to center on the spacecraft

* Dispaly Options (IN PROGRESS)
	* All display options (colour, alpha, width, length, size, etc.) should be configurable in the `Visual Options` pane.
	* Assets displayed in the model can be turned on and off via the shown checkboxes
	* The options are listed in a nested tree structure.
	* If an option is not yet active, the console should print a `NotImplemented` error.

* Choosing an orbit
	* Select a TLE file to display using the file picker
		* The TLE file must only have a single TLE for each satellite (i.e. 1 for the primary satellite)

* Selecting a Pointing File
	* The pointing file can be selected using the relevant file picker
	* The timestamp of the period start must be present in the pointing file
	* If the timesteps of the pointing file are not all the same, a warning will be issued
	* If the pointing file is not sufficiently long, or there is bad data for a particular time step, the previous valid pointing data will be used, however, the spacecraft body frame Gizmo (RGB axis), will be shown as all Magenta. The Body Frame Gizmo colour will be restored once good pointing data is present again.
	* The pointing file should be a csv file with the following columns in the following order:
		1. timestamp (Yr-Mon-Day Hr:Min:Sec.Millis)
		2. Quaternion W
		3. Quaternion X
		4. Quaternion Y
		5. Quaternion Z
	* The pointing file is expected to have one header row

* Constellations
	* Currently the constellations are hard coded
	* They can be selected from a drop down list
	* To clear a constellation, set a blank constellation in the drop down list.
	* Large constellations will take up to 2mins for the orbits to be propagated

* Spacecraft Sensor Suite
	* Currently the sensor suite file used is hardcoded as `spirit.json`
	* The sensor suite file is a dictionary describing the sensors in the suite.
	* Two types of sensors are currently encoded:
		* Cone - A cone of specified opening angle, the json fields for this sensor type are as follows:
			* `"shape":"cone"`
			* `"opening_angle":62.2`
			* `"range":550`
			* `"colour":"(52, 235, 198)"`
			* `"bf_quat":"(-0.40860704, -0.40860704, 0.577096542, 0.57709642)"`
		* Square pyramid - A rectangular pyramid of specified width and height opening angles, the json fields for this sensor type are as follows:
			* `"shape":"cone"`
			* `"width_opening_angle":62.2`
			* `"height_opening_angle":48.8`
			* `"range":550`
			* `"colour":"(52, 235, 198)"`
			* `"bf_quat":"(-0.40860704, -0.40860704, 0.577096542, 0.57709642)"`
	* The `bf_quat` field describes the quaternion of the sensor bore-sight axis ('height' direction up) in the spacecraft body frame
	* If pointing is not desired, clear the pointing file textbox and press `tab` or `enter`

