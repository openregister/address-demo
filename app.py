#!/usr/bin/env python

import csv
from config import MONGO_DBNAME
from base32_crockford import encode, decode
from flask import Flask, render_template, Markup, redirect
import markdown
from addresses import mongo, llist, latest, sorted_naturally, streets, addresses, address_parents, postcode_addresses
import schools


app = Flask(__name__)
app.config['MONGO_DBNAME'] = MONGO_DBNAME
mongo.init_app(app)

app.register_blueprint(schools.schools)


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


@app.route("/addresses/postcode/<postcode>")
def _postcode(postcode):
    addresses = postcode_addresses(postcode)
    return render_template("addresses.html", name=postcode, addresses=addresses)


if __name__ == "__main__":
    app.debug = True
    app.run()
