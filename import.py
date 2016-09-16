#!/usr/bin/env python

# import AddressBase register-shaped files into Mongo

import sys
from json import loads
from csv import DictReader
from pymongo import MongoClient

mongo_url = 'mongodb://127.0.0.1:27017/addressbase-data'
client = MongoClient(mongo_url)
db = client.get_default_database()

register = sys.argv[1]
collection = db[register]

for filename in sys.argv[2:]:
    for doc in DictReader(open(filename), delimiter="\t"):
        doc['point'] = loads(doc['point'])
        collection.insert(doc)
