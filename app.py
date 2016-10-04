#!/usr/bin/env python

from config import MONGO_DBNAME
import re
import csv
from base32_crockford import encode, decode
from flask import Flask, render_template, Markup, redirect, request, make_response
from flask_pymongo import PyMongo
from bson.son import SON
import markdown
from io import StringIO

import pyproj
osgb36 = pyproj.Proj("+init=EPSG:27700")
wgs84 = pyproj.Proj("+init=EPSG:4326")


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
    if not c:
        return []
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
        addresses=addresses('street', usrn))


@app.route("/address/<key>")
def _address(key):
    addresses = llist(mongo.db.address.find({'address': key}))
    address = latest(addresses)

    street = latest(mongo.db.street.find({'street': address['street']}))

    children = sorted_naturally(llist(mongo.db.address.find({'parent-address': key})))
    parents = address_parents(address)

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


@app.route("/uprn/<uprn>")
def uprn(uprn):
    return redirect("/address/" + encode(uprn), 301)


@app.route("/streets/locality/<name>")
def _locality(name):
    return render_template("streets.html", name=name, streets=streets('locality', name.upper()))


@app.route("/streets/town/<name>")
def _town(name):
    return render_template("streets.html", name=name, streets=streets('town', name.upper()))


@app.route("/streets/administrative-area/<name>")
def _administrative_area(name):
    return render_template("streets.html", name=name, streets=streets('administrative-area', name.upper()))


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


@app.route("/addresses/name/<name>")
def _addresses_name(name):
    return render_template("addresses.html", name=name, addresses=addresses('name', name.upper()))


@app.route("/addresses/postcode/<name>")
def _postcode(name):
    addresses = llist(mongo.db.address.find({'name': name}))
    return render_template("addresses.html", name=name, addresses=addresses)


#
#  review school addresses
#
def n7e(s, ignore=None):
    s = s.lower()
    s = re.sub('[\'\"]', '', s)
    s = re.sub('[/\-]', ' ', s)
    s = re.sub('infants', 'infant', s)
    s = re.sub('junior mixed and infant', ' jmi', s)
    s = re.sub(' c e ', 'cofe', s)
    if not ignore:
        ignore = ['the', 'school', 'jmi', 'former']
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
    for school in mongo.db['school-address'].find():
        edubase = mongo.db['edubase'].find_one({'URN': school['school-eng']})
        if edubase is not None:
            school['name'] = edubase['EstablishmentName']
        if 'address' in school:
            if ';' in school['address']:
                school['address'] = school['address'].split(';')[0]
            if school.get('address-match', '') == "byhand":
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


@app.route("/schools.tsv")
def _schools_tsv():
    # for school in mongo.db['school-address'].find():

    fields = ["school-eng", "address", "address-match"]
    items = list(mongo.db['school-address'].find())
    schools = iter(sorted(items, key=lambda item: item['school-eng']))
    s = StringIO()
    s.write("\t".join(fields) + "\n")
    for row in schools:
        s.write("\t".join([row[field] for field in fields]) + "\n")

    output = make_response(s.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=school-address.tsv"
    output.headers["Content-type"] = "text/tsv;charset=utf-8"
    return output


@app.route("/school/<urn>", methods=['GET', 'POST'])
def _school(urn):
    if request.method == 'POST':
        mongo.db['school-address'].find_one_and_update(
            {'school-eng': urn},
            {'$set': {'school-eng': urn, 'address': request.form['address'], 'address-match': 'byhand'}},
            upsert=True)
        return redirect("/school/" + urn, code=303)

    edubase = list(mongo.db.edubase.find({'URN': urn}))[0]
    key = uprn = postcode = ''
    address = street = {}
    addresses = parents = children = streets = []

    key = ''
    doc = mongo.db['school-address'].find_one({'school-eng': urn})
    if doc:
        key = doc['address']

    if key != '':
        key = key.split(";")[0]
        uprn = decode(key)
        addresses = llist(mongo.db.address.find({'address': key}))
        address = latest(addresses)
        street = latest(mongo.db.street.find({'street': address['street']}))
        children = sorted_naturally(llist(mongo.db.address.find({'parent-address': key})))
        parents = address_parents(address)
        addresses = addresses + children + parents
        postcode = mongo.db['address-postcode'].find_one({'address': key})['postcode']

    point = []
    if edubase['Easting']:
        lat, lon = pyproj.transform(osgb36, wgs84, edubase['Easting'], edubase['Northing'])
        point = [lon, lat]
        addresses = addresses + llist(mongo.db.address.find({'point': SON([('$nearSphere', [lat, lon]), ('$maxDistance', 0.00004)])}))
        streets = streets + llist(mongo.db.street.find({'point': SON([('$nearSphere', [lat, lon]), ('$maxDistance', 0.00004)])}))

    guesses = {}
    ignore = ['the']
    words = n7e(edubase['EstablishmentName'], ignore).split()
    words = words + ['school', 'academy', 'infant', 'junior', 'middle', 'college', 'jmi', 'campus']
    for a in addresses:
        if set(words).intersection(set(n7e(a['name'], ignore).split())):
            guesses[a['address'] + ":" + a['name']] = a

    guesses = [guesses[k] for k in sorted(guesses)]

    return render_template("school.html",
                           edubase=edubase,
                           guesses=guesses,
                           point=point,
                           address=address,
                           addresses=addresses,
                           streets=streets,
                           street=street,
                           postcode=postcode,
                           uprn=uprn,
                           parents=parents,
                           children=children)


@app.route("/school/<urn>/next")
def _school_next(urn):
    schools = iter(sorted_naturally(mongo.db['school-address'].find()))
    school = next(next(schools) for row in schools if row['school-eng'] == urn)
    return redirect("/school/%s" % (school['school-eng']), code=302)


if __name__ == "__main__":
    app.debug = True
    app.config['MONGO_DBNAME'] = MONGO_DBNAME
    mongo = PyMongo(app)
    app.run()
