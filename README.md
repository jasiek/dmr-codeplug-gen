## dmr-codeplug-gen

Script for generating a codeplug for the AnyTone AT-D878UV.

### How to use?

* Run `make validate` to build the codeplug. This will pull all data files and build a codeplug into `d878uv.conf` and validate it.
* To program into your radio, run `make program`.

### Dependencies

* python 3.11
* [dmrconfig](https://github.com/OpenRTX/dmrconfig)


