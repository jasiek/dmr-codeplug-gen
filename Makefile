RECIPE?=poland
PLUGFILE=plug-${RECIPE}.yaml

default:  validate
all: data/radiod_users.json data/brandmeister_talkgroups.json data/rptrs.json

data/radiod_users.json:
	curl -o data/radiod_users.json https://radioid.net/static/users.json

data/brandmeister_talkgroups.json:
	curl -o data/brandmeister_talkgroups.json https://api.brandmeister.network/v2/talkgroup

data/rptrs.json:
	curl -o data/rptrs.json https://radioid.net/static/rptrs.json

${PLUGFILE}: all $(wildcard codeplug/*.py)
	black .
	python codeplug/cli.py ${PLUGFILE} ${CALLSIGN} ${DMRID} ${RECIPE}

validate: ${PLUGFILE}
	dmrconf -y verify ${PLUGFILE}

program: validate
	dmrconf -y write ${PLUGFILE} --device cu.usbmodem0000000100001

lint: $(wildcard codeplug/*.py)
	pylint ./codeplug

clean:
	rm -rf ${PLUGFILE}

distclean: clean
	rm -rf data/*
	rm -rf cache/*
