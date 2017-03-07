#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

from math import sin, cos, atan2, sqrt
from collections import defaultdict
import json
import bz2
from bisect import bisect_left, bisect_right
from operator import itemgetter


class GeoCoord:
    Radius = 6378.137e3
    Radius2 = 6356.752315e3
    Eccentricity = (Radius - Radius2) / Radius

    def __init__(self, lat, lon):
        self._lat = lat
        self._lon = lon

    def _get_lat(self):
        return self._lat

    def _set_lat(self, lat):
        self._lat = lat

    def _get_lon(self):
        return self._lon

    def _set_lon(self, lon):
        self._lon = lon

    lat = property(_get_lat, _set_lat, None, 'latitude')
    lon = property(_get_lon, _set_lon, None, 'longitude')

    def range_to(self, other):
        φ1 = 8.72664626e-3 * self._lat
        φ2 = 8.72664626e-3 * other.lat
        dφ = 8.72664626e-3 * (other.lat - self._lat)
        dλ = 8.72664626e-3 * (other.lon - self._lon)
        a = sin(dφ) * sin(dφ) + cos(φ1) * cos(φ2) * sin(dλ) * sin(dλ)
        return 6371.0072e3 * 2 * atan2(sqrt(a), sqrt(1 - a))

    def __str__(self):
        return '({:7.5f},{:7.5f})'.format(self._lat, self._lon)


class City:
    def __init__(self, city):
        if isinstance(city, dict):
            self._city_id = city['_id']
            self._name = city['name']
            self._coord = GeoCoord(city['coord']['lat'], city['coord']['lon'])
            self._country = city['country']
        elif isinstance(city, City):
            self._city_id = city.city_id
            self._name = city.name
            self._coord = city.coord
            self._country = city.country
        else:
            self._city_id = None
            self._name = None
            self._coord = None
            self._country = None

    def _get_city_id(self):
        return self._city_id

    def _set_city_id(self, city_id):
        self._city_id = city_id

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    def _get_coord(self):
        return self._coord

    def _set_coord(self, coord):
        self._lat = coord

    def _get_country(self):
        return self._country

    def _set_country(self, country):
        self._country = country

    city_id = property(_get_city_id, _set_city_id, None, 'ID')
    name = property(_get_name, _set_name, None, 'name')
    coord = property(_get_coord, _set_coord, None, 'geo coords')
    country = property(_get_country, _set_country, None, 'country code')

    def __str__(self):
        return '{} ({:7.5f} {:7.5f}) {} {}'.format(self._name,
                                                   self._coord.lat,
                                                   self._coord.lon,
                                                   self._country,
                                                   self._city_id)


class CityList:
    def __init__(self, city_list_filename=None):
        self.countries = []
        self.cities = []
        self.cities_by_country = defaultdict(list)
        if city_list_filename:
            self.read(city_list_filename)

    def read(self, city_list_filename):
        with bz2.open(city_list_filename, 'r') as city_file:
            lines = city_file.readlines()
            for line in lines:
                city = City(json.loads(line.decode('utf-8')))
                self.cities.append(city)
                self.countries.append(city.country)
                self.cities_by_country[city.country].append(city)
        self.countries = sorted(list(set(self.countries)))

    def find(self, name, country=None):
        name = name.lower()

        def _by_name(city):
            return name in city.name.lower()

        city_list = self.cities_by_country[country] if country else self.cities
        return filter(_by_name, city_list)


class SortedCityCollection(object):
    def __init__(self, iterable=(), key=(lambda x: x), _id=lambda c: c.city_id):
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
