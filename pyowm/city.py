#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

from math import sin, cos, atan2, sqrt, radians
from collections import defaultdict
import json
import bz2
from bisect import bisect_left, bisect_right
from operator import itemgetter


__author__ = 'Oliver Lau <oliver@ersatzworld.net>'
__website__ = 'https://github.com/ola-ct/pyowm-micro'
__license__ = 'GPLv3+'


class GeoCoord(dict):
    R = 6371.0072e3

    def __init__(self, lat=0.0, lon=0.0):
        self.lat = lat
        self.lon = lon
        self.cartesian = Point3D.from_lat_lon(lat, lon)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def range_to(self, other):
        φ1 = radians(self.lat)
        φ2 = radians(other.lat)
        dφ = radians(other.lat - self.lat)
        dλ = radians(other.lon - self.lon)
        a = sin(dφ) * sin(dφ) + cos(φ1) * cos(φ2) * sin(dλ) * sin(dλ)
        return GeoCoord.R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def distance_3d(self, other):
        return self.cartesian.distance_to(other.cartesian)

    def __str__(self):
        return '({:7.5f},{:7.5f})'.format(self.lat, self.lon)


class Point3D(tuple):
    def __new__(cls, x, y, z):
        return super(Point3D, cls).__new__(cls, (x, y, z))

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dz = other.z - self.z
        return sqrt(dx * dx + dy * dy + dz * dz)

    @staticmethod
    def from_lat_lon(lat, lon):
        lat = radians(lat)
        lon = radians(lon)
        return Point3D(GeoCoord.R * cos(lat) * cos(lon),
                       GeoCoord.R * cos(lat) * sin(lon),
                       GeoCoord.R * sin(lat))


class City(dict):
    def __init__(self, _city=dict()):
        if isinstance(_city, City):
            self._id = city._id
            self.name = city.name
            self.country = city.country
            self.coord = city.coord
        elif isinstance(_city, dict):
            self._id = _city.get('_id')
            self.name = _city.get('name')
            self.country = _city.get('country')
            self.coord = GeoCoord(_city.get('coord', {}).get('lat'),
                                  _city.get('coord', {}).get('lon'))

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __str__(self):
        return '{} ({:7.5f} {:7.5f}) ({}) {} {}'\
            .format(self.name,
                    self.coord.lat,
                    self.coord.lon,
                    self.coord.cartesian,
                    self.country,
                    self._id)


class CityList:
    def __init__(self, city_list_filename=None):
        self.countries = []
        self.cities = []
        self.cities_by_country = defaultdict(list)
        if isinstance(city_list_filename, str):
            self.read(city_list_filename)

    def __iter__(self):
        return iter(self.cities)

    def __len__(self):
        return len(self.cities)

    def __getitem__(self, i):
        return self.cities[i]

    def read(self, city_list_filename, callback=None):
        with bz2.open(city_list_filename, 'r') as city_file:
            lines = city_file.readlines()
            n = 0
            n_lines = len(lines)
            for line in lines:
                c = City(json.loads(line.decode('utf-8')))
                self.cities.append(c)
                self.countries.append(c.country)
                self.cities_by_country[c.country].append(c)
                if callback:
                    n += 1
                    callback(100 * n // n_lines)
        self.countries = sorted(list(set(self.countries)))

    def find(self, name, country=None):
        name = name.lower()

        def _by_name(c):
            return name in c.name.lower()

        city_list = self.cities_by_country[country] if country else self.cities
        return filter(_by_name, city_list)


class SortedCityCollection(object):
    def __init__(self, iterable=(), key=(lambda x: x), _id=lambda c: c._id):
        self._given_key = key
        self._key = key
        self._id = _id

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

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key, self._id)

    def copy(self):
        return self.__class__(self, self._key, self._id)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)'.format(
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
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
        raise ValueError('No item found with _id equal to: %r'.format(_id))

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
        raise ValueError('No item found with key equal to: %r'.format(k))

    def remove(self, item):
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def range(self, l, r):
        i = bisect_right(self._keys, l)
        j = bisect_left(self._keys, r)
        return self._items[i:j]


if __name__ == '__main__':
    print('Loading city list ... ')
    cities = CityList()
    cities.read('city.list.reduced.json.bz2')
    for city in cities.find('Hannover'):
        print(' - {:s}, {:s} @ {:.5}, {:.5}'.format(city.name, city.country, city.coord.lat, city.coord.lon))
