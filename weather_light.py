#!/usr/bin/env python3

import json
import nanoleaf
import os
import requests

from typing import Tuple

OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]
OPENWEATHER_CITY_ID = 5391959
OPENWEATHER_API_URL = "http://api.openweathermap.org"\
                      "/data/2.5/weather?id={city_id}&appid={api_key}"

AURORA = None # Singleton
# TODO: Implement discovery.
AURORA_IP = os.environ["AURORA_IP"]
AURORA_AUTH_TOKEN = os.environ["AURORA_AUTH_TOKEN"]

TEMP_MIN_F = 50
TEMP_MAX_F = 80

# TODO: This is a pretty rough first-cut, play around with the color scaling
# more.
TEMP_MIN_RGB = (0, 0, 200)  # Blue
TEMP_MAX_RGB = (255, 120, 0) # Orange

def _kelv_to_fahr(deg_k: int) -> int:
    return 9/5*(deg_k - 273) + 32

def get_today_low_high_fahrenheit(city_id: int) -> Tuple[int, int]:
    url = OPENWEATHER_API_URL.format(
            city_id=str(city_id), api_key=OPENWEATHER_API_KEY)
    resp = requests.get(url)
    content_str = resp.content.decode()
    if resp.status_code != 200:
        raise Exception("Openweather API returned status code {} with response "
        "content: {}".format(resp.status_code, content_str))

    return tuple(map(_kelv_to_fahr,
                     (json.loads(content_str)["main"][k] for k in ("temp_min",
                                                                   "temp_max"))
                )
            )

def set_temp_color(pct: int):
    """ Using min and max color RGB tuples as the bound, set the color to
    reflect the passed-in percentage. """
    global AURORA
    AURORA = AURORA or nanoleaf.Aurora(AURORA_IP, os.environ["AURORA_AUTH_TOKEN"])
    
    frac = pct/100
    # Linearly transforms MIN_RGB to MAX_RGB depending on the percentage.
    AURORA.rgb = tuple(frac*max_rgb + (1-frac)*min_rgb \
            for min_rgb, max_rgb in zip(TEMP_MIN_RGB, TEMP_MAX_RGB)
    )

def main():
    # TODO: Once I write the ability to set the panels 50/50, set low and high
    # independently instead of using the avg.
    avg_temp = sum(get_today_low_high_fahrenheit(OPENWEATHER_CITY_ID))/2
    scaled_avg_temp = (avg_temp - TEMP_MIN_F)/(TEMP_MAX_F - TEMP_MIN_F)
    set_temp_color(scaled_avg_temp*100)

if __name__ == "__main__":
    main()
