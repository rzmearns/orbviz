## Installation

Installation should be done using a virtual environment to avoid conflicts with other python packages.   
This program must use python3.10 - other versions have not been tested.

Setup and activate a virtual environment with the name `<env_name>` like so:

```
python3.10 -m venv ./<env_name>/ 
source ./<env_name>/bin/activate
```

Then install the necessary dependancies

```
pip install -r requirements.txt
```

## Running

Execute the following in the root directory of the repo to start Satplot.

```
python3 application.py
```

### Debugging
stderr is displayed on the in program console. If the program crashes (so stderr is no longer visible) or access to stderr outside the program is desired, start with the `--debug` flag

### Problems Getting Satplot to Run
As Satplot uses python apis to the OpenGL language, sometimes it is necessary to fine tune access to OpenGL and your computers graphics card depending on your hardware.  

Some common problems:

* If the program doesn't show the Earth on initial startup, try running with reduced GL parallisation support
  * This may cause the program to lag if rendering large constellations.

```
python3 application.py --nogl+
```

* If the above doesn't work, and you are running satplot on a wayland based linux distro (rather than X11), try the following:
```
export QT_QPA_PLATFORM=wayland
```


## Satplot Demos

Demo data is provided in the `data` directories

- Satellite configs
  - SpIRIT Satellite
    - `data/primary_configs/SpIRIT.json`
  - Iridium NEXT constellation
    - `data/constellation_configs/Iridium_NEXT.json`
  - Swift satellite
    - `data/constellation_configs/Swift.json`
- Pointing files
  - Example pointing data from SpIRIT
    - `data/pointing/2024-02-23 03:00:00 UTC`
- Sensor suite files
  - Example sensor suite for the SpIRIT spacecraft
  - `data/spacecraft/spirit.json`
  

## Usage

To load data for the selected satellite (and constellation), click the 'Recalculate Button'  
The time slider will activate once the orbits have finished propagating.

- Time Slider
  - Click and drag the time slider bar to update to a particular time
  - Type the desired time in the fields above the time slider
    - The time slider will adjust to the closest time sample
  - The extents of the time slider are set by the `Period Start` and `Period End` fields
  - The time slider increment is set by the `Sampling Period` field
  - A particular time can be jumped to, by entering the time in the textbox above the slider (the nearest previous timestep will be selected)
  - Hotkeys are available to control the time slider
    - `Pg Up` - Decrement the current time (into the past)
    - `Pg Down` - Increment the current time (into the future)
    - `Home` - Go to the `Period Start`
    - `End` - Go to the `Period End`

- Camera Controls
  - Click and drag in the display pane to rotate the model
  - Hold `Shift`, and click and drag to pan the model
  - Use the ![image](resources/icons/camera-earth.png) toolbar button or `Camera->Center on Earth` menu option to reset the camera to center on the Earth
  - Use the ![image](resources/icons/camera-satellite.png) toolbar button or `Camera->Center on Spacecraft` menu option to stay centered on the spacecraft at each timestep.
    - This option is toggelable.
    - Centering the camera on the Earth will reset this option
    - The spacecraft will remain in the center as `Pg Up` or `Pg Down` are pressed

- Display Options (IN PROGRESS)
  - All display options (colour, alpha, width, length, size, etc.) should be configurable in the `Visual Options` tab.
  - Assets displayed in the model can be turned on and off via the shown checkboxes
  - The options are listed in a nested tree structure.
  - If an option is not yet active, the console should print a `NotImplemented` error.

- Choosing an orbit
  - Select a satellite to display using the file picker
    - The satellite configuration file must be constructed according to the format described in `docs/satellite_configs.md`

