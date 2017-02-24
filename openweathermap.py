#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

    Python bindings for OpenWeatherMap API.

    Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
    All rights reserved.

"""

import sys
import urllib3
import json
from collections import defaultdict
from datetime import datetime


class CityList:
    CityListFilename = "city.list.json"

    def __init__(self):
        with open(CityList.CityListFilename) as city_file:
            lines = city_file.readlines()
        self.countries = set()
        self.cities = []
        self.cities_by_country = defaultdict(list)
        for line in lines:
            d = json.loads(line)
            country = d.get("country")
            if country:
                self.countries.add(country)
                self.cities_by_country[country].append(d.get("name"))
                self.cities.append(d)


class OpenWeatherMapCore:
    api_key = None

    def __init__(self, api_key):
        self.api_key = api_key

    def _req(self, url, params):
        response = None
        try:
            http = urllib3.PoolManager()
            params["APPID"] = self.api_key
            params["units"] = "metric"
            response = http.request("GET", url, fields=params)
        except urllib3.exceptions.HTTPError as e:
            print(e)
        if response and response.data:
            return json.loads(response.data.decode("utf-8"))

    @staticmethod
    def icon_url(condition_code):
        return "http://openweathermap.org/img/w/{}.png".format(condition_code)

    def current(self, city_id):
        return self._req("api.openweathermap.org/data/2.5/weather",
                         {"id": city_id})

    def forecast(self, city_id):
        return self._req("api.openweathermap.org/data/2.5/forecast",
                         {"id": city_id})

    def forecast_daily(self, city_id, days=1):
        return self._req("api.openweathermap.org/data/2.5/forecast/daily",
                         {"id": city_id, "cnt": days})


class OpenWeatherMap(OpenWeatherMapCore):

    def __init__(self, api_key):
        super(OpenWeatherMap, self).__init__(api_key)


BURGDORF_DE = 6557397
HANNOVER_DE = 6559065


def main(api_key):
    owm = OpenWeatherMap(api_key)
    for forecast in owm.forecast_daily(HANNOVER_DE, 3)["list"]:
        print("{} {} {:d}-{:d}°C, wind @ {:d} km/h from {}"
              .format(datetime.fromtimestamp(forecast["dt"]).strftime("%a %d.%m."),
                      forecast["weather"][0]["description"],
                      int(round(forecast["temp"]["min"])), int(round(forecast["temp"]["max"])),
                      int(round(60 * 60 * forecast["speed"] / 1000)),
                      ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((forecast["deg"]-22.5) % 360) // 45]))
        # pprint(forecast)

    # cities = CityList()
    # pprint(cities.countries)
    # pprint(cities.cities_by_country)

if __name__ == "__main__":
    main(sys.argv[1])
