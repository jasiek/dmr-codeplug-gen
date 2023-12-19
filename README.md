## dmr-codeplug-gen

Script for generating a codeplug for the AnyTone AT-D878UV.

### How to use?

* Run `make validate` to build the codeplug. This will pull all data files and build a codeplug into `d878uv.conf` and validate it.
* To program into your radio, run `make program`.

### Dependencies

* python 3.11
* [dmrconfig](https://github.com/OpenRTX/dmrconfig)

### TODO

* ~~generate a set of digital channels for use with hotspots, given a set of TGs~~
* generate zones of digital repeaters and cluster by locator
* generate zones of digital repeaters and cluster by city
* generate zones of analog repeaters clustered by city
* generate a scanlist of analog repeaters clustered by city
* generate a scanlist of digital repeaters clustered by city
