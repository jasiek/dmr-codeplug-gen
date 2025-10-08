default:  validate
all: data/radiod_users.json data/brandmeister_talkgroups.json data/rptrs.json

data/radiod_users.json:
	curl -o data/radiod_users.json https://radioid.net/static/users.json

data/brandmeister_talkgroups.json:
	curl -o data/brandmeister_talkgroups.json https://api.brandmeister.network/v2/talkgroup

data/rptrs.json:
	curl -o data/rptrs.json https://radioid.net/static/rptrs.json

plug.yaml: all $(wildcard codeplug/*.py)
	black .
	python codeplug/cli.py plug.yaml ${CALLSIGN} ${DMRID} poland

validate: plug.yaml
	dmrconf -y verify plug.yaml

program: validate
	dmrconf -y write plug.yaml --device cu.usbmodem0000000100001

lint: $(wildcard codeplug/*.py)
	pylint ./codeplug

clean:
	rm -rf data/*
	rm -rf cache/*
	rm -rf plug.yaml
