#!/usr/bin/env python

# import AddressBase register-shaped files into Mongo

from sys import argv
from os import path
from config import MONGO_URL
from json import loads
from csv import DictReader
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

register = argv[1]
collection = db[register]

for filename in argv[2:]:
    source = path.splitext(path.basename(filename))[0]
    for doc in DictReader(open(filename), delimiter="\t"):
        doc['source'] = source
        if 'point' in doc:
            doc['point'] = loads(doc['point'])
        collection.insert(doc)
