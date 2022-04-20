#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import urllib
import urllib.request
import json

# Uses geogrpahicLib to easily calculate distance between
from geographiclib.geodesic import Geodesic

APIKEY = "&key=AIzaSyAi63zbrCv-tiXms4o6lnhY1c1W1MpzWZ0" # MaddHatt.pm@gmail.com

# This program takes as input: 4 points of (lat,long)
# And outputs avg slope of elevation, as well as if Uphill, or Downhill
# Relies HEAVILY on formulas outlined in
# http://www.movable-type.co.uk/scripts/latlong.html


def makeDivisByFive(dist):
    if dist % 10 != 0:
        if dist % 10 < 5:
            dist += 5 - dist % 10
        else:
            dist += 10 - dist % 10
    return dist


def toCSV(coordList):

    with open("./sawgrass18.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["latitude", "longitude", "elevation"])
        writer.writerows(coordList)


def apiRequest(coord):
    global APIKEY
    url = "https://maps.googleapis.com/maps/api/elevation/json?locations="
    currLat = coord[0]
    currLong = coord[1]
    # Get data requested from google
    data = json.load(
        urllib.request.urlopen((url + str(currLat) + "," + str(currLong) + APIKEY))
    )
    # return data['results'][0]['elevation']
    return [
        data["results"][0]["location"]["lat"],
        data["results"][0]["location"]["lng"],
        data["results"][0]["elevation"],
    ]


def createRectangle(p1, p2, p3, p4):
    elevations = []
    elevations.append(apiRequest(p1))

    ###
    # Inbetween lines 46,49 we  utilize geographiclib to calculate
    # The azimuth between our "top 2" points on the rectangle.
    # We calculate an azimuth, so that we may find, given a point(p1), and a distance
    # (0,length between p1,p2), lat/long pairs at intervals of 5 meters

    # Define ellipsoid
    # Reference: https://confluence.qps.nl/qinsy/9.1/en/world-geodetic-system-1984-wgs84-182618391.html
    geo = Geodesic.WGS84

    # Gets distance, and bearing, for top left & top right point, for use
    # in inner "for loop"
    info1 = geo.Inverse(p1[0], p1[1], p2[0], p2[1])
    dist1 = info1["s12"]
    azimuth1 = info1["azi1"]

    # Gets distance, and bearing, for top left & bottom left point, for use in
    # outer "for loop"
    info2 = geo.Inverse(p1[0], p1[1], p3[0], p3[1])
    dist2 = info2["s12"]
    azimuth2 = info2["azi1"]

    # To get next point "distance" meters away, use the form:
    # geo.Direct(lat,long,bearing,distance)
    # to access the coord pair, assign above statement to variable, and index
    # ['lat2'] & ['lon2']
    # Ex:
    # dir = geo.Direct(p1[0],p1[1],azimuth1,5)
    # C = (dir['lat2'],dir['lon2'])
    # print(C)
    info3 = geo.Inverse(p2[0], p2[1], p4[0], p4[1])
    azimuth3 = info3["azi1"]
    ######
    #   p1 dist1 p2
    #   +--------+
    # d -        -
    # 2 -        -
    #   -        -
    # p3 +--------x

    # Step is every 5m, between dist1 and dist2 (d2 in diagram above)
    step = 5
    debugCoordPairs = []
    currCoord = [p1[0], p1[1]]
    compareCoord = [p2[0], p2[1]]

    # Make dist1 & dist2 iterable by a step of 5,
    # Ex = dist1 = 23 meters, make it 25. Dist1 = 21 Meters, make it 25
    dist1 = makeDivisByFive(dist1)
    dist2 = makeDivisByFive(dist2)
    currInfo = geo.Inverse(currCoord[0], currCoord[1], compareCoord[0], compareCoord[1])
    currAzimuth = currInfo["azi1"]

    total = int(dist2) / step * int(dist1) / step
    count = 0

    for i in range(0, int(dist2), step):
        if i != 0:

            # Get new starting coord, 5m closer to p3
            tempDirP1P2 = geo.Direct(p1[0], p1[1], azimuth2, i)
            currCoord[0] = tempDirP1P2["lat2"]
            currCoord[1] = tempDirP1P2["lon2"]

            tempDirP2P4 = geo.Direct(p2[0], p2[1], azimuth3, i)
            compareCoord[0] = tempDirP2P4["lat2"]
            compareCoord[1] = tempDirP2P4["lon2"]

            currInfo = geo.Inverse(
                currCoord[0], currCoord[1], compareCoord[0], compareCoord[1]
            )
            currAzimuth = currInfo["azi1"]

            dist1 = currInfo["s12"]
            dist1 = makeDivisByFive(dist1)
            # debugCoordPairs.append(apiRequest(currCoord))
        for j in range(0, int(dist1), step):

            newDirect = geo.Direct(currCoord[0], currCoord[1], currAzimuth, j)
            debugCoordPairs.append(apiRequest([newDirect["lat2"], newDirect["lon2"]]))
            count += 1
            print(str(count) + "/" + str(total))

    toCSV(debugCoordPairs)
    print("Calculation completed! Check specified")


# INSERT YOUR COORDINATES BELOW
point1 = [30.197854, -81.394593]
point2 = [30.197901, -81.392501]
point3 = [30.194349, -81.391943]
point4 = [30.194498, -81.391257]


createRectangle(point1, point2, point3, point4)
