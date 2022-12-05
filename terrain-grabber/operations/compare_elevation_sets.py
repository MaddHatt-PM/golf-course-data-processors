"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from pathlib import Path
import matplotlib.pyplot as plt
from download_data import download_elevation, services

from utilities.math import meter_to_feet

def generate_comparison_plot(datasets:list[list], labels:list[str]):
    """
    Generate a line graph that compares the elevation data from the provided datasets.
    """
    title = 'Elevation Comparison between GPS App and Google Maps'
    plt.figure(title)

    plt.subplot(2,1,1)
    for index, ds in enumerate(datasets):
        plt.plot([*range(len(ds))], ds, label=labels[index])

    plt.fill_between([*range(len(ds))], *datasets, color='grey', alpha=0.2)
    plt.title(title)
    plt.xlabel('Sample Point Index')
    plt.ylabel('Elevation(ft) from sealevel')
    plt.legend(loc='upper right')
    plt.margins(x=0)
    plt.grid()

    ax = plt.subplot(2,1,2)
    diff = []
    for index in range(len(datasets[0])):
        diff.append(datasets[0][index] - datasets[1][index])

    x0, y0 = [0, len(datasets[0])], [0, 0]
    plt.plot(x0, y0, color='k')

    plt.plot([*range(len(diff))], diff, label='GPS Elev. minus Google Elev.', color='tab:purple')
    plt.fill_between([*range(len(diff))], diff, color='grey', alpha=0.2)
    plt.title('Difference of Elevation')
    plt.xlabel('Sample Point Index')
    plt.ylabel('Difference Elevation(ft)')
    plt.legend(loc='upper right')
    plt.margins(x=0)
    plt.grid()

    plt.subplots_adjust(left=0.1,
                    bottom=0.1, 
                    right=0.9, 
                    top=0.9, 
                    wspace=0.4, 
                    hspace=0.3)

    plt.show()

def process_topographic_data(csv_path:str):
    """
    Read out the csv_path (assuming it's perfect). The number of sample points is reliant on the provided source.
    Location data from the provided source is used to sample directly from Google Maps via API.
    """
    with csv_path.open('r') as file:
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
    legend_labels.append('Google Elevation (API Request Per Point)')
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

    walking_altitude_pts = [meter_to_feet(pt) for pt in walking_altitude_pts]
    google_altitude_pts = [meter_to_feet(pt) for pt in google_altitude_pts]

    generate_comparison_plot(
        datasets= [walking_altitude_pts, google_altitude_pts],
        labels=legend_labels
        )

if __name__ == '__main__':
    datapath = Path('ExternalData\CountryClubAsheville-WalkingData.csv')
    process_topographic_data(datapath)
