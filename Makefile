default: validate
all: data/radiod_users.json data/brandmeister_talkgroups.json data/pl_2m_fm.xml data/pl_70cm_fm.xml data/bm_2602.json data/rptrs.json

data/radiod_users.json:
	curl -o data/radiod_users.json https://radioid.net/static/users.json

data/brandmeister_talkgroups.json:
	curl -o data/brandmeister_talkgroups.json https://api.brandmeister.network/v2/talkgroup

data/pl_2m_fm.xml:
	curl -o data/pl_2m_fm.xml "https://przemienniki.net/export/rxf.xml?country=pl&band=2M&mode=FM&status=working"

data/pl_70cm_fm.xml:
	curl -o data/pl_70cm_fm.xml "https://przemienniki.net/export/rxf.xml?country=pl&band=70CM&mode=FM&status=working"

data/bm_2602.json:
	curl -o data/bm_2602.json "https://api.brandmeister.network/v2/device/byMaster/2602"

data/rptrs.json:
	curl -o data/rptrs.json https://radioid.net/static/rptrs.json

plug.yaml: all $(wildcard codeplug/*.py)
	black .
	python codeplug/cli.py plug.yaml ${CALLSIGN} ${DMRID}

validate: plug.yaml
	dmrconf -y verify plug.yaml

program: validate
	dmrconf -y write plug.yaml

lint: $(wildcard codeplug/*.py)
	pylint ./codeplug

