all: data/radiod_users.json data/brandmeister_talkgroups.json data/pl_2m_fm.xml data/pl_70cm_fm.xml

data/radiod_users.json:
	curl -o data/radiod_users.json https://radioid.net/static/users.json

data/brandmeister_talkgroups.json:
	curl -o data/brandmeister_talkgroups.json https://api.brandmeister.network/v2/talkgroup

data/pl_2m_fm.xml:
	curl -o data/pl_2m_fm.xml "https://przemienniki.net/export/rxf.xml?country=pl&band=2M&mode=FM&status=working"

data/pl_70cm_fm.xml:
	curl -o data/pl_70cm_fm.xml "https://przemienniki.net/export/rxf.xml?country=pl&band=70CM&mode=FM&status=working"
