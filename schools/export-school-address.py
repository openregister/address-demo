#!/usr/bin/env python

# export matched addresses for ../school-data/maps/school-address.tsv

from config import MONGO_URL
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

fields = ["school", "address", "address-match"]

if __name__ == '__main__':
    items = list(db['school-address'].find())
    schools = iter(sorted(items, key=lambda item: item['school']))
    print("\t".join(fields) + "\n")
    for row in schools:
        print("\t".join([row[field] for field in fields]))
