#!/usr/bin/env python

# import school addresses into Mongo

from config import MONGO_URL
from csv import DictReader
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

filename = 'schools.tsv'
collection = db['school-address']

for doc in DictReader(open(filename), delimiter='\t'):
    collection.insert(doc)

collection.ensure_index('URN')
