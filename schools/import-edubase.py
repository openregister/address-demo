#!/usr/bin/env python

# import edubase CSV into Mongo

from config import MONGO_URL
from csv import DictReader
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

filename = '../../school-data/cache/edubase.csv'
collection = db['edubase']

for doc in DictReader(open(filename)):
    collection.insert(doc)

collection.ensure_index('URN')
collection.ensure_index('LA (code)')
