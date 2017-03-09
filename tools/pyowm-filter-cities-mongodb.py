#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# Eliminate redundant entries from city.list.json (fetched from openweathermap.org)
# and save the result to a JSON file using MongoDB geonear queries.
#
# Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
# All rights reserved.


import sys
import os
import time
from pymongo import MongoClient, GEOSPHERE
from bson.son import SON
import json
import bz2
from shutil import copyfileobj
sys.path.insert(0, '../')
from pyowm.city import CityList, City


class JSONCityEncoder(json.JSONEncoder):
    def default(self, o):
        return self.encode(o) if isinstance(o, City) else json.JSONEncoder.default(self, o)

    def encode(self, o):
        return {'_id': o.city_id,
                'name': o.name,
                'coord': {
                    'lat': o.coord.lat,
                    'lon': o.coord.lon},
                'country': o.country}


class Stopwatch:
    def __init__(self):
        self._t = time.time()

    def start(self):
        self._t = time.time()

    def elapsed(self):
        return time.time() - self._t


def main():
    client = MongoClient('localhost', 27017)
    db = client.cities

    stopwatch = Stopwatch()

    print('Loading city list ... ', end='', flush=True)
    stopwatch.start()
    cities = CityList('../city.list.json.bz2')
    n_cities = len(cities)
    print('{:.2f}s ({:d} cities read)'.format(stopwatch.elapsed(), n_cities))

    print('Clearing MongoDB collection ... ', end='', flush=True)
    stopwatch.start()
    db.cities.remove({})
    print('{:.2f}s'.format(stopwatch.elapsed()))

    print('Storing in MongoDB collection ... ', end='', flush=True)
    stopwatch.start()
    db.cities.drop_index([("geo", GEOSPHERE)])
    db.cities.create_index([("geo", GEOSPHERE)])
    db.cities.insert(cities)
    print('{:.2f}s'.format(stopwatch.elapsed()))

    stopwatch.start()
    result = []
    n = 0
    max_distance = 2200.0
    for city in cities:
        nsum = db.cities.find({}).count()
        nearby = db.cities.find(
            {'$and': [
                {'_id': SON({'$ne': city['_id']})},
                {'geo': SON([('$near',
                              {'type': 'Point',
                               'coordinates': [city.coord.lon, city.coord.lat]
                               }
                              ),
                             ('$maxDistance', max_distance)])}
            ]})
        n_to_delete = nearby.count()
        if n_to_delete == 0:
            result.append(city)
        else:
            """
            for c in nearby:
                db.cities.delete_one(c)
            """
        n += 1
        print("\rFiltering ... {:d}% #{:07d}; {:d} deleted ({:.2f}%)"
              .format(100 * n // n_cities, city['_id'], n_cities - nsum, 100 - 100 * nsum / n_cities),
              end='', flush=True)
    n_removed = n_cities - len(result)
    print("\nRemoved {:d} from {:d} cities in {:.2f}s, {:.1f}% remaining."
          .format(n_removed, n_cities, stopwatch.elapsed(), 100 - 100 * n_removed // n_cities))

    stopwatch.start()
    out_filename = "city.list.reduced.mongo.json"
    n = 0
    n_cities = len(result)
    with open(out_filename, 'w') as json_file:
        for city in result:
            n += 1
            print("\rWriting result to {:s} ... {:d}%".format(out_filename, 100 * n // n_cities), end='', flush=True)
            json.dump(city, json_file, cls=JSONCityEncoder, ensure_ascii=False)
            json_file.write("\n")
    print(' {:.2f}s'.format(stopwatch.elapsed()))
    stopwatch.start()
    print("\nCompressing file ... ", end='', flush=True)
    with open(out_filename, 'rb') as json_file:
        with bz2.BZ2File(out_filename + '.bz2', 'wb', compresslevel=9) as output:
            copyfileobj(json_file, output)
    if os.path.exists(out_filename):
        os.remove(out_filename)
    print('{:.2f}s'.format(stopwatch.elapsed()))
    print("\nReady.")


if __name__ == '__main__':
    main()

