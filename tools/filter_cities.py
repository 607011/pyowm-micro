#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import json
from collections import defaultdict
from pprint import pprint

cities = defaultdict(list)

def read(filename):
    global cities
    with open(filename) as city_file:
        lines = city_file.readlines()
        n_lines = len(lines)
        n = 0
        for line in lines:
            d = json.loads(line)
            cities[d["name"]].append(d)
            n += 1
            yield 100 * n // n_lines

def filter_city(city_list):
    result = []
    for city in city_list:
        pass  # TODO ...
    return result

def main(filename):
    global cities
    for p in read(filename):
        print("\rLoading city list ... {:d}%".format(p), end="", flush=True)
    print("\nFiltering ...")
    result = []
    EPSILON = 1e3
    for city in cities.keys():
        result.extend(filter_city(cities[city]))

    print("Sorting ...")
    result.sort(key=lambda k: k["name"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
