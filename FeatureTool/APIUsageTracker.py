

import json
from pathlib import Path

# ------------------------------------------------------------ #
# --- File IO ------------------------------------------------ #
storage_path = Path("AppAssets/api_tracker.json")

def __load_storage(path=None) -> dict[str, int]:
    if path is None:
        path = storage_path

    storage_raw = {}

    if path.is_file():
        with path.open(mode='r') as file:
            storage_raw = json.loads(file.read())
        return dict([a, int(x)] for a,x in storage_raw.items())

    else:
        empty_dict = {}
        return empty_dict

def __save_storage(storage:dict[str, int], path=None):
    if path is None:
        path = storage_path

    json_str = json.dumps(storage, indent=4)

    with path.open(mode='w') as outfile:
        outfile.write(json_str)

# ------------------------------------------------------------ #
# --- Usage Tracking ----------------------------------------- #
def get_api_count(name:str, path=None):
    storage = __load_storage(path)
    return storage.get(name, '0')

def add_api_count(name:str, add:int, path=None) -> int:
    storage = __load_storage(path)
    storage[name] = storage.get(name, 0) + add
    __save_storage(storage, path)

    return storage[name]

# ------------------------------------------------------------ #
# --- Testing ------------------------------------------------ #
if __name__ == "__main__":
    print("--- APIUsageTracker tester ---")
    print("[0] Creating and saving fake data...")
    storage_raw = {}
    storage_raw["fake_serv_0"] = "100"
    storage_raw["fake_serv_1"] = "25"

    storage:dict[str, int] = dict([a, int(x)] for a,x in storage_raw.items())

    test_path = Path("AppAssets/api_tracker_test.json")
    __save_storage(storage, path=test_path)

    print("[1] Fake_serv_0: {}".format(get_api_count("fake_serv_0", test_path)))
    print("[2] Adding 100 api requests...")

    add_api_count("fake_serv_0", 100, test_path)

    if (get_api_count("fake_serv_0", test_path) == 200):
        print("[3] Fake_serv_0: {}".format(get_api_count("fake_serv_0", test_path)))
        print("[4] Success, deleting test file")
        test_path.unlink()

    else:
        print("[x] Something has gone wrong")