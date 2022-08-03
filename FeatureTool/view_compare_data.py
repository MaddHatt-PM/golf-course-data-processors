from pathlib import Path
import numpy as np
from numpy import genfromtxt
import matplotlib.pyplot as plt
from data_downloader import download_elevation, services

from utilities import meter_to_feet

def __generate_plot(datasets:list[list], labels:list[str]):
    plt.subplot(2,1,1)
    for index, ds in enumerate(datasets):
        plt.plot([*range(len(ds))], ds, label=labels[index])

    plt.fill_between([*range(len(ds))], *datasets, color='grey', alpha=0.15)
    plt.title('asdf')
    plt.xlabel('Sample Point Index')
    plt.ylabel('Elevation(m) from sealevel')
    plt.legend(loc='upper right')
    plt.grid()

    
    plt.subplot(2,1,2)
    diff = []
    for index in range(len(datasets[0])):
        diff.append(datasets[0][index] - datasets[1][index])
    
    plt.plot([*range(len(diff))], diff)
    plt.xlabel('Sample Point Index')
    plt.ylabel('Difference Elevation(m)')
    plt.grid()

    plt.show()

if __name__ == '__main__':
    datapath = Path('ExternalData\CountryClubAsheville-WalkingData.csv')
    with datapath.open('r') as file:
        lines = file.readlines()
    
    legend_labels = []

    '''GPS DATA'''
    legend_labels.append('GPS Data')
    header = lines.pop(0).split(',')
    latitude_id = header.index('Latitude')
    longitude_id = header.index('Longitude')
    altitude_id = header.index('Altitude(m)')
    walking_altitude_pts = []
    latlong_pts = []

    for ln in lines:
        ln = ln.split(',')
        pt = eval(ln[latitude_id]), eval(ln[longitude_id])
        latlong_pts.append(pt)
        walking_altitude_pts.append(eval(ln[altitude_id]))

    '''Google Elevation (API Request Per Point)'''
    legend_labels.append('Google Elevation (API Request Per Point')
    output_path = Path('temp.csv')
    if output_path.exists() is False:
        output_path = download_elevation(target=None, points=latlong_pts, service=services.google_elevation , output_path=output_path, sample_inside_polygon=False)

    with output_path.open() as file:
        lines = file.readlines()

    header = lines.pop(0).split(',')
    altitude_id = header.index('elevation')
    google_altitude_pts = []

    for ln in lines:
        ln = ln.split(',')
        google_altitude_pts.append(eval(ln[altitude_id]))

    __generate_plot(
        datasets= [walking_altitude_pts, google_altitude_pts],
        labels=legend_labels
        )
