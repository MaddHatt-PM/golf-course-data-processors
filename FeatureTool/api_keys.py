from pathlib import Path

GOOGLE_MAPS_KEY = 'google_maps'

def read_env() -> dict:
    env = Path('.env')
    output = {}
    if env.exists():
        with env.open('r') as file:
            for line in file.read().splitlines():
                split = line.split('=')
                output[split[0]] = split[1]

    return output

def google_maps() -> str:
    apis = read_env()
    return apis.get(GOOGLE_MAPS_KEY, 'NO KEY')