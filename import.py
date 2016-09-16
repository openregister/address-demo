#!/usr/bin/env python

# import AddressBase register-shaped files into Mongo

import sys
from config import MONGO_URL
from json import loads
from csv import DictReader
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

register = sys.argv[1]
collection = db[register]

for filename in sys.argv[2:]:
    for doc in DictReader(open(filename), delimiter="\t"):
        doc['point'] = loads(doc['point'])
        collection.insert(doc)
