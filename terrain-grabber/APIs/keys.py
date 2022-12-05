"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from pathlib import Path

GOOGLE_MAPS_KEY = 'google_maps'

def read_env() -> dict:
    """
    Retrieve and return all contents from .env file
    """
    env = Path('.env')
    output = {}
    if env.exists():
        with env.open('r', encoding='utf8') as file:
            for line in file.read().splitlines():
                split = line.split('=')
                output[split[0]] = split[1]

    return output

def google_maps() -> str:
    """
    Access the .env file and retrieve the google maps API
    """
    apis = read_env()
    return apis.get(GOOGLE_MAPS_KEY, 'NO KEY')
