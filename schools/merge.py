#!/usr/bin/env python

import csv

schools = {}

for row in csv.DictReader(open('../../school-data/maps/addresses.tsv'), delimiter='\t'):
    schools[row['school']] = row

for row in csv.DictReader(open('school-address.tsv'), delimiter='\t'):
    schools[row['school-eng']] = row

fields = ['school', 'address']
print("\t".join(fields))
for key in sorted(schools):

    school = schools[key]
    if 'school' not in school:
        school['school'] = school['school-eng']

    print("\t".join([school[field] for field in fields]))
