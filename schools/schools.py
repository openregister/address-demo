#!/usr/bin/env python

import re
import csv


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


def find_address(addresses, name):
    matches = []
    for key, entries in addresses.items():
        for address in entries:
            if n7e(name) == n7e(address['name']):
                matches.append(address['address'])

    return matches


if __name__ == "__main__":

    # load herts schools
    addresses = {}
    for row in csv.DictReader(open('herts.tsv'), delimiter="\t"):
        if not row['address'] in addresses:
            addresses[row['address']] = []
        addresses[row['address']].append(row)

    print("%s\t%s\t%s\t%s" % ('school-eng', 'name', 'address', 'address-match'))

    for school in csv.DictReader(open('schools.tsv1'), delimiter="\t"):
        if school['address-match'] != 'byhand':
            school['address'] = ";".join(find_address(addresses, school['name']))
        print("%s\t%s\t%s\t%s" % (school['school-eng'], school['name'], school['address'], school['address-match']))
