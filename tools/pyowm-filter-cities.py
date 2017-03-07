#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# Eliminate redundant entries from city.list.json (fetched from openweathermap.org)
# and save the result to a JSON file.
#
# Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
# All rights reserved.

import json
from shutil import copyfileobj
from math import cos, pi
import bz2
import os
import sys
sys.path.insert(0, "{}/../..".format(os.getcwd()))
from pyowm.city import City, SortedCityCollection


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


def main(filename):
    cities = []
    cities_by_id = {}
    with open(filename, encoding='utf-8') as city_file:
        lines = city_file.readlines()
        n_lines = len(lines)
        n = 0
        for line in lines:
            city = City(json.loads(line))
            cities.append(city)
            cities_by_id[city.city_id] = city
            n += 1
            print("\rLoading city list ... {:d}%".format(100 * n // n_lines), end='', flush=True)
    print("\nSorting by latitude ... ", end='', flush=True)
    cities_lat = SortedCityCollection(cities, key=lambda c: c.coord.lat)
    print("\nSorting by longitude ... ", end='', flush=True)
    cities_lon = SortedCityCollection(cities, key=lambda c: c.coord.lon)
    print()
    result = []
    n = 0
    min_dist = 2200.0
    earth_radius = 6371e3
    dlat2 = pi / 4 * min_dist / earth_radius
    while len(cities) > 0:
        ref_city = cities.pop(0)
        cities_lat.remove_by_id(ref_city.city_id)
        cities_lon.remove_by_id(ref_city.city_id)
        dlon2 = pi / 2 * min_dist / earth_radius * cos(pi * ref_city.coord.lat / 180)
        cities_by_lat = cities_lat.range((ref_city.coord.lat - dlat2) % 90, (ref_city.coord.lat + dlat2) % 90)
        cities_by_lon = cities_lon.range((ref_city.coord.lon - dlon2) % 180, (ref_city.coord.lon + dlon2) % 180)
        ids = set([c.city_id for c in cities_by_lat]).intersection([c.city_id for c in cities_by_lon])
        merged = [cities_by_id[i] for i in ids]
        if all([ref_city.coord.range_to(c.coord) > min_dist for c in merged]):
            result.append(ref_city)
        n += 1
        print("\rFiltering ... {:d}% #{:07d}".format(100 * n // n_lines, ref_city.city_id), end='', flush=True)
    n_removed = n_lines - len(result)
    print("\nRemoved {:d} redundant cities, {:.1f}% remaining.".format(n_removed, 100 - 100 * n_removed // n_lines))
    out_filename = '{:s}.reduced.json'.format('.'.join(filename.split('.')[0:-1]))
    if os.path.exists(out_filename):
        os.remove(out_filename)
    n = 0
    n_cities = len(result)
    with open(out_filename, 'w') as json_file:
        for city in result:
            n += 1
            print("\rWriting result to {:s} ... {:d}%".format(out_filename, 100 * n // n_cities), end='', flush=True)
            json.dump(city, json_file, cls=JSONCityEncoder, ensure_ascii=False)
            json_file.write("\n")
    print("\nCompressing file ... ", end='', flush=True)
    with open(out_filename, 'rb') as json_file:
        with bz2.BZ2File(out_filename + '.bz2', 'wb', compresslevel=9) as output:
            copyfileobj(json_file, output)
    if os.path.exists(out_filename):
        os.remove(out_filename)
    print("\nReady.")


if __name__ == '__main__':
    main(sys.argv[1])
