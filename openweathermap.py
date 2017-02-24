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
from pprint import pprint


def degree_to_meteo(deg):
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((deg - 22.5) % 360) // 45]


class CityList:
    def __init__(self, city_list_filename=None):
        self.countries = []
        self.cities = []
        self.cities_by_country = defaultdict(list)
        if city_list_filename:
            self.read(city_list_filename)

    def read(self, city_list_filename):
        with open(city_list_filename) as city_file:
            lines = city_file.readlines()
            n_lines = len(lines)
            n = 0
            for line in lines:
                d = json.loads(line)
                country = d.get("country")
                if country:
                    self.countries.append(country)
                    self.cities_by_country[country].append(d)
                    self.cities.append(d)
                n += 1
                yield 100 * n // n_lines
            self.countries = sorted(list(set(self.countries)))

    def find(self, name, country=None):
        name = name.lower()

        def _by_name(city):
            return name in city["name"].lower()

        city_list = self.cities_by_country[country] if country else self.cities
        return filter(_by_name, city_list)


class Weather:
    def __init__(self, owm_obj=None):
        self.weather = owm_obj
        self.icon = None
        self.description = None
        self.temp_min = None
        self.temp_max = None
        self.wind_speed = None
        self.wind_degrees = None

    def icon_url(self):
        return "http://openweathermap.org/img/w/{}.png".format(self.icon) if self.icon else str()


class CurrentWeather(Weather):
    def __init__(self, owm_obj=None):
        super(CurrentWeather, self).__init__(owm_obj)
        try:
            self.date = datetime.fromtimestamp(self.weather["dt"])
            self.humidity = self.weather["main"]["humidity"]
            self.pressure = self.weather["main"]["pressure"]
            self.temp = self.weather["main"]["temp"]
            self.temp_max = self.weather["main"]["temp_max"]
            self.temp_min = self.weather["main"]["temp_min"]
            self.visibility = self.weather["visibility"]
            self.sunset = datetime.fromtimestamp(self.weather["sys"]["sunset"])
            self.sunrise = datetime.fromtimestamp(self.weather["sys"]["sunrise"])
            self.description = self.weather["weather"][0]["description"]
            self.icon = self.weather["weather"][0]["icon"]
            self.main = self.weather["weather"][0]["main"]
            self.wind_degrees = self.weather["wind"]["deg"]
            self.wind_speed = self.weather["wind"]["speed"]
            self.url = self.icon_url()
        except KeyError as e:
            print(e)
        except ValueError as e:
            print(e)


class WeatherForecast(Weather):
    def __init__(self, owm_obj=None):
        super(WeatherForecast, self).__init__(owm_obj)
        pprint(self.weather)
        try:
            self.date = datetime.fromtimestamp(self.weather["dt"])
            self.rain = self.weather["rain"]
            self.snow = self.weather["snow"]
            self.clouds = self.weather["clouds"]
            self.humidity = self.weather["humidity"]
            self.pressure = self.weather["pressure"]
            self.wind_degrees = self.weather["deg"]
            self.wind_speed = self.weather["speed"]
            self.temp_day = self.weather["temp"]["day"]
            self.temp_evening = self.weather["temp"]["eve"]
            self.temp_morning = self.weather["temp"]["morn"]
            self.temp_night = self.weather["temp"]["night"]
            self.temp_min = self.weather["temp"]["min"]
            self.temp_max = self.weather["temp"]["max"]
            self.description = self.weather["weather"][0]["description"]
            self.main = self.weather["weather"][0]["main"]
            self.icon = self.weather["weather"][0]["icon"]
            self.url = self.icon_url()
        except KeyError as e:
            print(e)
        except ValueError as e:
            print(e)


class OpenWeatherMapCore:
    api_key = None

    def __init__(self, api_key, units):
        self.api_key = api_key
        self.units = units
        self.base_url = "api.openweathermap.org/data/2.5/"

    def _req(self, url, params):
        response = None
        try:
            http = urllib3.PoolManager()
            params["APPID"] = self.api_key
            if self.units:
                params["units"] = self.units
            response = http.request("GET", url, fields=params)
        except urllib3.exceptions.HTTPError as e:
            print(e)
        if response and response.data:
            return json.loads(response.data.decode("utf-8"))

    def current(self, city_id):
        return self._req(self.base_url + "weather",
                         {"id": city_id})

    def forecast(self, city_id):
        return self._req(self.base_url + "forecast",
                         {"id": city_id})

    def forecast_daily(self, city_id, days=1):
        return self._req(self.base_url + "forecast/daily",
                         {"id": city_id, "cnt": days})


class OpenWeatherMap(OpenWeatherMapCore):

    def __init__(self, api_key, units="metric"):
        super(OpenWeatherMap, self).__init__(api_key, units)


BURGDORF_DE = 2941405
HANNOVER_DE = 2910831


def main(api_key):
    owm = OpenWeatherMap(api_key)
    for forecast in owm.forecast_daily(BURGDORF_DE, 10)["list"]:
        w = WeatherForecast(forecast)
        print("{} {:s}, lo {:.0f} °C, hi {:.0f} °C, wind {:.0f} km/h from {:s}"
              .format(w.date.strftime("%a %d.%m."),
                      w.description,
                      w.temp_min, w.temp_max,
                      3.6 * w.wind_speed,
                      degree_to_meteo(w.wind_degrees)))

    cities = CityList()
    for p in cities.read("city.list.json"):
        print("\rLoading city list ... {:d}%".format(p), end="", flush=True)

    pprint(list(cities.find("Hamburg")))


if __name__ == "__main__":
    main(sys.argv[1])
