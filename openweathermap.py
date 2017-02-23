#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

    Python bindings for OpenWeatherMap API.

    Copyright (c) 2017 Oliver Lau <oliver@ersatzworld.net>
    All rights reserved.

"""

import sys
import urllib3
from pprint import pprint


class OpenWeatherMapCore:

    api_key = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.verbose = False

    def _req(self, url, params):
        response = None
        try:
            http = urllib3.PoolManager()
            params["APPID"] = self.api_key
            response = http.request("GET", url, fields=params)
        except urllib3.exceptions.HTTPError as e:
            print(e)
        if response:
            return response.data

    def current(self, city_id):
        return self._req("api.openweathermap.org/data/2.5/weather", {"id": city_id})


class OpenWeatherMap(OpenWeatherMapCore):

    def __init__(self, api_key):
        super(OpenWeatherMap, self).__init__(api_key)


def main(api_key):
    owm = OpenWeatherMap(api_key)
    pprint(owm.current(6557397))

if __name__ == "__main__":
    main(sys.argv[1])
