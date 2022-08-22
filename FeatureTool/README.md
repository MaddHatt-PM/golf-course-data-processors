v2.0 Notes
To run:
python3 run.py <optional-saved-area-name>

Progress Report 01 Changelist:
    June 2nd
    [x] UI framework change: cv/pyautogui -> tkinter
    [x] Prompt for downloading new areas
    [x] Hard coded corner values no longer needed, API keys is still hardcoded
    [x] Added install_required.py to grab missing dependencies
    [x] Files are now saved to their own directories to avoid overwrites

Ideas:
    [ ] Get rid of the API file and change it to dot file information and the service class inside of AreaAsset
    [ ] Display areas in the inspector via a drop down window
    [x] Implement api request tracking
    [x] Archive
    [x] Write area settings to json file
    [x] Keep a single preview line and only keep 

---------------------------------------------------------------------
v1.0 Notes
Warning: tool overwrites existing output files
(Hole_features.xlsx,holeImg.tif,Features.png,Img_data.txt,polygonMain.png)

Prerequisites:
-need to hard-code the google maps api key
-hard code the corners of the satellite image (first will be top-left but it doesn't have
to be northwest--it will be rotated)

To run:
python3 Driver.py

that will bring up a preview image
hit Escape key, will prompt to enter a Feature Type (e.g. 'f' for fairway)
after entering feature type, will open a new window,
click along the outline of the feature (last point will be connected to the
first point when finished), hit Escape key when done
hit Escape again to bring back up menu of feature types (or 'd' for done)

primary output is Hole_features.xlsx, which is one column per feature type
note there are tuples for (x,y,z) in coordinate space but z values are all 0.

Img_data.txt has the lat-lon coordinates of the image and the dimensions, which
you can use to translate x,y coords to lat-lon