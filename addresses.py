#!/usr/bin/env python

import re
from flask_pymongo import PyMongo

mongo = PyMongo()


def llist(s):
    l = list(s)
    for o in l:
        if 'point' in o:
            o['ll'] = [o['point'][1], o['point'][0]]
    return l


def atoi(text):
    return int(text) if text.isdigit() else text


def latest(c):
    if not c:
        return None
    l = list(c)
    if len(l) < 1:
        return None
    return sorted(l, key=lambda e: e['entry-timestamp'], reverse=True)[0]


def natural_keys(item):
    text = item['name']
    return [atoi(c) for c in re.split('(\d+)', text)]


def sorted_naturally(items):
    return sorted(items, key=natural_keys)


def sorted_by_name(items):
    return sorted(items, key=lambda item: item['name'])


def streets(field, name):
    streets = llist(mongo.db.street.find({field: name}))
    return sorted_by_name(streets)


def addresses(field, value):
    addresses = llist(mongo.db.address.find({field: value}))
    return sorted_naturally(addresses)


def address_parents(address):
    parents = []
    while address['parent-address']:
        address = latest(llist(mongo.db.address.find({'address': address['parent-address']})))
        parents.append(address)
    return parents


def postcode_addresses(postcode):
    addresses = []
    for a in list(mongo.db['address-postcode'].find({'postcode': postcode})):
        addresses = addresses + llist(mongo.db.address.find({'address': a['address']}))
    return addresses
