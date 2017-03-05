#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

# Eliminate redundant entries from city.list.json (fetched from openweathermap.org)
# and save the result to a JSON file.
#
# Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
# All rights reserved.

import sys
import json
from math import sin, cos, atan, sqrt, pi, atan2
from bisect import bisect_left, bisect_right
from operator import itemgetter
import pickle
import bz2


class SortedCityCollection(object):
    def __init__(self, iterable=(), key=None, _id=None):
        self._given_key = key
        self._key = (lambda x: x) if key is None else key
        self._id = (lambda x: x) if _id is None else _id

        decorated = sorted([(self._key(item), item) for item in iterable], key=itemgetter(0))
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]

        decorated_ids = sorted([(self._id(item), item) for item in iterable], key=itemgetter(0))
        self._ids = [_id for _id, item in decorated_ids]
        self._items_by_id = {_id: item for _id, item in decorated_ids}

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, "key function")

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key, self._id)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return "%s(%r, key=%s)".format(
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, "__name__", repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index_by_id(self, _id):
        i = bisect_left(self._ids, _id)
        return i

    def find_by_id(self, _id):
        i = self.index_by_id(_id)
        if i != len(self) and self._ids[i] == _id:
            return self._items_by_id[i]
        raise ValueError("No item found with _id equal to: %r".format(_id))

    def remove_by_id(self, _id):
        item = self._items_by_id[_id]
        del self._items_by_id[_id]
        self.remove(item)

    def index(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def find(self, k):
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError("No item found with key equal to: %r".format(k))

    def remove(self, item):
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def range(self, item_a, item_b):
        i = bisect_right(self._keys, item_a)
        j = bisect_left(self._keys, item_b)
        return self._items[i:j]


class GeoCoord:
    Radius = 6378.137e3
    Radius2 = 6356.752315e3
    Eccentricity = (Radius - Radius2) / Radius

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def range_to(self, other):
        φ1 = 8.72664626e-3 * self.lat
        φ2 = 8.72664626e-3 * other.lat
        dφ = 8.72664626e-3 * (other.lat - self.lat)
        dλ = 8.72664626e-3 * (other.lon - self.lon)
        a = sin(dφ) * sin(dφ) + cos(φ1) * cos(φ2) * sin(dλ) * sin(dλ)
        return 6371.0072e3 * 2 * atan2(sqrt(a), sqrt(1 - a))

    def range_to_accurate(self, other):
        f = pi * (self.lat + other.lat) / 360
        g = pi * (self.lat - other.lat) / 360
        l = pi * (self.lon - other.lon) / 360
        s = sin(g) * sin(g) * cos(l) * cos(l) + cos(f) * cos(f) * sin(l) * sin(l)
        c = cos(g) * cos(g) * cos(l) * cos(l) + sin(f) * sin(f) * sin(l) * sin(l)
        if s == 0 or c == 0:
            return -1
        o = atan(sqrt(s / c))
        r = sqrt(s / c) / o
        d = 2 * o * GeoCoord.Radius
        h1 = (3 * r - 1) / (2 * c)
        h2 = (3 * r + 1) / (2 * s)
        return d * (1 +
                    GeoCoord.Eccentricity * h1 * sin(f) * sin(f) * cos(g) * cos(g) -
                    GeoCoord.Eccentricity * h2 * cos(f) * cos(f) * sin(g) * sin(g))

    def __str__(self):
        return "({:7.5f},{:7.5f})".format(self.lat, self.lon)


class City:
    def __init__(self, city):
        self.city_id = city["_id"]
        self.name = city["name"]
        self.pos = GeoCoord(city["coord"]["lat"], city["coord"]["lon"])
        self.country = city["country"]


def main(filename):
    cities = []
    cities_by_id = {}

    with open(filename, encoding="utf-8") as city_file:
        lines = city_file.readlines()
        n_lines = len(lines)
        n = 0
        for line in lines:
            city = City(json.loads(line))
            cities.append(city)
            cities_by_id[city.city_id] = city
            n += 1
            print("\rLoading city list ... {:d}%".format(100 * n // n_lines), end="", flush=True)
        print()

    print("Pre-filtering ...")
    cities_lat = SortedCityCollection(cities, key=lambda c: c.pos.lat, _id=lambda c: c.city_id)
    cities_lon = SortedCityCollection(cities, key=lambda c: c.pos.lon, _id=lambda c: c.city_id)
    dlat2 = 0.003
    dlon2 = 0.003

    result = []
    n = 0
    min_dist = 2200.0
    while len(cities) > 0:
        ref_city = cities.pop(0)
        ref_pos = ref_city.pos
        cities_lat.remove_by_id(ref_city.city_id)
        cities_lon.remove_by_id(ref_city.city_id)
        cities_by_lat = cities_lat.range(ref_pos.lat - dlat2, ref_pos.lat + dlat2)
        cities_by_lon = cities_lon.range(ref_pos.lon - dlon2, ref_pos.lon + dlon2)
        ids = set([c.city_id for c in cities_by_lat]).intersection([c.city_id for c in cities_by_lon])
        merged = [cities_by_id[i] for i in ids]
        if all([ref_pos.range_to(c.pos) > min_dist for c in merged]):
            result.append(ref_city)
        n += 1
        print("\rFiltering ... {:d}%".format(100 * n // n_lines), end="", flush=True)
    n_removed = n_lines - len(result)
    print("\nRemoved {:d} redundant cities, {:.1f}% remaining.".format(n_removed, 100 - 100 * n_removed // n_lines))

    out_filename = "city.list.reduced.pickle.bz2"
    print("Writing result to {} ...".format(out_filename))
    with bz2.open(out_filename, "wb", compresslevel=9) as out_file:
        pickle.dump(result, out_file)


if __name__ == "__main__":
    main(sys.argv[1])
