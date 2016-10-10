#!/usr/bin/env python

import csv

schools = {}

for row in csv.DictReader(open('../../school-data/maps/school-address.tsv'), delimiter='\t'):
    schools[row['school']] = row

for row in csv.DictReader(open('../tmp/school-address.tsv'), delimiter='\t'):
    schools[row['school']] = row

fields = ['school', 'address', 'address-match']
print("\t".join(fields))
for key in sorted(schools):

    school = schools[key]
    if 'school' not in school:
        school['school'] = school['school']

    print("\t".join([school[field] for field in fields]))
