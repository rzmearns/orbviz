# Architecture
This document describes the high-level architecture of SatPlot. If you want to familiarise yourself with the code base, this is a good place to start.

## Concept
TODO: High level description

## Code Map
This section talks briefly about various important directories and data structures. Pay attention to the Architecture Invariant sections. They often talk about things which are deliberately absent in the source code.

satplot  
├── [data](#data)  
├── [resources](#resources)  
└── satplot  
&emsp;&emsp;&emsp;├── [model](#satplotmodel)  
&emsp;&emsp;&emsp;└── [visualiser](#satplotvisualiser)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;├── [assets](#satplotvisualiserassets)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;├── [contexts](#satplotvisualisercontexts)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;│&emsp;&emsp;&emsp;└── [canvaswrappers](#satplotvisualisercontextscanvaswrappers)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;└── [controls](#satplotvisualisercontrols)  


### `data`
This directory stores user data.   
Currently contains:
  - pointing - files describing a time-series of pointing of a spacecraft
  - saves - save files of satplot
  - spacecraft - files describing a spacecraft; sensor suite descriptions, mesh models, etc.
  - TLEs - TLE files sourced from celestrak

### `resources`
This directory stores resources used by satplot. e.g. icon images, data for continent boundaries, etc.

### `satplot/model`
This module encompasses the data structures used to capture the physical behaviour over time.

### `satplot/visualiser`
This module encompasses the necessary gui and visualisation code

### `satplot/visualiser/assets`
Assets are written using `vispy` and follow a defined API to allow contexts to re-use them.

### `satplot/visualiser/contexts`
Contexts are a combination of a visualisation and user controls, forming a separate 'tab' of the SatPlot application

### `satplot/visualiser/contexts/canvaswrappers`
A canvas wrapper is the `vispy` `scene` which is used to render the assets to the screen. They follow a suggest API to allow a context to utilise them in a defined way. However, as there is a 1-to-1 mapping of a canvaswrapper to a context, there is freedom (and this is sometimes necessar) to hard-code behaviour specific to that context.

### `satplot/visualiser/controls`
This module encompasses QT5 based controls, these can be re-used by any context.

## Saving & Loading
capturing the context, data, settings, etc. Essentially a 'snapshot' of satplot

## Context Structure

## Asset Structure
All SatPlot assets inherit from one of:
  - `base.BaseAsset`
  - `base.SimpleAsset`

BaseAssets are assets which may contain both `vispy` `visuals` as well as their own sub-assets.  
SimpleAssets may only contain `vispy` `visuals`

The asset instantiation process and rendering is as follows:
```
                   ┌───────────────────────────┐
                   │  *Create Asset            │
                   │      _initData()          │
                   │      _instantiateAssets() │
                   │      _createVisuals()     │
                   │      setSource()          │
                   └─────────────┬─────────────┘
                                 │
                 ┌───────────────┴───────────────┬──────────────────────────┐
                 │                               │                          │
                 ▼                               ▼                          │
   ┌───────────────────────────┐   ┌───────────────────────────┐            │
   │   *Populate Data          │   │   *Create Visuals         │            │
   │       setSource()         │   │       _instantiateAssets()│            │
   │                           │   │       _createVisuals()    │            │
   │                           │   │                           │            │
   └─────────────┬─────────────┘   └─────────────┬─────────────┘            │
                 │                               │               ┌──────────┴──────────┐
                 └───────────────┬───────────────┘               │   if first_draw     │
                                 │                               │                     │
                                 ▼                               │                     │
                   ┌───────────────────────────┐                 └─────────────────────┘
                   │  *Timestep Rendering      │                            ▲ 
                   │      updateIndex()        │                            │ 
                   │      recompute()          ├────────────────────────────┘ 
                   │                           │
                   │                           │
                   └───────────────────────────┘
```


#### BaseAsset API
##### Properties
- data - a dictionary containing all data necessary for this asset
	- mandatory fields are:
		- name - a string for tracking the asset
		- v_parent - the `vispy` parent `visual`
		- curr_index - the current time index of the visual
- opts - a dictionary storing the current option data for the asset
- assets - a dictionary of sub-assets
- visuals - a dictionary of `vispy` visuals
- first_draw - a boolean flag to indicate this is the first drawing since being re-instantiated
- requires_recompute - a boolean flag to indicate that the underlying data has changed, and so the rendered object is stale
##### Methods
- attachToParentView() 
	- sets all nested assets and visuals to use `data['v_parent']`
- detachFromParentView() 
- sets all nested assets and visuals to use None for the parent
- setParentView(view) 
	- sets `data['v_parent']` to `view`
- setVisibility(state) 
	- sets whether all nested assets and visuals are drawn to the screen
- setFirstDrawFlag() 
	- sets the first_draw flag to `True`
- setSource(*args)
	- ABSTRACT
	- populates `data` dictionary as required for this asset
	- called when data is loaded into a context.
- _initData() 
	- ABSTRACT 
	- Called to initialise the data used for drawing this asset
- _instantiateAssets() 
	- ABSTRACT 
	- Create child assets
- _createVisuals() 
	- ABSTRACT 
	- Create any visuals belonging to this asset (not sub-assets)
- _setDefaultOptions() 
	- ABSTRACT 
	- Create default option dictionary, should copy default dictionary into active dictionary
- recompute() 
	- ABSTRACT 
	- Called at each timestep update of the `canvaswrapper`, see `base.BaseAsset` for how to write the overriding function
- updateIndex() 
	- Called when the `canvaswrapper` timestep index is updated. Should set `requires_recompute` when called. See `base.BaseAsset` for how to write an overriding function if necessary.
- childAssetsRecompute()
	- iterates through child assets and recomputes
- getScreenMouseOverInfo()
	- called when mouse is over object
	- Returns: list of screen positions, list of world positions, list of strings for visual

#### SimpleAsset API
##### Properties
- data - a dictionary containing all data necessary for this asset
	- mandatory fields are:
		- name - a string for tracking the asset
		- v_parent - the `vispy` parent `visual`
		- curr_index - the current time index of the visual
- opts - a dictionary storing the current option data for the asset
- visuals - a dictionary of `vispy` visuals
- first_draw - a boolean flag to indicate this is the first drawing since being re-instantiated
- requires_recompute - a boolean flag to indicate that the underlying data has changed, and so the rendered object is stale
##### Methods
- attachToParentView() 
	- sets all nested assets and visuals to use `data['v_parent']`
- detachFromParentView() 
- sets all nested assets and visuals to use None for the parent
- setParentView(view) 
	- sets `data['v_parent']` to `view`
- setVisibility(state) 
	- sets whether all nested assets and visuals are drawn to the screen
- setFirstDrawFlag() 
	- sets the first_draw flag to `True`
- _initData() 
	- ABSTRACT 
	- Called to initialise the data used for drawing this asset
- _createVisuals() 
	- ABSTRACT 
	- Create any visuals belonging to this asset (not sub-assets)
- _setDefaultOptions() 
	- ABSTRACT 
	- Create default option dictionary, should copy default dictionary into active dictionary
- setTransform(pos=(0,0,0), rotation=np.eye(3)) 
	- ABSTRACT 
	- Used to apply an affine transformation to a `vispy` `visual`

### Options

## Controls Structure