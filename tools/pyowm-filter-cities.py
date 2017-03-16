#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# Eliminate redundant entries from city.list.json (fetched from openweathermap.org)
# and save the result to a JSON file.
#
# Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
# All rights reserved.

import json
from shutil import copyfileobj
import bz2
import os
import sys
import time
from scipy import spatial
sys.path.insert(0, '../')
from pyowm.city import City, SortedCityCollection


class Stopwatch:
    def __init__(self):
        self._t = time.time()

    def start(self):
        self._t = time.time()

    def elapsed(self):
        return time.time() - self._t


class JSONCityEncoder(json.JSONEncoder):
    def default(self, o):
        return self.encode(o) if isinstance(o, City) else json.JSONEncoder.default(self, o)

    def encode(self, o):
        return {'_id': o._id,
                'name': o.name,
                'coord': {
                    'lat': o.coord.lat,
                    'lon': o.coord.lon},
                'country': o.country}


def main(filename, min_dist):
    min_dist = int(min_dist) if type(min_dist) is not int else min_dist
    stopwatch = Stopwatch()
    stopwatch.start()
    cities = []
    cities_by_id = {}
    with open(filename, encoding='utf-8') as city_file:
        lines = city_file.readlines()
        n_lines = len(lines)
        n = 0
        for line in lines:
            city = City(json.loads(line))
            cities.append(city)
            cities_by_id[city._id] = city
            n += 1
            print("\rLoading city list ... {:d}% ".format(100 * n // n_lines), end='', flush=True)
    print(' [{:.2f}s]'.format(stopwatch.elapsed()))

    print('Building k-d-tree ... ', end='', flush=True)
    stopwatch.start()
    tree = spatial.KDTree([c.coord.cartesian for c in cities])
    print(' [{:.2f}s]'.format(stopwatch.elapsed()))

    stopwatch.start()
    result = []
    n = 0
    for ref_city in cities:
        if len(tree.query_ball_point(ref_city.coord.cartesian, min_dist)) <= 1:
            result.append(ref_city)
        n += 1
        print("\rFiltering ... {:d}% #{:07d}  [{:.2f}s]"
              .format(100 * n // n_lines, ref_city._id, stopwatch.elapsed()), end='', flush=True)
    print()
    n_removed = n_lines - len(result)
    print('Removed {:d} redundant cities, {:.1f}% remaining.'.format(n_removed, 100 - 100 * n_removed // n_lines))
    out_filename = '{:s}.reduced.json'.format('.'.join(filename.split('.')[0:-1]))

    if os.path.exists(out_filename):
        os.remove(out_filename)

    stopwatch.start()
    n = 0
    n_cities = len(result)
    with open(out_filename, 'w') as json_file:
        for city in result:
            n += 1
            print("\rWriting result to {:s} ... {:d}% ".format(out_filename, 100 * n // n_cities), end='', flush=True)
            json.dump(city, json_file, cls=JSONCityEncoder, ensure_ascii=False)
            json_file.write("\n")
    print(' [{:.2f}s]'.format(stopwatch.elapsed()))

    stopwatch.start()
    print('Compressing file ... ', end='', flush=True)
    with open(out_filename, 'rb') as json_file:
        with bz2.BZ2File(out_filename + '.bz2', 'wb', compresslevel=9) as output:
            copyfileobj(json_file, output)
    print(' [{:.2f}s]'.format(stopwatch.elapsed()))

    if os.path.exists(out_filename):
        os.remove(out_filename)

    print('Ready.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '../city.list.json',
         sys.argv[2] if len(sys.argv) > 2 else 5000)
