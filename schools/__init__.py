import re
from base32_crockford import decode
from bson.son import SON
from flask import Blueprint, request, render_template, redirect, make_response, abort
from io import StringIO
import pyproj
from addresses import mongo, llist, latest, sorted_naturally, address_parents

schools = Blueprint('schools', __name__, template_folder='templates')

osgb36 = pyproj.Proj("+init=EPSG:27700")
wgs84 = pyproj.Proj("+init=EPSG:4326")


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


@schools.route("/schools")
def _schools():
    # ad-hoc load schools to be reviewed ..
    schools = []
    addresses = []
    byhand = 0
    matches = 0
    for school in mongo.db['school-address'].find():
        edubase = mongo.db['edubase'].find_one({'URN': school['school']})
        if not edubase:
            print("unknown school", school['school'])
            continue
        school['name'] = edubase['EstablishmentName']
        if 'address' in school and school['address']:
            if school.get('address-match', '') == "byhand":
                byhand = byhand + 1
            else:
                for address in llist(mongo.db.address.find({'address': school['address']})):
                    if 'name' not in school or 'name' not in school:
                        print(school)
                        print(address)
                    addresses.append(address)
                    if n7e(school['name']) == n7e(address['name']):
                        school['address-name'] = address['name']
                        school['address'] = address['address']
                        school['address-match'] = 'matched'
                        matches = matches + 1
                        break
        if 'address' in school and 'address-name' not in school and school['address']:
            a = latest(mongo.db.address.find({'address': school['address']}))
            if a:
                school['address-name'] = a['name']
        schools.append(school)

    return render_template("schools.html", schools=sorted_naturally(schools), addresses=addresses, matches=matches, byhand=byhand)


@schools.route("/school-address.tsv")
def _schools_tsv():
    # for school in mongo.db['school-address'].find():

    fields = ["school", "address", "address-match"]
    items = list(mongo.db['school-address'].find())
    schools = iter(sorted(items, key=lambda item: item['school']))
    s = StringIO()
    s.write("\t".join(fields) + "\n")
    for row in schools:
        s.write("\t".join([row[field] for field in fields]) + "\n")

    output = make_response(s.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=school-address.tsv"
    output.headers["Content-type"] = "text/tsv;charset=utf-8"
    return output


@schools.route("/school/<urn>", methods=['GET', 'POST'])
def _school(urn):
    if request.method == 'POST':
        mongo.db['school-address'].find_one_and_update(
            {'school': urn},
            {'$set': {'school': urn, 'address': request.form['address'], 'address-match': 'byhand'}},
            upsert=True)
        return redirect("/school/" + urn, code=303)

    edubase = latest(mongo.db.edubase.find({'URN': urn}))
    if not edubase:
        return abort(404)
    key = uprn = postcode = ''
    address = street = {}
    addresses = parents = children = streets = []

    key = ''
    doc = mongo.db['school-address'].find_one({'school': urn})
    if doc:
        key = doc['address']

    if key != '':
        key = key.split(";")[0]
        uprn = decode(key)
        addresses = llist(mongo.db.address.find({'address': key}))
        address = latest(addresses)
        if address:
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


@schools.route("/school/<urn>/next")
def _school_next(urn):
    schools = iter(sorted_naturally(mongo.db['school-address'].find()))
    school = next(next(schools) for row in schools if row['school'] == urn)
    return redirect("/school/%s" % (school['school']), code=302)
