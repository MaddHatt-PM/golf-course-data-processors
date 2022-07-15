from datetime import datetime
import json
from pathlib import Path

# ------------------------------------------------------------ #
# --- File IO ------------------------------------------------ #
storage_str = "AppAssets/api_tracker.json"
storage_path = Path(storage_str)

def __load_storage(path=None) -> dict[str, int]:
    if path is None:
        path = storage_path

    storage_raw = {}

    # Check that the file exists and if its creation date matches this month
    if path.is_file():
        creation_timestamp = path.stat().st_ctime
        creation_date = datetime.fromtimestamp(creation_timestamp)
        
        if creation_date.month == datetime.now().month:
            with path.open(mode='r') as file:
                storage_raw = json.loads(file.read())
            return dict([a, int(x)] for a,x in storage_raw.items())

        # File is old and should be archived
        else:
            creation_timestamp = storage_path.stat().st_ctime
            creation_date = datetime.fromtimestamp(creation_timestamp)
            archive_str = storage_str
            archive_str = archive_str.replace("AppAssets", "AppAssets/Archives")

            month = str(creation_date.month).zfill(2)
            year = str(creation_date.year)
            year = year[len(year)-2:]
            archive_str = archive_str.replace(".json", "_{}_{}.json".format(month, year))

            archive_path = Path(archive_str)
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            if archive_path.is_file():
                archive_path.unlink()

            storage_path.rename(archive_path)
            

    # No file exists
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