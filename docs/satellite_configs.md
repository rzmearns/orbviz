## Primary Satellite configs
```
{
	"name": "<Satellite Display Name>",
	"sensor_suites":[<sensor suite 1 json filename>, <sensor suite 2 json filename>],
	"satellites":{
		"<NORAD Name>": <NORAD Catalog ID>
	}
}
```

## Constellation configs
```
{
	"name": "<Constellation Display Name>",
	"beam_width": <float, full beam width angle for earth pointing beam>,
	"satellites":{
		"<NORAD Name>": <NORAD Catalog ID>,
		"<NORAD Name>": <NORAD Catalog ID>,
		"<NORAD Name>": <NORAD Catalog ID>
	}
}
```