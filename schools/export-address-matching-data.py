#!/usr/bin/env python

# export matched edubase addresses for the address-matching-data repository

import re
from config import MONGO_URL
from pymongo import MongoClient

client = MongoClient(MONGO_URL)
db = client.get_default_database()

address_fields = ["Street", "Locality", "Address3", "Town", "County (name)"]
fields = ["test", "address", "name", "text", "postcode"]
sep = "\t"

if __name__ == '__main__':

    print(sep.join(fields))

    for matched in db['school-address'].find({'$query': {}, '$orderby': {'school': 1}}):

        if matched.get('address', ''):
            row = db['edubase'].find_one({'URN': matched['school']})

            if row and row['URN']:
                item = {}
                item['test'] = "school:" + row['URN']
                item['address'] = matched['address']
                item['name'] = row['EstablishmentName']

                item['text'] = ",".join([row[field] for field in address_fields])
                item['text'] = re.sub(",+", ", ", item['text'])

                item['postcode'] = row['Postcode']

                print("\t".join([item[field] for field in fields]))
