DATA=../addressbase-data/data

all: flake8

#
#  import addressbase-data into Mongo
#  - uses GNU parallel
#
import: import-streets import-addresses import-address-postcodes indexes

import-streets:
	find $(DATA)/street -name \*tsv | parallel -v -n 50 python import.py street

import-addresses:
	find $(DATA)/address -name \*tsv | parallel -v -n 50 python import.py address

import-address-postcodes:
	find $(DATA)/address-postcode -name \*tsv | parallel -v -n 50 python import.py address-postcode

indexes:
	python indexes.py

#
#  run a demo server using data imported into Mongo
#
server:	flake8
	python3 app.py

bower::
	bower install leaflet leaflet-fullscreen turfjs

#
#  python
#
init::
	pip3 install -r requirements.txt

upgrade:
	pip3 install --upgrade -r requirements.txt

flake8::
	flake8 --ignore=E501 .
