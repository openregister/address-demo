#!/usr/bin/env python

from config import MONGO_URL
from pymongo import MongoClient, GEOSPHERE

client = MongoClient(MONGO_URL)
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
