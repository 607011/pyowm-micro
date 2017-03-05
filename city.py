#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

from math import sin, cos, atan2, atan, sqrt, pi
from collections import defaultdict
import pickle
import bz2


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
    def __init__(self, city, fmt="JSON"):
        if city:
            if type(city) is City:
                self.city_id = city.city_id
                self.name = city.name
                self.pos = city.pos
                self.country = city.country
            if fmt == "JSON":
                self.city_id = city["_id"]
                self.name = city["name"]
                self.pos = GeoCoord(city["coord"]["lat"], city["coord"]["lon"])
                self.country = city["country"]

    def __str__(self):
        return "{} ({:7.5f} {:7.5f}) {} {}".format(self.name, self.pos.lat, self.pos.lon, self.country, self.city_id)


class CityList:
    def __init__(self, city_list_filename=None):
        self.countries = []
        self.cities = []
        self.cities_by_country = defaultdict(list)
        if city_list_filename:
            self.read(city_list_filename)

    def read(self, city_list_filename):
        with bz2.open(city_list_filename) as city_file:
            self.cities = pickle.load(city_file)
        for city in self.cities:
            self.countries.append(city.country)
            self.cities_by_country[city.country].append(city)
        self.countries = sorted(list(set(self.countries)))

    def find(self, name, country=None):
        name = name.lower()

        def _by_name(city):
            return name in city.name.lower()

        city_list = self.cities_by_country[country] if country else self.cities
        return filter(_by_name, city_list)


