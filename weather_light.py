#!/usr/bin/env python3

import json
import nanoleaf
import os
import requests

from typing import Tuple

YAHOO_WEATHER_FORECAST_URL = "https://query.yahooapis.com/v1/public/yql?"\
                             "q=select+item+from+weather.forecast+where+woeid"\
                             "={woeid}&format=json"
YAHOO_WEATHER_CITY_ID_SF = 2487956

AURORA = None  # Lazily-loaded Singleton
# TODO: Implement discovery.
AURORA_IP = os.environ["AURORA_IP"]
AURORA_AUTH_TOKEN = os.environ["AURORA_AUTH_TOKEN"]

TEMP_MIN_F = 50
TEMP_MAX_F = 80

# TODO: This is a pretty rough first-cut, play around with the color scaling
# more.
TEMP_MIN_RGB = (0, 0, 200)  # Blue
TEMP_MAX_RGB = (255, 120, 0) # Orange

def get_today_low_high_fahrenheit(yahoo_city_woeid: int) -> Tuple[int, int]:
    resp = requests.get(
            YAHOO_WEATHER_FORECAST_URL.format(woeid=yahoo_city_woeid))
    content_str = resp.content.decode()
    if resp.status_code != 200:
        raise Exception("Openweather API returned status code {} with response "
        "content: {}".format(resp.status_code, content_str))
    forecast_dct = \
            json.loads(content_str)["query"]["results"]["channel"]["item"]["forecast"][0]
    return int(forecast_dct["low"]), int(forecast_dct["high"])

def set_temp_color(pct: int):
    """ Using min and max color RGB tuples as the bound, set the color to
    reflect the passed-in percentage. """
    global AURORA
    AURORA = AURORA or nanoleaf.Aurora(AURORA_IP, os.environ["AURORA_AUTH_TOKEN"])
    
    frac = pct/100
    # Scales between MIN_RGB and MAX_RGB based on the provided percentage.
    AURORA.rgb = tuple(frac*max_rgb + (1-frac)*min_rgb \
            for min_rgb, max_rgb in zip(TEMP_MIN_RGB, TEMP_MAX_RGB)
    )

def main():
    # TODO: Once I write the ability to set the panels 50/50, set low and high
    # independently instead of using the avg.
    avg_temp = sum(get_today_low_high_fahrenheit(YAHOO_WEATHER_CITY_ID_SF))/2
    scaled_avg_temp = (avg_temp - TEMP_MIN_F)/(TEMP_MAX_F - TEMP_MIN_F)
    set_temp_color(scaled_avg_temp*100)

if __name__ == "__main__":
    main()
