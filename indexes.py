#!/usr/bin/env python

from pymongo import MongoClient, GEOSPHERE

mongo_url = 'mongodb://127.0.0.1:27017/addressbase-data'
client = MongoClient(mongo_url)
db = client.get_default_database()

address = db["address"]
address.ensure_index([("point", GEOSPHERE)])
address.ensure_index("name")

street = db["street"]
street.ensure_index([("point", GEOSPHERE)])
street.ensure_index("name")
street.ensure_index("locality")
street.ensure_index("town")
street.ensure_index("administrative-area")
street.ensure_index("street-custodian")
