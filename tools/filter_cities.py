#!/usr/bin/env python3
#  -*- coding: utf-8 -*-

import sys
import json
from math import sin, cos, atan, sqrt, pi


def deg2rad(a):
    return a * pi / 180


Radius = 6378137.0
Radius2 = 6356752.315
Eccentricity = (Radius - Radius2) / Radius


def geo_distance(lat0, lon0, lat1, lon1):
    f = deg2rad(lat0 + lat1) / 2
    g = deg2rad(lat0 - lat1) / 2
    l = deg2rad(lon0 - lon1) / 2
    s = sin(g) * sin(g) * cos(l) * cos(l) + cos(f) * cos(f) * sin(l) * sin(l)
    c = cos(g) * cos(g) * cos(l) * cos(l) + sin(f) * sin(f) * sin(l) * sin(l)
    if s == 0 or c == 0:
        return -1
    o = atan(sqrt(s / c))
    r = sqrt(s / c) / o
    d = 2 * o * Radius
    h1 = (3 * r - 1) / (2 * c)
    h2 = (3 * r + 1) / (2 * s)
    return d * (1 +
                Eccentricity * h1 * sin(f) * sin(f) * cos(g) * cos(g) -
                Eccentricity * h2 * cos(f) * cos(f) * sin(g) * sin(g))


def far_enough(lat1, lon1, lat2, lon2, min_dist=1000):
    return geo_distance(lat1, lon1, lat2, lon2) > min_dist


def main(filename):
    cities = []

    with open(filename) as city_file:
        lines = city_file.readlines()
        n_lines = len(lines)
        n = 0
        for line in lines:
            d = json.loads(line)
            cities.append(d)
            n += 1
            print("\rLoading city list ... {:d}%".format(100 * n // n_lines), end="", flush=True)
        print()

    result = []
    n = 0
    while len(cities) > 0:
        ref_city = cities.pop(0)
        lat = ref_city["coord"]["lat"]
        lon = ref_city["coord"]["lon"]
        if all(map(lambda city: far_enough(lat, lon, city["coord"]["lat"], city["coord"]["lon"]), cities)):
            result.append(ref_city)
        n += 1
        print("\rFiltering ... {:d}%".format(100 * n // n_lines), end="", flush=True)
    n_removed = n_lines - len(result)
    print("\nRemoved {:d} ({:.1f}%) redundant cities.".format(n_removed, 100 - 100 * n_removed // n_lines))

    print("Sorting ...")
    result.sort(key=lambda k: k["name"])

    print("Writing result to out.json ...")
    with open("out.json", "w+") as out_file:
        json.dump(result, out_file, indent=2)


if __name__ == "__main__":
    main(sys.argv[1])
