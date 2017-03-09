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
from datetime import datetime
from pyowm.city import CityList


def degree_to_meteo(deg):
    return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][int((deg - 22.5) % 360) // 45]


class Weather:
    def __init__(self, owm_obj=None):
        self._weather = owm_obj
        self.icon = None

    def icon_url(self):
        return 'http://openweathermap.org/img/w/{}.png'.format(self.icon) if self.icon else ''


class CurrentWeather(Weather):
    def __init__(self, owm_obj=None):
        super(CurrentWeather, self).__init__(owm_obj)
        self.date = datetime.fromtimestamp(self._weather.get('dt', datetime.now().timestamp()))
        self.humidity = self._weather.get('main', {}).get('humidity')  # %
        self.pressure = self._weather.get('main', {}).get('pressure')  # hPa
        self.temp = self._weather.get('main', {}).get('temp')
        self.temp_max = self._weather.get('main', {}).get('temp_max')
        self.temp_min = self._weather.get('main', {}).get('temp_min')
        self.visibility = self._weather.get('visibility')
        self.sunset = datetime.fromtimestamp(self._weather.get('sys', {}).get('sunset'))
        self.sunrise = datetime.fromtimestamp(self._weather.get('sys', {}).get('sunrise'))
        self.description = self._weather.get('weather', [{}])[0].get('description')
        self.icon = self._weather.get('weather', [{}])[0]['icon']
        self.main = self._weather.get('weather', [{}])[0]['main']
        self.wind_degrees = self._weather.get('wind', {}).get('deg')
        self.wind_speed = 3.6 * self._weather.get('wind', {}).get('speed')  # m/s
        self.url = self.icon_url()


class WeatherForecast(Weather):
    def __init__(self, owm_obj=None):
        super(WeatherForecast, self).__init__(owm_obj)
        self.date = datetime.fromtimestamp(self._weather.get('dt', datetime.now().timestamp()))
        self.rain = self._weather.get('rain')  # mm
        self.snow = self._weather.get('snow')  # mm
        self.clouds = self._weather.get('clouds')  # %
        self.humidity = self._weather.get('humidity')  # %
        self.pressure = self._weather.get('pressure')  # hPa
        self.wind_degrees = self._weather.get('deg')
        self.wind_speed = 3.6 * self._weather.get('speed')  # m/s
        self.temp_day = self._weather.get('temp', {}).get('day')
        self.temp_evening = self._weather.get('temp', {}).get('eve')
        self.temp_morning = self._weather.get('temp', {}).get('morn')
        self.temp_night = self._weather.get('temp', {}).get('night')
        self.temp_min = self._weather.get('temp', {}).get('min')
        self.temp_max = self._weather.get('temp', {}).get('max')
        self.description = self._weather.get('weather', [{}])[0].get('description')
        self.main = self._weather.get('weather', [{}])[0].get('main')
        self.icon = self._weather.get('weather', [{}])[0].get('icon')
        self.url = self.icon_url()


class WeatherForecast3(Weather):
    def __init__(self, owm_obj=None):
        super(WeatherForecast3, self).__init__(owm_obj)
        self.date = datetime.fromtimestamp(self._weather.get('dt', datetime.now().timestamp()))
        self.rain = self._weather.get('rain', {}).get('3h')  # mm
        self.snow = self._weather.get('snow', {}).get('3h')  # mm
        self.clouds = self._weather.get('clouds', {}).get('all')  # %
        self.humidity = self._weather.get('main', {}).get('humidity')  # %
        self.pressure = self._weather.get('main', {}).get('pressure')  # hPa
        self.pressure_sea_level = self._weather.get('main', {}).get('sea_level')  # hPa
        self.pressure_ground_level = self._weather.get('main', {}).get('grnd_level')  # hPa
        self.temp = self._weather.get('main', {}).get('temp')
        self.temp_max = self._weather.get('main', {}).get('temp_max')
        self.temp_min = self._weather.get('main', {}).get('temp_min')
        self.wind_degrees = self._weather.get('wind', {}).get('deg')  # degrees
        self.wind_speed = 3.6 * self._weather.get('wind', {}).get('speed')  # m/s
        self.description = self._weather.get('weather', [{}])[0].get('description')
        self.main = self._weather.get('weather', [{}])[0].get('main')
        self.icon = self._weather.get('weather', [{}])[0].get('icon')
        self.url = self.icon_url()


class OpenWeatherMapCore:
    def __init__(self, api_key, units='metric'):
        self._api_key = api_key
        self._units = units
        self._base_url = 'api.openweathermap.org/data/2.5/'

    def _req(self, url, params):
        response = None
        try:
            http = urllib3.PoolManager()
            params['APPID'] = self._api_key
            if self._units:
                params['units'] = self._units
            response = http.request('GET', url, fields=params)
        except urllib3.exceptions.HTTPError as e:
            print(e)
        return json.loads(response.data.decode('utf-8')) if response and response.data else {}

    def current(self, city_id):
        return self._req(self._base_url + 'weather',
                         {'id': city_id})

    def forecast(self, city_id, n=None):
        return self._req(self._base_url + 'forecast',
                         {'id': city_id, 'cnt': n})

    def forecast_daily(self, city_id, days=1):
        return self._req(self._base_url + 'forecast/daily',
                         {'id': city_id, 'cnt': days})


class OpenWeatherMap(OpenWeatherMapCore):
    def __init__(self, api_key, units='metric'):
        super(OpenWeatherMap, self).__init__(api_key, units)

    def current(self, city_id):
        return CurrentWeather(super(OpenWeatherMap, self).current(city_id))

    def forecast(self, city_id, n=None):
        forecasts = super(OpenWeatherMap, self).forecast(city_id, n).get('list')
        return [WeatherForecast3(f) for f in forecasts] if type(forecasts) is list else []

    def forecast_daily(self, city_id, days=1):
        forecasts = super(OpenWeatherMap, self).forecast_daily(city_id, days).get('list')
        return [WeatherForecast(f) for f in forecasts] if type(forecasts) is list else []


if __name__ == '__main__':
    _api_key = sys.argv[1]
    _owm = OpenWeatherMap(_api_key)
    for forecast in _owm.forecast(2941405, 16):
        print('{} {:s}, lo {:.0f} °C, hi {:.0f} °C, wind {:.0f} km/h from {:s}'
              .format(forecast.date.strftime('%a %d.%m. %H:%M'),
                      forecast.description,
                      forecast.temp_min, forecast.temp_max,
                      forecast.wind_speed,
                      degree_to_meteo(forecast.wind_degrees)))
