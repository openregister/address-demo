#
#  import addressbase-data into Mongo
#  - uses GNU parallel
#
DATA=../addressbase-data/data

all: flake8

import: import-streets import-addresses indexes

import-streets:
	find $(DATA)/street -name \*tsv | parallel -v -n 50 python import.py street

import-addresses:
	find $(DATA)/address -name \*tsv | parallel -v -n 50 python import.py address

indexes:
	python indexes.py

#
#  run a demo server using data imported into Mongo
#
server:
	python3 app.py

#
#  python
#
init::
	pip3 install -r requirements.txt

upgrade:
	pip3 install --upgrade -r requirements.txt

flake8::
	flake8 .