- Selecting a Pointing File
  - Enable the use of a pointing file
  - The pointing file can then be selected using the file picker
  - The period times can be derived automatically from the pointing file, select the checkbox if desired
  - Otherwise:
    - The timestamp of the period start must be present in the pointing file
  - If the delta between timesteps of the pointing file are not all the same, a warning will be issued
  - If the pointing file is not sufficiently long, or there is bad data for a particular time step, the previous valid pointing data will be used, however, the spacecraft body frame Gizmo (RGB axis), will be shown as all Magenta. The Body Frame Gizmo colour will be restored once good pointing data is present again.
  - The pointing file should be a csv file with the following columns in the following order:
    1. timestamp (Yr-Mon-Day Hr:Min:Sec.Millis)
    2. Quaternion W
    3. Quaternion X
    4. Quaternion Y
    5. Quaternion Z
  - The pointing file is expected to have one header row

- Constellations
  - Enable the simulation of an additional constellation
  - The selection of constellations are populated using the files present in `data/constellation_configs/`
  - A new constellation can be included as a `.json` following the format described in `docs/satellite_configs.md`
  - Large constellations can take a long time for the orbits to be propagated, especially if there are many timesteps.

- Spacecraft Sensor Suite
  - Currently the sensor suite file used is hardcoded as `spirit.json`
  - The sensor suite file is a dictionary describing the sensors in the suite.
  - Two types of sensors are currently encoded:
    - Cone - A cone of specified opening angle, the json fields for this sensor type are as follows:
      - `"shape":"cone"`
      - `"opening_angle":62.2`
      - `"range":550`
      - `"colour":"(52, 235, 198)"`
      - `"bf_quat":"(-0.40860704, -0.40860704, 0.577096542, 0.57709642)"`
    - Square pyramid - A rectangular pyramid of specified width and height opening angles, the json fields for this sensor type are as follows:
      - `"shape":"cone"`
      - `"width_opening_angle":62.2`
      - `"height_opening_angle":48.8`
      - `"range":550`
      - `"colour":"(52, 235, 198)"`
      - `"bf_quat":"(-0.40860704, -0.40860704, 0.577096542, 0.57709642)"`
  - The `bf_quat` field describes the quaternion of the sensor bore-sight axis ('height' direction up) in the spacecraft body frame
  - If pointing is not desired, clear the pointing file textbox and press `tab` or `enter`


## Fetching TLE Data
In order to calculate the position of a satellite at any given time, Satplot requires [TLE information](https://en.wikipedia.org/wiki/Two-line_element_set) for each satellite which is accurate for the given time period.  
TLE data can be obtained from either [Celestrak](https://celestrak.org/) or [Spacetrack](https://www.space-track.org/). Celestrak holds only the most recent TLE data for each satellite, while Spacetrack will provide historical TLE data. Satplot will fall back to using Celestrak if it cannot authenticate access to Spacetrack.  
In order to use Spacetrack, you must provide your [Spacetrack credentials](https://www.space-track.org/auth/createAccount) to satplot. These can be entered from a dialog, using either the ![image](resources/icons/spacetrak-unlock.png) icon or through the `Spacetrack > Enter Credentials` menu option.  
*If the 'Save Credentials Locally' option is checked, satplot will store your credentials locally, as a binary pickle file, data/spacetrack/.credentials, this is not cryptographically secure* 


## Contributing
Please read the `CONTRIBUTING.md` guide, and the `ARCHITECTURE.md` guide.

## Saving
The current Satplot program state can be saved and loaded
* Use the ![image](resources/icons/disk-black.png) toolbar button or `File->Save State` menu option

If the state has not been saved while Satplot has been open, a `Save As` dialog will open, allowing the file to be chosen.  
If the state has previously been saved while Satplot has been open, the last saved filename will be used by both the ![image](resources/icons/disk-black.png) toolbar button or `File->Save State` menu option.  
To save as a new filename, use the `File->Save State As..` menu option.

* To load a state, use the ![image](resources/icons/folder-horizontal-open.png) toolbar button or `File->Load State` menu option

The following information is saved in a satplot state:
* propagated satellite information
  * position
  * velocity
  * time periods
* satellite pointing information
* propagated constellation information

Saving states is particularly useful for large time period simulations, allowing you to forego the TLE update and propagation steps, or for sharing simulations.