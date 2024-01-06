## dmr-codeplug-gen

Script for generating a codeplug for the AnyTone AT-D878UV and other radios supported by [qdmr](https://github.com/hmatuschek/qdmr).

### How to use?

* define the env variable CALLSIGN as your callsign
* define the env variable DMRID as your DMR ID (radioid.net)
* `poetry install`
* `poetry shell`
* Run `make` to build the codeplug. This will pull all data files and build a codeplug into `plug.yaml`.

### Dependencies

* python 3.11
* [qdmr](https://github.com/hmatuschek/qdmr)

### TODO

- scanlists
- gps roaming
- plug for the uk
