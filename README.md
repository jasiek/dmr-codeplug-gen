## dmr-codeplug-gen

Script for generating a codeplug for the AnyTone AT-D878UV and other radios supported by [qdmr](https://github.com/hmatuschek/qdmr).

### How to use?

* `poetry install`
* `poetry shell`
* Run `make` to build the codeplug. This will pull all data files and build a codeplug into `plug.yml`.

### Dependencies

* python 3.11
* [qdmr](https://github.com/hmatuschek/qdmr)

### TODO

* ~~generate a set of digital channels for use with hotspots, given a set of TGs~~
* generate zones of digital repeaters and cluster by locator
* ~~generate zones of digital repeaters and cluster by prefix~~
* ~~generate zones of analog repeaters clustered by prefix~~
* generate a scanlist of analog repeaters clustered by prefix
* generate a scanlist of digital repeaters clustered by prefix
