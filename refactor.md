
Base Assets
-----------

Need to standardise and clean up how Assets are drawn

* draw() -> instantiateSubAssets()
* lose compute()
* lose _createOptHelp()
* setVisibility() at asset level
	* set parent, rather than visibile flag

* Asset creation process (for EVERY asset)
	* create asset
		* _initDummyData()
		* _instantiateSubAssets()
		* _createVisuals()
	* setSource()

* timestep rendering
	* updateIndex()
	* recompute()
		* if first draw -> _instantiateSubAssets() & _createVisuals()