from asset_project import ProjectAsset
from pathlib import Path
import csv

def convert_csv_to_area(in_path:Path, asset:ProjectAsset=None) -> Path:
    if in_path.exists() is False and in_path.is_file() is False:
        raise Exception("Error from trying to retrieve file at: {}".format(str(in_path)))

    with in_path.open() as in_file:
        data = list(csv.reader(in_file, delimiter=","))
        headers = data.pop(0)

    out_path = Path(in_path.name.replace(in_path.suffix, "_path" + in_path.suffix))
    if asset is not None:
        out_path = asset.basePath.joinpath(out_path)

    # Rewrite later to allow variations via GUI
    needed_headers = [
        "Latitude",
        "Longitude",
        "Altitude(m)"
    ]
    
    needed_header_ids = []
    for needed in needed_headers:
        for id in range(len(headers)):
            if headers[id] == needed:
                needed_header_ids.append(id)

    with out_path.open("w") as file:
        output = ""
        for header in needed_headers:
            output += header + ','
        output = output[:-1]
        file.write(output + '\n')

        for line in data:
            output = ""
            for id in needed_header_ids:
                output += line[id] + ','
            output = output[:-1]
            file.write(output + '\n')
    
    return out_path

def calculate_bounds_from_csv(path:Path):
    # [(NW), (SE)] <=> [(maxY,minX), (minY,maxX)]
    N = float("-inf")
    W = float("inf")
    S = float("inf")
    E = float("-inf")

    with path.open() as in_file:
        data = list(csv.reader(in_file, delimiter=","))
        data.pop(0)

    lat_id = 0
    long_id = 1
    for item in data:
        N = max(N, float(item[lat_id]))
        W = min(W, float(item[long_id]))
        S = min(S, float(item[lat_id]))
        E = max(E, float(item[long_id]))

    return (N,W,S,E)

test_file = Path("ExternalData\CountryClubAsheville-WalkingData.csv")
outpath = convert_csv_to_area(test_file)
bounds = calculate_bounds_from_csv(outpath)
print("\n{},{}\n{},{}".format(*bounds))