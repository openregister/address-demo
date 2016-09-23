#!/usr/bin/env python

from config import MONGO_DBNAME
import re
import csv
from base32_crockford import decode
from flask import Flask, render_template, Markup
from flask_pymongo import PyMongo
import markdown

app = Flask(__name__)


def llist(s):
    l = list(s)
    for o in l:
        if 'point' in o:
            o['ll'] = [o['point'][1], o['point'][0]]
    return l


def atoi(text):
    return int(text) if text.isdigit() else text


def latest(c):
    l = sorted(list(c), key=lambda e: e['entry-timestamp'], reverse=True)
    return l[0]


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


def street_addresses(usrn):
    addresses = llist(mongo.db.address.find({'street': usrn}))
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


@app.route("/")
def _home():
    # load interesting examples ..
    examples = []
    with open('INTERESTING.tsv') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        for example in reader:
            example['href'] = "/" + example['curie'].replace(":", "/")
            example['content'] = Markup(markdown.markdown(example['text']))
            examples.append(example)

    return render_template("home.html", examples=examples)


@app.route("/street/<usrn>")
def _street(usrn):
    streets = llist(mongo.db.street.find({'street': usrn}))
    street = latest(streets)
    return render_template(
        "street.html",
        street=street,
        streets=streets,
        addresses=street_addresses(usrn))


@app.route("/address/<key>")
def _address(key):
    addresses = llist(mongo.db.address.find({'address': key}))
    address = latest(addresses)

    street = latest(mongo.db.street.find({'street': address['street']}))

    children = sorted_naturally(llist(mongo.db.address.find({'parent-address': key})))
    parents = address_parents(address)
    print(parents)

    addresses = addresses + children + parents

    postcode = mongo.db['address-postcode'].find_one({'address': key})['postcode']

    return render_template("address.html",
                           address=address,
                           addresses=addresses,
                           street=street,
                           postcode=postcode,
                           uprn=decode(key),
                           parents=parents,
                           children=children)


@app.route("/streets/locality/<name>")
def _locality(name):
    return render_template("streets.html", name=name, streets=streets('locality', name.upper()))


@app.route("/streets/town/<name>")
def _town(name):
    return render_template("streets.html", name=name, streets=streets('town', name))


@app.route("/streets/administrative-area/<name>")
def _administrative_area(name):
    return render_template("streets.html", name=name, streets=streets('administrative-area', name))


@app.route("/streets/name/<name>")
def _streets(name):
    return render_template("streets.html", name=name, streets=streets('name', name.upper()))


@app.route("/streets/street-custodian/<key>")
def _street_custodian(key):
    # TBD - pull in register
    street_custodian = {'street-custodian': key}

    return render_template("street_custodian.html",
                           street_custodian=street_custodian,
                           streets=streets('street-custodian', key))


@app.route("/addresses/postcode/<name>")
def _postcode(name):
    return render_template("addresses.html", name=name, addresses=postcode_addresses(name))


#
#  review school addresses
#
def n7e(s):
    s = s.lower()
    s = re.sub('[\'\"]', '', s)
    s = re.sub('[\-]', ' ', s)
    s = re.sub('infants', 'infant', s)
    s = re.sub('junior mixed and infant', ' jmi', s)
    s = re.sub(' c e ', 'cofe', s)
    ignore = ['the', 'school', 'jmi']
    words = [word for word in s.split() if word not in ignore]
    s = ' '.join(words)
    return s


@app.route("/schools")
def _schools():
    # ad-hoc load schools to be reviewed ..
    schools = []
    addresses = []
    byhand = 0
    matches = 0
    with open('schools.tsv') as tsvfile:
        for school in csv.DictReader(tsvfile, delimiter="\t"):
            if 'address' in school:
                if school['address-match'] == "byhand":
                    byhand = byhand + 1
                else:
                    for address in llist(mongo.db.address.find({'address': school['address']})):
                        addresses.append(address)
                        if n7e(school['name']) == n7e(address['name']):
                            school['address-name'] = address['name']
                            school['address'] = address['address']
                            school['address-match'] = 'matched'
                            matches = matches + 1
                            break
            if 'address' in school and 'address-name' not in school and school['address']:
                a = latest(mongo.db.address.find({'address': school['address']}))
                school['address-name'] = a['name']
            schools.append(school)

    return render_template("schools.html", schools=sorted_naturally(schools), addresses=addresses, matches=matches, byhand=byhand)


if __name__ == "__main__":
    app.debug = True
    app.config['MONGO_DBNAME'] = MONGO_DBNAME
    mongo = PyMongo(app)
    app.run()
